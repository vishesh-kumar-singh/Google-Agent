from googleapiclient.discovery import build
import datetime
from RAG import RAG





class GoogleCalendar:
    def __init__(self, credentials):
        try:
            self.service = build("calendar", "v3", credentials=credentials)
            
        except:
            self.service= None
            print("Unable to make connection with gmail")

    def upcoming_events(self, max_results=10):
        now = datetime.datetime.now(datetime.UTC).isoformat()
        results = self.service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = results.get("items", [])

        formatted = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            formatted.append({
                "start": start,
                "summary": event.get("summary", "(No Title)"),
                "id": event.get("id"),
                "location": event.get("location"),
                "description": event.get("description"),
            })
        return formatted
    
    def search_events(self, query, max_results=10, days_ahead=30):
        now = datetime.datetime.now(datetime.UTC).isoformat()
        future = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=days_ahead)).isoformat()

        results = self.service.events().list(
            calendarId="primary",
            q=query,
            timeMin=now,
            timeMax=future,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = results.get("items", [])
        return [
            {
                "id": e["id"],
                "start": e["start"].get("dateTime", e["start"].get("date")),
                "summary": e.get("summary", "(No Title)"),
                "location": e.get("location"),
            }
            for e in events
        ]
    
    
    # Can do if got time
    def create_event(self, summary, start_time, end_time, timezone="UTC"):
        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
        }
        return self.service.events().insert(calendarId="primary", body=event).execute()