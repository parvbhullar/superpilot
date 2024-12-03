import os
import sys
import asyncio
import time
import chardet

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import io
from typing import IO, Any
from chardet.universaldetector import UniversalDetector
from email.parser import Parser

TEXT_SECTION_SEPARATOR = "\n\n"


def detect_encoding(file: IO[bytes]) -> str:
    raw_data = file.read(50000)
    encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
    file.seek(0)
    return encoding


def eml_to_text(file: IO[Any]) -> str:
    text_file = io.TextIOWrapper(file, encoding=detect_encoding(file))
    parser = Parser()
    message = parser.parse(text_file)
    text_content = []
    for part in message.walk():
        if part.get_content_type().startswith("text/plain"):
            text_content.append(part.get_payload())
    return TEXT_SECTION_SEPARATOR.join(text_content)