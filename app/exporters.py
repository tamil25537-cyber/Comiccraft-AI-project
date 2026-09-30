import os
import re
from datetime import datetime
from fpdf import FPDF

FONT_PATH = "static/fonts/DejaVuSans.ttf"
EXPORT_FOLDER = "static/exports"

class PDF(FPDF):
    pass

def _clean_for_latin1(text: str) -> str:
    """Replaces Unicode characters with standard ASCII equivalents for default fonts."""
    replacements = {
        '“': '"', '”': '"', '‘': "'", '’': "'",
        '—': '-', '–': '-', '…': '...', '•': '*',
        'é': 'e', 'è': 'e', 'á': 'a', 'à': 'a'
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return re.sub(r'[^\x00-\x7F]+', ' ', text)

def save_pdf(layout: list) -> str:
    """
    Compiles the full comic into a multi-page PDF file.
    Each panel's image and narration are placed on separate pages.

    Args:
        layout (list): List of panel layout dictionaries.

    Returns:
        str: Relative path to the generated PDF file.
    """
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    has_unicode_font = False
    if os.path.exists(FONT_PATH):
        try:
            pdf.add_font('DejaVu', '', FONT_PATH)
            pdf.set_font('DejaVu', '', 12)
            font_name = 'DejaVu'
            has_unicode_font = True
        except Exception as e:
            print(f"⚠️ Could not load DejaVu font: {e}")
            pdf.set_font('Helvetica', '', 12)
            font_name = 'Helvetica'
    else:
        pdf.set_font('Helvetica', '', 12)
        font_name = 'Helvetica'

    for panel in layout:
        image_path = panel.get('image_path', '')
        story_text = panel.get('text', '')
        panel_num = panel.get('panel', 1)
        panel_title = panel.get('title', '')

        pdf.add_page()

        # Panel title
        pdf.set_font(font_name, '', 14)
        title_text = f"Panel {panel_num}: {panel_title}" if panel_title else f"Panel {panel_num}"
        if not has_unicode_font:
            title_text = _clean_for_latin1(title_text)
        
        try:
            pdf.cell(0, 10, title_text, ln=True, align="C")
        except TypeError:
            pdf.cell(0, 10, title_text, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font(font_name, '', 11)

        # Image placement
        y_image = 30
        image_height = 100
        spacing_after_image = 15

        clean_img_path = image_path.lstrip("/\\") if image_path else ""
        target_img = clean_img_path if os.path.exists(clean_img_path) else (image_path if os.path.exists(image_path) else None)

        if target_img and os.path.exists(target_img):
            # Center image on page: width = page width - 20, margin x = 10
            pdf.image(target_img, x=10, y=y_image, w=pdf.w - 20, h=image_height)
        else:
            pdf.set_y(y_image)
            pdf.multi_cell(0, 10, f"Image placeholder for Panel {panel_num}")

        # Text placement below image
        pdf.set_y(y_image + image_height + spacing_after_image)
        story_lines = story_text.strip().splitlines()

        # Remove title line like "**Panel 1: Title**" if present
        if story_lines and story_lines[0].strip().lower().startswith("**panel"):
            story_lines = story_lines[1:]

        cleaned_text = "\n".join(story_lines).strip()
        # Clean formatting
        cleaned_text = cleaned_text.replace("**", "")

        if not has_unicode_font:
            cleaned_text = _clean_for_latin1(cleaned_text)

        pdf.multi_cell(0, 8, cleaned_text)

    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    os.makedirs(EXPORT_FOLDER, exist_ok=True)
    pdf_path = os.path.join(EXPORT_FOLDER, filename)
    pdf.output(pdf_path)

    return pdf_path
