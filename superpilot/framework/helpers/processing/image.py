import os
import base64
import requests
import json
from PIL import Image
import pytesseract
from superpilot.framework.tools.latex import latex_to_text


def remove_image(path):
    try:
        os.remove(path)
    except Exception as e:
        pass
    return True


def extract_text_from_image(path):
    url = "https://api.mathpix.com/v3/text"
    r = requests.post(
        url,
        files={"file": open(path, "rb")},
        data={
            "options_json": json.dumps(
                {"math_inline_delimiters": ["$", "$"], "rm_spaces": True}
            )
        },
        headers={
            "app_id": os.environ.get("MATHPIX_APP_ID"),
            "app_key": os.environ.get("MATHPIX_APP_KEY"),
        },
    )
    return r.json().get("text", "")


def image_to_text(image_path):
    # Load the image from file
    img_path = image_path
    img = Image.open(img_path)
    # Use Tesseract to do OCR on the image
    text = pytesseract.image_to_string(img)
    return text


def image_to_base64(content):
    base64_data = base64.b64encode(content).decode()
    return base64_data


def read_image(image_path):
    try:
        content = requests.get(image_path)
        with open("image.png", "wb") as f:
            f.write(content.content)
        query = extract_text_from_image("image.png")
        query = query.replace("\\", " ")
        if not query:
            query = image_to_text("image.png")
        if not query:
            return {"solution": "We are unable to process this image"}
        try:
            query = latex_to_text(query)
        except Exception as ex:
            query = ""

        base64_string = image_to_base64(content.content)
        remove_image("image.png")
        return base64_string, query
    except Exception as e:
        print("Image error", str(image_path))
        remove_image("image.png")
        return "", ""
