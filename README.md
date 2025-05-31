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

Agentic app to make filling PDF forms effortless. Upload a PDF form and let the agent do the rest. It consists of a FastAPI backend that uses LangGraph to process queries and a React frontend.

## Features

TO-DO

## Setup and Installation

### Prerequisites

- Python 3.13+
- Node.js 22+
- npm
- Docker (optional, for containerized deployment)

### Backend

1. Navigate to the backend directory:

   ```
   cd backend
   ```

2. Create virtual environment using uv:

   ```
   uv venv .venv
   ```

3. Activate virtual environment:

   ```
   source .venv/bin/activate
   ```

4. Install dependencies using uv:

   ```
   uv pip install -r requirements.txt
   ```

5. Create a `.env` file from the example:

   ```
   cp .env.example .env
   ```

6. Edit the `.env` file to add the different API keys:

7. Start the server:
   ```
   python -m app.main
   ```

### Frontend

1. Navigate to the frontend directory:

   ```
   cd frontend
   ```

2. Install dependencies:

   ```
   npm install
   ```

3. Start the development server:

   ```
   npm run dev
   ```

4. Open your browser and go to http://localhost:3000

## Usage

1. Select a category from the dropdown menu
2. Click "Show me trending information"
3. View the real-time streaming response in the content section

## Troubleshooting

### Common Issues

- **OpenAI API Key Error**: If you see an error about the OpenAI API key, make sure:

  - You have created a `.env` file in the backend directory
  - The file contains `OPENAI_API_KEY=sk-your-actual-api-key-here` with your real API key
  - There are no spaces around the equals sign
  - The API key is valid and has not expired

## Test Strings

Test parsing of the PDF form

```
curl -X POST "http://localhost:7860/api/parse_pdf_form" -H "Content-Type: application/json" -d '{"pdf_file": "app/docs/forms/form-example.pdf"}'
```

Test the loading of supporting documents into memory
(To test this, create a Word document with information related to the fields in the form)

```
curl -X POST http://localhost:7860/api/load_context  -H "Content-Type: application/json"   -d '{"document_filepaths": ["app/docs/context/info.docx"]}'
```

Test pre-filling of a form using supporting documents

```
curl -X POST http://localhost:7860/api/pre_fill_form  -H "Content-Type: application/json"   -d '{"form_data": {"formFileName":"app/docs/forms/form-example.pdf","lastSaved":"","fields":[{"label":"Given Name Text Box","description":"First name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Family Name Text Box","description":"Last name","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 1 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"House nr Text Box","description":"House and floor","type":"text","docId":null,"value":"ewresd fdsf wr","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Address 2 Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Postcode Text Box","description":"","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"City Text Box","description":"","type":"text","docId":null,"value":"erewrs erter tertret ert ertertd fsdf ","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Country Combo Box","description":"Use selection or write country name","type":"dropdown","docId":null,"value":"ert t ert","options":["Austria","Belgium","Britain","Bulgaria","Croatia","Cyprus","Czech-Republic","Denmark","Estonia","Finland","France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands","Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden"],"lastProcessed":"","lastSurveyed":""},{"label":"Gender List Box","description":"Select from list","type":"dropdown","docId":null,"value":"Man","options":["Man","Woman"],"lastProcessed":"","lastSurveyed":""},{"label":"Height Formatted Field","description":"Value from 40 to 250 cm","type":"text","docId":null,"value":"","options":[],"lastProcessed":"","lastSurveyed":""},{"label":"Favourite Colour List Box","description":"Select from colour spectrum","type":"dropdown","docId":null,"value":"Red","options":["Black","Brown","Red","Orange","Yellow","Green","Blue","Violet","Grey","White"],"lastProcessed":"","lastSurveyed":""},{"label":"Driving License Check Box","description":"Car driving license","type":"checkbox_group","docId":null,"value":["/Off"],"options":["Driving License Check Box"],"lastProcessed":"","lastSurveyed":""},{"label":"Language  Check Box","description":"","type":"checkbox_group","docId":null,"value":["/Off","/Yes","/Off","/Off","/Off"],"options":["Language 1 Check Box","Language 2 Check Box","Language 3 Check Box","Language 4 Check Box","Language 5 Check Box"],"lastProcessed":"","lastSurveyed":""}]}, "docs_data": [{"docId":"app/docs/context/david-q_info.docx__20250530185312","docType":"docx","dateCreated":"2025-05-30 18:53:12","content":"Name: David\n\nHeight: 170cm\n\nAddress: \n\nUrbanización La Antigua \n\nCalle Jade, Casa #435\n\nTres Ríos, Cartago\n\nZip code: 30301"}]}'
```
