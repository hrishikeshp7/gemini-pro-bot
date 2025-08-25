import os
import google.generativeai as genai
from google.generativeai.types.safety_types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

# Disable all safety filters
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

# Available models list
AVAILABLE_MODELS = {
    "1": {
        "name": "Gemini 2.5 Pro",
        "id": "gemini-2.5-pro",
        "description": "Most capable model for complex reasoning tasks"
    },
    "2": {
        "name": "Gemini 2.5 Flash",
        "id": "gemini-2.5-flash",
        "description": "Fast and efficient for most tasks"
    },
    "3": {
        "name": "Gemini 2.5 Flash Lite",
        "id": "gemini-2.5-flash-lite",
        "description": "Lightweight version for simple tasks"
    },
    "4": {
        "name": "Gemini 2.5 Flash Live",
        "id": "gemini-2.5-flash-live",
        "description": "Real-time streaming capabilities"
    }
}

DEFAULT_MODEL = "gemini-2.5-flash-lite"

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def get_model(model_id: str = None):
    """Get a model instance with the specified model ID."""
    if model_id is None:
        model_id = DEFAULT_MODEL
    return genai.GenerativeModel(model_id, safety_settings=SAFETY_SETTINGS)


def get_model_list_text():
    """Get formatted text showing available models."""
    text = "🤖 *Available Models:*\n\n"
    for key, model_info in AVAILABLE_MODELS.items():
        text += f"{key}. *{model_info['name']}*\n"
        text += f"   └ {model_info['description']}\n\n"
    text += "Send the number (1-4) to select a model, or send `/model` to see this list again."
    return text


def get_model_name_by_id(model_id: str):
    """Get the display name of a model by its ID."""
    for model_info in AVAILABLE_MODELS.values():
        if model_info['id'] == model_id:
            return model_info['name']
    return "Unknown Model"


# Default model instances (will be replaced with user-specific models)
model = get_model(DEFAULT_MODEL)
img_model = get_model(DEFAULT_MODEL)
