import base64
from googleapiclient.discovery import build
from tqdm import tqdm
from langchain.schema import Document
from RAG import RAG


def get_message_body(msg):
    payload = msg.get("payload", {})
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                return base64.urlsafe_b64decode(data).decode("utf-8")
    else:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8")
    return None


class Gmail:
    def __init__(self, credentials):
        try:
            self.service = build("gmail", "v1", credentials=credentials)
        except:
            self.service = None
            print("Unable to make connection with Gmail")

    def Inbox(self, results: int = 5, query: str = None):
        try:
            print("Fetching Message ID's...", end="\r")
            results = (
                self.service.users()
                .messages()
                .list(userId="me", labelIds=["INBOX"], maxResults=results)
                .execute()
            )
            messages = results.get("messages", [])

            if not messages:
                return "No messages found in inbox."
            
            print("Fetching Complete Messages...", end="\r")
            detailed_messages = []
            docs = []
            for m in tqdm(messages):
                msg_id = m["id"]
                msg_detail = self.service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                payload = msg_detail.get("payload", {})
                headers = payload.get("headers", [])
                body = get_message_body(msg_detail)

                details = {h["name"]: h["value"] for h in headers}
                msg = {
                    "id": msg_id,
                    "from": details.get("From"),
                    "subject": details.get("Subject"),
                    "date": details.get("Date"),
                    "body": body,
                }
                detailed_messages.append(msg)

                # Convert to Document for RAG
                content = f"From: {msg['from']}\nSubject: {msg['subject']}\nDate: {msg['date']}\nBody: {msg['body']}"
                docs.append(Document(page_content=content, metadata={"id": msg_id}))

            if query:  # Apply RAG if user provides a semantic query
                return RAG(docs, query)
            else:  # Otherwise return raw emails
                return detailed_messages

        except Exception as error:
            return f"Error: {error}"

    def search(self, query: str, results: int = 5, rag: bool = False):
        try:
            print("Searching for Mails", end="\r")
            results = (
                self.service.users()
                .messages()
                .list(userId="me", labelIds=["INBOX"], maxResults=results, q=query)
                .execute()
            )
            messages = results.get("messages", [])

            if not messages:
                return "No messages found."
            
            print("Fetching Complete Messages...", end="\r")
            detailed_messages = []
            docs = []
            for m in tqdm(messages):
                msg_id = m["id"]
                msg_detail = self.service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                payload = msg_detail.get("payload", {})
                headers = payload.get("headers", [])
                body = get_message_body(msg_detail)

                details = {h["name"]: h["value"] for h in headers}
                msg = {
                    "id": msg_id,
                    "from": details.get("From"),
                    "subject": details.get("Subject"),
                    "date": details.get("Date"),
                    "body": body,
                }
                detailed_messages.append(msg)

                # Convert to Document for RAG
                content = f"From: {msg['from']}\nSubject: {msg['subject']}\nDate: {msg['date']}\nBody: {msg['body']}"
                docs.append(Document(page_content=content, metadata={"id": msg_id}))

            if rag:  # If rag=True, run semantic retrieval
                return RAG(docs, query)
            else:
                return detailed_messages

        except Exception as error:
            return f"Error: {error}"