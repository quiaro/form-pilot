from dotenv import load_dotenv, find_dotenv
import os
import sys

def setup():
    """
    Set up the environment for the application.
    
    This function:
    1. In development mode, loads environment variables from a .env file
    2. In production mode, verifies the presence of required API keys
    3. Configures API keys in the environment
    
    Raises:
        SystemExit: If the .env file is not found or required environment variables are missing
    """
    if os.getenv("ENV", "development").lower() == "development":
      dotenv_path = find_dotenv(usecwd=True)
      if not dotenv_path:
          print("Error: .env file not found in the current directory or parent directories.")
          sys.exit(1)

      load_dotenv(dotenv_path)
