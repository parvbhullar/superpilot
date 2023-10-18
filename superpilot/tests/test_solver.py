# flake8: noqa
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.ed_tech.question_executor import QuestionExecutor
from superpilot.framework.tools.latex import latex_to_text
import pandas as pd


def solve_question(image_path):
    t1 = time.time()
    executor = QuestionExecutor()
    print("\n", "*" * 32, "Running QuestionExecutor", "*" * 32, "\n\n")
    res = asyncio.run(executor.run(image_path))
    print(res)
    # print(res.content.get("status"))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")


def extract_latex_from_image(path):
    from PIL import Image
    from pix2tex.cli import LatexOCR

    img = Image.open(path)
    model = LatexOCR()
    print(model(img))

def extract_text_from_image(path):
    ACCESS_KEY = 'AKIA5UPPEATFLZART5OB'
    SECRET_KEY = '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'
    import boto3
    client = boto3.client('textract', region_name='ap-south-1', aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY)

    with open(path, 'rb') as document:
        img_test = document.read()
        image_bytes = bytearray(img_test)
    # response = client.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['TABLES'])
        # Call Amazon Textract
    response = client.detect_document_text(Document={'Bytes': image_bytes})

    # Parse the results
    detected_text = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            detected_text.append(item["Text"])
    detected_text = "\n".join(detected_text)
    print(detected_text)
    return detected_text


def process_directory_images(dir_path):
    """Iterate over all images in the directory and extract text using OCR."""

    # Supported image extensions, you can add more if needed
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

    # Iterate over files in directory
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                full_path = os.path.join(root, file)
                print(f"Processing: {full_path}")

                # Extract text using OCR
                text = extract_text_from_image(full_path)

                # Print or save the extracted text as needed
                print(text)
                print('-' * 40)



if __name__ == "__main__":
    path = '/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/WhatsApp Image 2023-10-03 at 8.31.50 PM.jpeg'
    path = '/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/Ques20.png'
    solve_question(path)
    # extract_text_from_image(path)

    path = '/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/'
    # process_directory_images(path)