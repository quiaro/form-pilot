---
title: Form Pilot
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: docker
python_version: 3.13
app_port: 7860
app_file: app.main.py
pinned: false
short_description: Agentic app to make filling PDF forms effortless.
---

# Form Pilot

Agentic app to make filling PDF forms effortless. Upload a PDF form and let the agent do the rest. This app uses [Streamlit](https://docs.streamlit.io/) and [LangGraph](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/), plus other great packages listed in `pyproject.toml`.

## How it works

1. User uploads an empty or incomplete PDF form
2. User uploads any support documents related to the form
3. The app prefills the form with any data that exists in the support documents
4. For the fields that were not prefilled, the app will ask the user for the answers to these fields
5. When the app is done requesting information from the user, the user is prompted to download the PDF form
6. The user can download the completed PDF form
7. The app's agent chat bot guides the user through the process

## Setup and Installation

### Prerequisites

- Python 3.13+
- Node.js 22+
- npm
- Docker (optional, for containerized deployment)

#### Create a `.env` file by copying `.env.example`:

```
cp .env.example .env
```

#### Ollama

The application uses LLM models running locally using [Ollama](https://ollama.com/).
To see/change the models used, edit the `.env` file.

1. Pull models specified in `.env` file:

   ```
   ollama pull <model_name>
   ```

2. Run models before launching the app:
   ```
   ollama run <model_name>
   ```

### Run Locally

1. Install dependencies and create virtual environment with `uv`

   ```
   uv sync
   ```

2. Run the app on http://0.0.0.0:7860/
   ```
   streamlit run app/main.py
   ```

> If you wish to change any settings to the frontend of the app, edit `config.toml` in the `.streamlit` folder. Follow the [Streamlit configuration instructions](https://docs.streamlit.io/develop/api-reference/configuration).

### Run in Docker container

1. Create the docker image from the Dockerfile

   ```
   docker build -t "form_pilot:latest" .
   ```

2. Run the docker container from the docker image. The app will run `http://0.0.0.0:7860/`.
   ```
   docker run --name form_pilot -p 7860:7860 -d form_pilot:latest
   ```

## Roadmap

1. Extend the app to work with other fields types in forms besides `text` inputs
2. Integrate judge for user's answers (`/graphs/judge_answer.py`) (is the answer `valid`?)
3. Extend support for other support document types (images, pdf, xls, etc.)
4. Optimize for longer forms
5. Add ability to preview PDF form
6. Replace text interface with voice

## TODO List

1. User can ask the app to edit any field at any time
2. Manage `retries` for answering a field
3. More error handling for thrown errors
