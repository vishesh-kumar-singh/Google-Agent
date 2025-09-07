from OAuth import Authenticate
from services.calender import GoogleCalendar
from services.mail import Gmail
from services.drive import GoogleDrive
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from mem0 import MemoryClient
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Dict


creds = Authenticate()

mail_service = Gmail(creds)
drive_service = GoogleDrive(creds)
calendar_service = GoogleCalendar(creds)

mem0 = MemoryClient()
model = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")



prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are J.A.R.V.I.S. from Ironman and you need to treat anyone talking to you as your master. Answer all the questions to the best of your ability, but also make sure to not give any information you are not sure about.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)



def retrieve_context(query: str, user_id: str) -> List[Dict]:
    """Retrieve relevant context from Mem0"""
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
        # Return empty context if there's an error
        return [{"role": "user", "content": query}]
    



def save_interaction(user_id: str, user_input: str, assistant_response: str):
    """Save the interaction to Mem0"""
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



def call_model_main(state: MessagesState, config):
    # Extract the latest user query
    user_query = state["messages"][-1].content
    user_id = config["configurable"]["thread_id"]

    memory_context = retrieve_context(user_query, user_id)

    full_prompt = prompt_template.invoke({"messages": memory_context})

    response = model.invoke(full_prompt)

    save_interaction(user_id, user_query, response.content)

    return {"messages": state["messages"] + [response]}





workflow1 = StateGraph(state_schema=MessagesState)
workflow1.add_node("model", call_model_main)
workflow1.add_edge(START, "model")
app1 = workflow1.compile()


config = {"configurable": {"thread_id": "000"}}



def Answer(query):
    
    input_messages = [HumanMessage(content=query)]
    output = app1.invoke({"messages": input_messages}, config)
    

    return output["messages"][-1].content