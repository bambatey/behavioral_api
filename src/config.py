from pydantic_settings import BaseSettings
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)
print(f"Loading .env from: {env_file}")
 

class AppConfig(BaseSettings):
    firebase_credentials_path: str  # Path to serviceAccountKey.json
    firebase_project_id: str
    environment: str = "development"

    class Config:
        env_file = str(env_file)
        case_sensitive = False


# Load config from environment variables
app_config = AppConfig()
