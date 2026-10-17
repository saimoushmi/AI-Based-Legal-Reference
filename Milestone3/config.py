import os
from dotenv import load_dotenv
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

# Load from .env if present
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "Milestone2", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def _get_setting(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except StreamlitSecretNotFoundError:
        return default


OPENAI_API_KEY = _get_setting("OPENAI_API_KEY")
GOOGLE_API_KEY = _get_setting("GOOGLE_API_KEY")
PINECONE_API_KEY = _get_setting("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = _get_setting("PINECONE_ENVIRONMENT", "us-east1-aws")
PINECONE_INDEX_NAME = _get_setting("PINECONE_INDEX_NAME", "legal-chatbot")
