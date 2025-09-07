import dotenv
dotenv.load_dotenv()

from agent import Answer

print("J.A.R.V.I.S. is at your service sir! Type 'exit' or 'quit' to end the session.")
while True:
    input_query= input("Enter your query: ")
    if input_query.lower() in ['exit', 'quit']:
        break
    response = Answer(input_query)
    print("\n")
    print("Response: ", response)
    print("\n\n")