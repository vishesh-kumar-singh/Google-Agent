# Google Agent 

A conversational assistant that integrates with Gmail, Google Drive, and Google Calendar using Google APIs and Retrieval-Augmented Generation (RAG). This agent can search, send emails, manage calendar events, and retrieve documents with semantic search.

## Features

- **Gmail Integration**: Search, send, and retrieve unread emails. Semantic search via RAG.
- **Google Drive Integration**: Search files by keywords, download, and run semantic queries on documents (PDF, DOCX, TXT).
- **Google Calendar Integration**: Search, create, and delete events using natural language.
- **Conversational Interface**: Chat with J.A.R.V.I.S. in the terminal.
- **Memory**: Stores and retrieves previous interactions for context-aware responses using **mem0**

## Directory Structure

```
.env
.gitignore
agent.py
credentials.json
main.py
OAuth.py
RAG.py
README.md


services/
	 calender.py
	 drive.py
	 mail.py

Temporary/
	 downloaded_file0.pdf
	 ...
```

## Setup

1. **Clone the repository**  
	```sh
	git clone https://github.com/vishesh-kumar-singh/Google-Agent.git
	cd Google Agent
	```

2. **Install dependencies**  
	- Python 3.12+
	- Required packages:
	  ```sh
	  pip install -r requirements.txt
	  ```

3. **Google API Credentials**  
	- Place your OAuth credentials in `credentials.json`.
	- On first run, authenticate in browser; tokens are saved in `token.json`.

4. **Run the Agent**  
	```sh
	python main.py
	```

## Usage

- Start the agent and type your queries:
  ```
  Enter your query: Search for emails about any meeting
  Enter your query: Schedule a meet today at 11:30 pm for inter IIT tech meet discussion
  Enter your query: Updates on the tenure project file in my drive
  ```

- Type `exit` or `quit` to end the session.

## Modules

- `agent.py`: Main orchestration, tools, and chat logic.
- `main.py`: CLI entry point.
- `OAuth.py`: Handles Google OAuth authentication.
- `RAG.py`: Retrieval-Augmented Generation for semantic search.
- `services/mail.py`: Gmail API integration.
- `services/drive.py`: Google Drive API integration.
- `services/calender.py`: Google Calendar API integration.

## Temporary Files

Downloaded files from Drive are stored in the `Temporary` folder.

## Current Status

The application is still under development and things are being added. For running the files only the registered gmail ids can be used to login because the app is still in testing phase as per google.
