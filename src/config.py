from pydantic_settings import BaseSettings
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
import json
import os

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)
print(f"Loading .env from: {env_file}")


class FirebaseCredentials(BaseModel):
    """Firebase service account credentials"""
    type: str
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
    universe_domain: str


class AppConfig(BaseSettings):
    firebase_credentials_json: str
    environment: str = "development"

    class Config:
        case_sensitive = False

    @property
    def firebase(self) -> FirebaseCredentials:
        """Parse Firebase credentials from JSON string"""
        creds_dict = json.loads(self.firebase_credentials_json)
        return FirebaseCredentials(**creds_dict)


# Load config from environment variables
app_config = AppConfig(
    firebase_credentials_json=os.getenv("FIREBASE_CREDENTIALS", "{}")
)
