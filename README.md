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

Agentic app to make filling PDF forms effortless. Upload a PDF form and let the agent do the rest. This app uses [Streamlit](https://docs.streamlit.io/) in the frontend and [LangGraph](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/) in the backend, plus other great packages listed in `pyproject.toml`.

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
   streamlit run app/app.py
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

## Test Strings

A test server can be run to test specific aspects of the backend code:

```
python -m app.main
```

- Test parsing of the PDF form

```
curl -X POST "http://localhost:7861/api/parse_pdf_form" -H "Content-Type: application/json" -d '{"pdf_file": "app/docs/forms/form-example.pdf"}'
```

- Test the loading of supporting documents into memory (to test this, create a Word document with information related to the fields in the form)

```
curl -X POST http://localhost:7861/api/load_context  -H "Content-Type: application/json"   -d '{"document_filepaths": ["app/docs/context/info.docx"]}'
```

- Test pre-filling of a form using supporting documents

```
curl -X POST http://localhost:7861/api/pre_fill_form  -H "Content-Type: application/json"   -d '{"form_data": {"formFileName":"app/docs/forms/form-example.pdf","lastSaved":"","fields":[{"label":"Given Name Text Box","description":"First name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Family Name Text Box","description":"Last name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 1 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"House nr Text Box","description":"House and floor","type":"text","docId":null,"value":"ewresd fdsf wr","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 2 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Postcode Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"City Text Box","description":"","type":"text","docId":null,"value":"erewrs erter tertret ert ertertd fsdf ","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Country Combo Box","description":"Use selection or write country name","type":"dropdown","docId":null,"value":"ert t ert","options":["Austria","Belgium","Britain","Bulgaria","Croatia","Cyprus","Czech-Republic","Denmark","Estonia","Finland","France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands","Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden"],"lastProcessed":"","lastSurveyed":""},{"label":"Gender List Box","description":"Select from list","type":"dropdown","docId":null,"value":"Man","options":["Man","Woman"],"lastProcessed":"","lastSurveyed":""},{"label":"Height Formatted Field","description":"Value from 40 to 250 cm","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Favourite Colour List Box","description":"Select from colour spectrum","type":"dropdown","docId":null,"value":"Red","options":["Black","Brown","Red","Orange","Yellow","Green","Blue","Violet","Grey","White"],"lastProcessed":"","lastSurveyed":""},{"label":"Driving License Check Box","description":"Car driving license","type":"checkbox_group","docId":null,"value":["/Off"],"options":["Driving License Check Box"],"lastProcessed":"","lastSurveyed":""},{"label":"Language  Check Box","description":"","type":"checkbox_group","docId":null,"value":["/Off","/Yes","/Off","/Off","/Off"],"options":["Language 1 Check Box","Language 2 Check Box","Language 3 Check Box","Language 4 Check Box","Language 5 Check Box"],"lastProcessed":"","lastSurveyed":""}]}, "docs_data": [{"docId":"app/docs/context/david-q_info.docx__20250530185312","docType":"docx","dateCreated":"2025-05-30 18:53:12","content":"Name: David\n\nHeight: 170cm\n\nAddress: \n\nUrbanización La Antigua \n\nCalle Jade, Casa #435\n\nTres Ríos, Cartago\n\nZip code: 30301"}]}'
```

- Test asking a question related to an unanswered form field

```
curl -X POST http://localhost:7861/api/complete_form_field -H "Content-Type: application/json"  -d '{"form_data": {"formFileName":"app/docs/forms/form-example.pdf","lastSaved":"","fields":[{"label":"Given Name Text Box","description":"First name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Family Name Text Box","description":"Last name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 1 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"House nr Text Box","description":"House and floor","type":"text","docId":null,"value":"ewresd fdsf wr","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 2 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Postcode Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"City Text Box","description":"","type":"text","docId":null,"value":"erewrs erter tertret ert ertertd fsdf ","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Country Combo Box","description":"Use selection or write country name","type":"dropdown","docId":null,"value":"ert t ert","options":["Austria","Belgium","Britain","Bulgaria","Croatia","Cyprus","Czech-Republic","Denmark","Estonia","Finland","France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands","Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden"],"lastProcessed":"","lastSurveyed":""},{"label":"Gender List Box","description":"Select from list","type":"dropdown","docId":null,"value":"Man","options":["Man","Woman"],"lastProcessed":"","lastSurveyed":""},{"label":"Height Formatted Field","description":"Value from 40 to 250 cm","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Favourite Colour List Box","description":"Select from colour spectrum","type":"dropdown","docId":null,"value":"Red","options":["Black","Brown","Red","Orange","Yellow","Green","Blue","Violet","Grey","White"],"lastProcessed":"","lastSurveyed":""},{"label":"Driving License Check Box","description":"Car driving license","type":"checkbox_group","docId":null,"value":["/Off"],"options":["Driving License Check Box"],"lastProcessed":"","lastSurveyed":""},{"label":"Language  Check Box","description":"","type":"checkbox_group","docId":null,"value":["/Off","/Yes","/Off","/Off","/Off"],"options":["Language 1 Check Box","Language 2 Check Box","Language 3 Check Box","Language 4 Check Box","Language 5 Check Box"],"lastProcessed":"","lastSurveyed":""}]}, "unanswered_field": {"label":"Given Name Text Box","description":"First name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""}}'
```

```
curl -X POST http://localhost:7861/api/complete_form_field -H "Content-Type: application/json"  -d '{"form_data": {"formFileName":"app/docs/forms/form-example.pdf","lastSaved":"","fields":[{"label":"Given Name Text Box","description":"First name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Family Name Text Box","description":"Last name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 1 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"House nr Text Box","description":"House and floor","type":"text","docId":null,"value":"ewresd fdsf wr","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 2 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""}]}, "unanswered_field": {"label":"Address 1 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":"", "retries": 0, "valid": false}}'
```

- Test judging the answer to an unanswered form field

> Invalid answer

```
curl -X POST http://localhost:7861/api/judge_answer -H "Content-Type: application/json"  -d '{"form_data": {"formFileName":"app/docs/forms/form-example.pdf","lastSaved":"","fields":[{"label":"Given Name Text Box","description":"First name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Family Name Text Box","description":"Last name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 1 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"House nr Text Box","description":"House and floor","type":"text","docId":null,"value":"ewresd fdsf wr","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 2 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Postcode Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"City Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""}]}, "unanswered_field": {"label":"City Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":"", "retries": 0, "valid": false}, "answer": "upstairs"}'
```

> Valid answer

```
curl -X POST http://localhost:7861/api/judge_answer -H "Content-Type: application/json"  -d '{"form_data": {"formFileName":"app/docs/forms/form-example.pdf","lastSaved":"","fields":[{"label":"Given Name Text Box","description":"First name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Family Name Text Box","description":"Last name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 1 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"House nr Text Box","description":"House and floor","type":"text","docId":null,"value":"ewresd fdsf wr","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 2 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Postcode Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"City Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""}]}, "unanswered_field": {"label":"City Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":"", "retries": 0, "valid": false}, "answer": "cartago"}'
```

## TODO List

1. Integrate graphs with Streamlit UI
2. Complete the implementation of the `complete_form_field` graph
3. Test `manage_form_completion`
4. Synthesize graphs
5. Persist completed PDF form to disk
6. Add ability to preview PDF form
7. Add ability to download PDF form
8. Make the application more robust by completing other TODOs
9. Error handling for thrown errors
10. Give AgentStates in graphs more descriptive names and clean up code
11. Write brief summary of the app's features i.e. add Features section in README.md
