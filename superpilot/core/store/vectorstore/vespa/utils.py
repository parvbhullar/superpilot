import re
import zipfile
from typing import BinaryIO
import io
import re

# NOTE: This does not seem to be used in reality despite the Vespa Docs pointing to this code
# See here for reference: https://docs.vespa.ai/en/documents.html
# https://github.com/vespa-engine/vespa/blob/master/vespajlib/src/main/java/com/yahoo/text/Text.java

# Define allowed ASCII characters
ALLOWED_ASCII_CHARS: list[bool] = [False] * 0x80
ALLOWED_ASCII_CHARS[0x9] = True  # tab
ALLOWED_ASCII_CHARS[0xA] = True  # newline
ALLOWED_ASCII_CHARS[0xD] = True  # carriage return
for i in range(0x20, 0x7F):
    ALLOWED_ASCII_CHARS[i] = True  # printable ASCII chars
ALLOWED_ASCII_CHARS[0x7F] = True  # del - discouraged, but allowed


def is_text_character(codepoint: int) -> bool:
    """Returns whether the given codepoint is a valid text character."""
    if codepoint < 0x80:
        return ALLOWED_ASCII_CHARS[codepoint]
    if codepoint < 0xD800:
        return True
    if codepoint <= 0xDFFF:
        return False
    if codepoint < 0xFDD0:
        return True
    if codepoint <= 0xFDEF:
        return False
    if codepoint >= 0x10FFFE:
        return False
    return (codepoint & 0xFFFF) < 0xFFFE


def replace_invalid_doc_id_characters(text: str) -> str:
    """Replaces invalid document ID characters in text."""
    # There may be a more complete set of replacements that need to be made but Vespa docs are unclear
    # and users only seem to be running into this error with single quotes
    return text.replace("'", "_")


def remove_invalid_unicode_chars(text: str) -> str:
    """Vespa does not take in unicode chars that aren't valid for XML.
    This removes them."""
    _illegal_xml_chars_RE: re.Pattern = re.compile(
        "[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]"
    )
    return _illegal_xml_chars_RE.sub("", text)



def fix_vespa_app_name(app_name):
    # Convert to lowercase
    app_name = app_name.lower()

    # Remove invalid characters (keep only letters and digits)
    app_name = re.sub(r'[^a-z0-9]', '', app_name)

    # Ensure it starts with a letter
    app_name = re.sub(r'^[^a-z]+', '', app_name)

    # Trim to 20 characters
    app_name = app_name[:20]

    # If the string is empty after cleanup, default to 'a'
    if not app_name:
        app_name = 'a'

    return app_name

def in_memory_zip_from_file_bytes(file_contents: dict[str, bytes]) -> BinaryIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in file_contents.items():
            zipf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer


def create_document_xml_lines(doc_names: list[str | None]) -> str:
    doc_lines = [
        f'<document type="{doc_name}" mode="index" />'
        for doc_name in doc_names
        if doc_name
    ]
    return "\n".join(doc_lines)
