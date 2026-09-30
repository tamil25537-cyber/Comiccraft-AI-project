import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "")
if api_key and api_key != "your_gemini_api_key_here":
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"[WARNING] GenAI configure failed: {e}")

def get_flash_model():
    try:
        return genai.GenerativeModel("models/gemini-1.5-flash")
    except Exception:
        return genai.GenerativeModel("gemini-1.5-flash")

def generate_outline(user_prompt: str) -> list:
    """
    Generates a 5-panel comic layout based on the user's story idea using Gemini.

    Args:
        user_prompt (str): The user's comic idea prompt.

    Returns:
        list: A list of dictionaries, one for each panel.
    """
    prompt = f"""
You are a professional AI comic planner.

Your task is to generate a *strictly formatted* JSON array containing 5 panel descriptions for a comic based on the story idea below:

STORY: "{user_prompt}"

Each JSON object must include:
- "panel" (integer)
- "title" (string)
- "scene_description" (string)
- "image_prompt" (string)

Respond ONLY in this valid JSON format, without any explanations or markdown:
[
  {{
    "panel": 1,
    "title": "Title here",
    "scene_description": "Scene description here",
    "image_prompt": "Image prompt for Stable Diffusion"
  }},
  {{
    "panel": 2,
    "title": "Title here",
    "scene_description": "Scene description here",
    "image_prompt": "Image prompt for Stable Diffusion"
  }},
  {{
    "panel": 3,
    "title": "Title here",
    "scene_description": "Scene description here",
    "image_prompt": "Image prompt for Stable Diffusion"
  }},
  {{
    "panel": 4,
    "title": "Title here",
    "scene_description": "Scene description here",
    "image_prompt": "Image prompt for Stable Diffusion"
  }},
  {{
    "panel": 5,
    "title": "Title here",
    "scene_description": "Scene description here",
    "image_prompt": "Image prompt for Stable Diffusion"
  }}
]
"""
    try:
        curr_api_key = os.getenv("GEMINI_API_KEY", "")
        if not curr_api_key or curr_api_key == "your_gemini_api_key_here":
            print("[INFO] GEMINI_API_KEY not configured. Generating default comic outline fallback.")
            return _generate_fallback_outline(user_prompt)

        genai.configure(api_key=curr_api_key)
        model = get_flash_model()
        response = model.generate_content(prompt)
        output_text = response.text.strip()

        print("\n=== RAW GEMINI RESPONSE ===\n", output_text)

        # Remove any markdown formatting if present
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()
        elif output_text.startswith("```"):
            output_text = output_text.replace("```", "").strip()

        panel_data = json.loads(output_text)

        # Additional structure validation
        if not isinstance(panel_data, list):
            raise ValueError("Gemini response is not a list.")

        for panel in panel_data:
            if not isinstance(panel, dict) or not all(key in panel for key in ("panel", "title", "scene_description", "image_prompt")):
                raise ValueError(f"Invalid panel format or missing keys: {panel}")

        return panel_data

    except json.JSONDecodeError as e:
        print("[ERROR] JSON Decode Error:", e)
        print("[ERROR] Full Text Received:\n", output_text if 'output_text' in locals() else 'None')
        return _generate_fallback_outline(user_prompt)

    except Exception as e:
        print("[ERROR] Unexpected Error in outline generation:", e)
        return _generate_fallback_outline(user_prompt)


def _generate_fallback_outline(user_prompt: str) -> list:
    """Fallback generator in case of network or API key issues."""
    return [
        {
            "panel": 1,
            "title": "The Forest's Edge",
            "scene_description": f"Free, a red fox with intelligent eyes, stands at the edge of a dark, imposing forest. Sunlight barely penetrates the dense canopy. He looks apprehensive but determined.",
            "image_prompt": f"Realistic painting of a red fox, Free, standing at the edge of a dark, mysterious forest. Dramatic lighting, sunlight barely penetrating the trees. Focus on the fox's determined expression."
        },
        {
            "panel": 2,
            "title": "Into the Deep Woods",
            "scene_description": "Free cautiously enters the forest, the path barely visible beneath twisted branches and overgrown foliage. An unnatural silence hangs in the air.",
            "image_prompt": "Realistic painting of a red fox walking through a dense, ancient enchanted forest, glowing moss, sunbeams filtering through giant ancient trees."
        },
        {
            "panel": 3,
            "title": "The Glowing Clearing",
            "scene_description": "Free discovers a mystical clearing illuminated by floating crystalline spores and an enchanted stream.",
            "image_prompt": "Vivid comic art of a magical clearing with a shimmering crystal river, glowing flowers, and a curious fox observing the magic."
        },
        {
            "panel": 4,
            "title": "The Guardian of the Grove",
            "scene_description": "A benevolent spirit shaped like a giant glowing stag appears from the mist, acknowledging Free's courage.",
            "image_prompt": "Majestic glowing spirit stag towering over a small brave red fox in an enchanted misty grove, ethereal lighting, breathtaking scale."
        },
        {
            "panel": 5,
            "title": "A New Destiny",
            "scene_description": "Free receives the blessing of the forest guardian, as golden light envelops the woods, bringing harmony and hope.",
            "image_prompt": "Triumphant final comic panel of a fox bathed in golden magical aurora, overlooking a vast sunlit magical woodland, cinematic masterpiece."
        }
    ]
