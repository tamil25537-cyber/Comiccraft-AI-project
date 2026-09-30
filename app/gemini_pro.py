import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "")
if api_key and api_key != "your_gemini_api_key_here":
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"[WARNING] GenAI configure failed: {e}")

def get_pro_model():
    try:
        return genai.GenerativeModel("models/gemini-1.5-pro")
    except Exception:
        try:
            return genai.GenerativeModel("gemini-1.5-pro")
        except Exception:
            return genai.GenerativeModel("models/gemini-1.5-flash")

def generate_story(outline: list) -> str:
    """
    Generates a detailed comic story with narration and character dialogue
    from a list of comic panel outlines using Gemini 1.5 Pro.

    Args:
        outline (list): A list of dictionaries/strings representing each comic panel's idea.

    Returns:
        str: The generated comic story text or an error message.
    """
    # Format the panel outline as a numbered list for clarity
    formatted_items = []
    for i, item in enumerate(outline):
        if isinstance(item, dict):
            title = item.get("title", f"Panel {i+1}")
            desc = item.get("scene_description", "")
            img_p = item.get("image_prompt", "")
            formatted_items.append(f"Panel {i+1}: {title}\n- Description: {desc}\n- Image Prompt: {img_p}")
        else:
            formatted_items.append(f"{i+1}. {item}")

    formatted_outline = "\n\n".join(formatted_items)

    # Construct the prompt
    prompt = f"""
You're a comic book writer.

Given the following panel breakdown, write a comic-style story with engaging narration and character dialogues for each panel.

Panel Outline:
{formatted_outline}

Guidelines:
- Use a fun and engaging tone, like an actual comic book.
- For each panel, format the header EXACTLY as:
**Panel X: Title**
Followed by:
**CAPTION:** [Brief atmospheric / scene setting caption]
**NARRATION:** [Engaging narration of the character's actions, emotions, or dialogues]
**IMAGE PROMPT:** [Artistic prompt description used for the visual]
- Include narration and clearly marked character lines.
- Keep each panel self-contained but part of a cohesive story.
"""
    try:
        curr_api_key = os.getenv("GEMINI_API_KEY", "")
        if not curr_api_key or curr_api_key == "your_gemini_api_key_here":
            print("[INFO] GEMINI_API_KEY not configured. Generating default story narration fallback.")
            return _generate_fallback_story(outline)

        genai.configure(api_key=curr_api_key)
        model = get_pro_model()
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        return _generate_fallback_story(outline)

    except Exception as e:
        print(f"[ERROR] Error generating story with Gemini: {e}")
        return _generate_fallback_story(outline)


def _generate_fallback_story(outline: list) -> str:
    """Fallback story generator when API key or internet is unavailable."""
    story_parts = []
    for i, panel in enumerate(outline, start=1):
        if isinstance(panel, dict):
            title = panel.get("title", f"Panel {i}")
            desc = panel.get("scene_description", "The scene unfolds.")
            img_p = panel.get("image_prompt", "Comic illustration")
        else:
            title = f"Panel {i}"
            desc = str(panel)
            img_p = "Comic illustration"

        panel_text = f"""**Panel {i}: {title}**
{desc}
**CAPTION:** Whispers carried on the wind, tales of magic and mystery unfolded across the realm...
**NARRATION:** Free, the bravest fox this side of Silverstream, stood at the threshold. The ancient trees loomed like watchful giants, their shadows a daunting promise.
**IMAGE PROMPT:** {img_p}"""
        story_parts.append(panel_text)

    return "\n\n".join(story_parts)
