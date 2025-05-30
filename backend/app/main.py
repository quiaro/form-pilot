import os
from app.utils.setup import setup

# Call setup to initialize environment
setup()

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import markdown
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import build_graph, create_agent_state
from datetime import datetime


graph = build_graph()
app = FastAPI(title="Form Pilot")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Valid categories
VALID_CATEGORIES = [
    "Business and Finance",
    "Entertainment",
    "Food and Drink",
    "Games",
    "Health",
    "Hobbies and Leisure",
    "Jobs and Education",
    "Science",
    "Sports",
    "Technology"
]

async def stream_agent_response(category: str):
    """
    Stream the agent's response for a given category.
    
    Args:
        category: The trending category to query
        
    Yields:
        Chunks of the agent's response as HTML
    """
    # Create the initial prompt
    prompt = f"Find some information related to this {category.lower()} from Google and Reddit. The information provided must be up to date. Today is {datetime.now().strftime('%B')} {datetime.now().day}, {datetime.now().year}. "
    
    # Initialize state
    state = create_agent_state(messages=[HumanMessage(content=prompt)])
    
    # Process through the graph
    try:
        async for chunk in graph.astream(state, stream_mode="updates"):
            for node, values in chunk.items():
                # Only yield messages from the agent
                if node == "agent":
                    last_message = values["messages"][-1].text()
                    if last_message != "":
                        # Convert markdown to HTML
                        html_content = markdown.markdown(last_message)
                        yield html_content

    except Exception as e:
        # Log the error but don't raise it to avoid breaking the stream
        print(f"Error in streaming response: {str(e)}")
        yield f"\n\nError during response generation: {str(e)}"


@app.get("/api/trending/{category}")
async def get_trending(
    category: str = Path(..., description="The category to get trending information for")
):
    """
    Get trending information for a specific category.
    
    Args:
        category: The category to get trending information for
        
    Returns:
        A streaming response with trending information as HTML
    """
    # Validate category
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
    # Return streaming response
    return StreamingResponse(
        stream_agent_response(category),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",  # Disable buffering for Nginx
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/api/categories")
async def get_categories():
    """
    Get the list of valid categories.
    
    Returns:
        List of valid categories
    """
    return {"categories": VALID_CATEGORIES}

# Determine the frontend build directory 
# If in Docker, the frontend build is at /app/frontend/build
# If running locally, use relative path ../frontend/build
FRONTEND_BUILD_DIR = "/app/frontend/build"
FRONTEND_STATIC_DIR = os.path.join(FRONTEND_BUILD_DIR, "assets")
FRONTEND_INDEX_HTML = os.path.join(FRONTEND_BUILD_DIR, "index.html")

# Mount the frontend build folder (only in production)
if os.getenv("ENV", "development").lower() == "production":
    print("Production environment detected")
    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(FRONTEND_INDEX_HTML)

    # Catch-all route to serve React Router paths
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        # If the path is an API endpoint, skip this handler
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Check if a static file exists in the build folder
        static_file_path = os.path.join(FRONTEND_BUILD_DIR, full_path)
        if os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
        
        # Otherwise, serve the index.html for client-side routing
        return FileResponse(FRONTEND_INDEX_HTML)

    # Mount static files (JavaScript, CSS, images)
    app.mount("/assets", StaticFiles(directory=FRONTEND_STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    env = os.getenv("ENV", "development")
    
    # Only enable auto-reload in development
    reload = env.lower() == "development"
    
    uvicorn.run("app.main:app", host=host, port=port) 