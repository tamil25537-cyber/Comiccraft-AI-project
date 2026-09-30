import os
import re
import hashlib
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

# Initialize diffusers pipeline if available and requested
pipe = None
USE_LOCAL_DIFFUSERS = os.getenv("USE_LOCAL_DIFFUSERS", "false").lower() == "true"
HF_API_KEY = os.getenv("HF_API_KEY", "")

if USE_LOCAL_DIFFUSERS:
    try:
        import torch
        from diffusers import StableDiffusionPipeline
        model_id = "runwayml/stable-diffusion-v1-5"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)
        pipe = pipe.to(device)
        print("[INFO] Stable Diffusion pipeline loaded successfully on", device)
    except Exception as e:
        print(f"[WARNING] Could not initialize local diffusers pipeline: {e}")
        pipe = None


def sanitize_filename(prompt: str) -> str:
    """Creates a clean and safe filename from the image prompt."""
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', prompt[:30]).strip('_')
    if not cleaned:
        cleaned = "panel"
    hash_str = hashlib.md5(prompt.encode('utf-8')).hexdigest()[:8]
    return f"{cleaned}_{hash_str}.png"


def _generate_via_hf_api(prompt: str, token: str) -> Image.Image:
    """Attempts to generate image using Hugging Face Inference API."""
    api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt}
    response = requests.post(api_url, headers=headers, json=payload, timeout=45)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    raise Exception(f"HF API returned status {response.status_code}: {response.text}")


def _generate_artistic_comic_placeholder(prompt: str) -> Image.Image:
    """
    Generates a high quality comic book style illustration placeholder image
    with vivid colors, stylized framing, and title typography.
    """
    width, height = 512, 512
    h_val = int(hashlib.md5(prompt.encode('utf-8')).hexdigest()[:6], 16)
    r = (h_val & 0xFF0000) >> 16
    g = (h_val & 0x00FF00) >> 8
    b = h_val & 0x0000FF

    top_color = (max(20, min(240, r)), max(20, min(240, g)), max(50, min(250, b)))
    bottom_color = (max(10, r // 2), max(10, g // 2), max(20, b // 2))

    img = Image.new("RGB", (width, height), top_color)
    draw = ImageDraw.Draw(img)

    # Vertical gradient
    for y in range(height):
        ratio = y / height
        cur_r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        cur_g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        cur_b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(cur_r, cur_g, cur_b))

    # Halftone / comic dots aesthetic
    for x in range(10, width, 24):
        for y in range(10, height, 24):
            draw.ellipse([x, y, x + 3, y + 3], fill=(255, 255, 255))

    # Comic border / vignette
    draw.rectangle([8, 8, width - 8, height - 8], outline=(20, 20, 20), width=6)
    draw.rectangle([14, 14, width - 14, height - 14], outline=(255, 255, 255), width=2)

    # Sunburst / dramatic dynamic comic lines
    center_x, center_y = width // 2, height // 2 - 30
    import math
    for angle_deg in range(0, 360, 30):
        rad = math.radians(angle_deg)
        x2 = center_x + int(300 * math.cos(rad))
        y2 = center_y + int(300 * math.sin(rad))
        draw.line([(center_x, center_y), (x2, y2)], fill=(255, 255, 255), width=1)

    # Central comic emblem / badge
    badge_radius = 90
    draw.ellipse(
        [center_x - badge_radius, center_y - badge_radius, center_x + badge_radius, center_y + badge_radius],
        fill=(20, 25, 40),
        outline=(255, 215, 0),
        width=4
    )

    # Comic icon in center
    draw.polygon([
        (center_x, center_y - 45),
        (center_x + 35, center_y + 35),
        (center_x - 35, center_y + 35)
    ], fill=(255, 140, 0), outline=(255, 255, 255))

    draw.polygon([
        (center_x, center_y - 20),
        (center_x + 18, center_y + 25),
        (center_x - 18, center_y + 25)
    ], fill=(255, 255, 255))

    # Text overlay at bottom banner
    banner_y = height - 90
    draw.rectangle([20, banner_y, width - 20, height - 25], fill=(0, 0, 0), outline=(255, 215, 0), width=2)

    # Truncated prompt text
    display_text = prompt[:55] + ("..." if len(prompt) > 55 else "")
    draw.text((30, banner_y + 12), "COMICCRAFT ILLUSTRATION", fill=(255, 215, 0))
    draw.text((30, banner_y + 34), display_text, fill=(220, 220, 220))

    return img


def generate_image(prompt: str, filename: str = None) -> str:
    """
    Generates a comic-style image based on the provided prompt and saves it.

    Args:
        prompt (str): Prompt describing the scene.
        filename (str, optional): Custom filename.

    Returns:
        str: Relative path to saved image.
    """
    if not filename:
        filename = sanitize_filename(prompt)

    path = f"static/panels/{filename}"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 1. Try local Diffusers pipeline if loaded
    if pipe is not None:
        try:
            image = pipe(prompt).images[0]
            image.save(path)
            return path
        except Exception as e:
            print(f"[WARNING] Diffusers error: {e}, attempting fallback...")

    # 2. Try Hugging Face Inference API if token provided
    curr_hf_token = os.getenv("HF_API_KEY", "")
    if curr_hf_token and curr_hf_token != "your_huggingface_api_key_here":
        try:
            image = _generate_via_hf_api(prompt, curr_hf_token)
            image.save(path)
            return path
        except Exception as e:
            print(f"[WARNING] HF API error: {e}, falling back to built-in generator...")

    # 3. Built-in high-quality comic illustrator
    image = _generate_artistic_comic_placeholder(prompt)
    image.save(path)
    return path
