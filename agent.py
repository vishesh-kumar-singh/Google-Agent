from OAuth import Authenticate
from services.calender import GoogleCalendar
from services.mail import Gmail
from services.drive import GoogleDrive
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document


creds = Authenticate()

mail_service = Gmail(creds)
drive_service = GoogleDrive(creds)
calendar_service = GoogleCalendar(creds)




prompt_template_main = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are J.A.R.V.I.S. from Ironman and you need to treat anyone talking to you as your master. Answer all the questions to the best of your ability, but also make sure to not give any information you are not sure about.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# prompt_template_refine = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             """You are a part of ai agent workflow. The task of the agent is to scrape necessary information from either mail, calender to answer user queries.""",
#         ),
#         MessagesPlaceholder(variable_name="messages"),
#     ]
# )



memory = MemorySaver()
model = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")
workflow1 = StateGraph(state_schema=MessagesState)
# workflow2 = StateGraph(state_schema=MessagesState)

def call_model_main(state: MessagesState):
    prompt=prompt_template_main.invoke(state)
    response = model.invoke(prompt)
    return {"messages": response}

# def call_model_refine(state: MessagesState):
#     prompt=prompt_template_refine.invoke(state)
#     response = model.invoke(prompt)
#     return {"messages": response}


workflow1.add_edge(START, "model")
workflow1.add_node("model", call_model_main)
# workflow2.add_edge(START, "model")
# workflow2.add_node("model", call_model_refine)

app1 = workflow1.compile(checkpointer=memory)
# app2 = workflow2.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "000"}}



def Answer(query):

    
    
    input_messages = [HumanMessage(content=query)]
    output = app1.invoke({"messages": input_messages}, config)
    

    return output["messages"][-1].content