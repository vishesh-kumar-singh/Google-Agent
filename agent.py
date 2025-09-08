from OAuth import Authenticate
from services.calender import GoogleCalendar
from services.mail import Gmail
from services.drive import GoogleDrive
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model
from mem0 import MemoryClient
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Dict
from langchain_core.tools import tool
from services.calender import parse_datetime_to_iso
from services.calender import parse_datetime_to_iso
from datetime import datetime, timedelta
import pytz

creds = Authenticate()

mail_service = Gmail(creds)
drive_service = GoogleDrive(creds)
calendar_service = GoogleCalendar(creds)


@tool
def gmail_send(to: str, subject: str, body: str):
    """Send an email using Gmail"""
    return mail_service.send_mail(to, subject, body)

@tool
def gmail_search(query: str, results: int = 5):
    """Search Gmail inbox and return semantically relevant emails"""
    return mail_service.search(query, results=results, rag=True)

@tool
def gmail_unread(results: int = 5):
    """Fetch unread Gmail messages"""
    return mail_service.unread(max_results=results)

@tool
def gmail_send(to: str, subject: str, body: str):
    """Send an email using Gmail"""
    return mail_service.send_mail(to, subject, body)


@tool
def drive_search(query: str, keywords: List[str], max_results: int = 5):
    """Search Google Drive for files related to list of keywords and retrieve content through RAG for a given query"""
    return drive_service.get_results(query, keywords, max_results=max_results)

@tool
def calendar_search(query: str, max_results: int = 5):
    """Search Google Calendar events for a given query"""
    return calendar_service.search_events(query, max_results=max_results)

@tool
def calendar_upcoming(max_results: int = 10):
    """Get upcoming events"""
    return calendar_service.upcoming_events(max_results=max_results)

@tool
def calendar_create(summary: str, start: str, end: str = None, timezone: str = "Asia/Kolkata"):
    """
    Create a new calendar event using natural language dates.
    
    start: natural language start time, e.g., "8th Sep 2025 at 23:30"
    end: optional natural language end time; if not provided, defaults to 1 hour after start
    timezone: e.g., "Asia/Kolkata"
    """


    # Parse start datetime to ISO
    start_iso = parse_datetime_to_iso(start, timezone)

    # Parse end datetime
    if end:
        end_iso = parse_datetime_to_iso(end, timezone)
    else:
        # Default: 1 hour after start
        tz = pytz.timezone(timezone)
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = start_dt + timedelta(hours=1)
        if end_dt.tzinfo is None:
            end_iso = tz.localize(end_dt).isoformat()
        else:
            end_iso = end_dt.isoformat()

    # Call the actual calendar service
    
    return calendar_service.create_event(summary, start_iso, end_iso, timezone)

@tool
def calendar_delete(summary: str, days_ahead: int = 30):
    """Delete an event by summary text (first match)"""
    return calendar_service.delete_event(summary, days_ahead=days_ahead)


tools = [
    gmail_send,
    gmail_search,
    gmail_unread,
    drive_search,
    calendar_search,
    calendar_upcoming,
    calendar_create,
    calendar_delete,
]




mem0 = MemoryClient()
model = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")
model_with_tools = model.bind_tools(tools)



prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are J.A.R.V.I.S. from Ironman and you need to treat anyone talking to you as your master. You have access to various tools likegmail_send,gmail_search,gmail_unread,drive_search,calendar_search,calendar_upcoming,calendar_create,calendar_delete. All of them are called according to their need and executed automatically. You are supposed to have casual conversations with the user, update them about the execution of tasks and give required results. Answer all the questions to the best of your ability, but also make sure to not give any information you are not sure about.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)



def retrieve_context(query: str, user_id: str) -> List[Dict]:

    try:
        memories = mem0.search(query, user_id=user_id, output_format='v1.1')
        memory_list = memories['results']
        
        serialized_memories = ' '.join([mem["memory"] for mem in memory_list])
        context = [
            {
                "role": "system", 
                "content": f"Relevant information: {serialized_memories}"
            },
            {
                "role": "user",
                "content": query
            }
        ]
        return context
    except Exception as e:
        print(f"Error retrieving memories: {e}")

        return [{"role": "user", "content": query}]
    



def save_interaction(user_id: str, user_input: str, assistant_response: str):

    try:
        interaction = [
            {
              "role": "user",
              "content": user_input
            },
            {
                "role": "assistant",
                "content": assistant_response
            }
        ]
        result = mem0.add(interaction, user_id=user_id, output_format='v1.1')
        print(f"Memory saved successfully: {len(result.get('results', []))} memories added")
    except Exception as e:
        print(f"Error saving interaction: {e}")


def refine_tool_output(raw_results, user_query):
    refinement_prompt = f"""
    The following are raw outputs from tools responding to the user's query:
    {raw_results}

    Please:
    1. Summarize the key points.
    2. Remove duplicates.
    3. Format it in readable paragraphs or bullet points.
    4. Keep it relevant to the user's original query: "{user_query}"

    Provide the refined and clear response.
    """
    response = model.invoke(refinement_prompt)
    return response.content


def call_model_main(state: MessagesState, config):
    user_query = state["messages"][-1].content
    user_id = config["configurable"]["thread_id"]

    memory_context = retrieve_context(user_query, user_id)
    full_prompt = prompt_template.invoke({"messages": memory_context})

    response = model_with_tools.invoke(full_prompt)

    if response.tool_calls:  
        results = []
        for tool_call in response.tool_calls:
            tool = next(t for t in tools if t.name == tool_call["name"])
            tool_result = tool.invoke(tool_call["args"])
            results.append(str(tool_result))

        raw_results = "\n".join(results)
        final_content = refine_tool_output(raw_results, user_query)  # LLM refinement
    else:
        final_content = response.content

    save_interaction(user_id, user_query, final_content)

    return {"messages": state["messages"] + [HumanMessage(content=final_content)]}






workflow1 = StateGraph(state_schema=MessagesState)
workflow1.add_node("model", call_model_main)
workflow1.add_edge(START, "model")
app1 = workflow1.compile()


config = {"configurable": {"thread_id": "000"}}



def Answer(query):
    
    input_messages = [HumanMessage(content=query)]
    output = app1.invoke({"messages": input_messages}, config)
    

    return output["messages"][-1].content