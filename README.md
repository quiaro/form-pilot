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
