from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


UNICODE_FONT_NAME = "NotoSansBold"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UNICODE_FONT_PATH = PROJECT_ROOT / "fonts" / "NotoSans-Bold.ttf"


def register_unicode_font():
    if not UNICODE_FONT_PATH.is_file():
        raise FileNotFoundError(
            f"Unicode font not found: {UNICODE_FONT_PATH}"
        )

    registered_fonts = pdfmetrics.getRegisteredFontNames()

    if UNICODE_FONT_NAME not in registered_fonts:
        pdfmetrics.registerFont(
            TTFont(
                UNICODE_FONT_NAME,
                str(UNICODE_FONT_PATH)
            )
        )

    return UNICODE_FONT_NAME