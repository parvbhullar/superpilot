# flake8: noqa
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.framework.helpers.processing.text import write_to_file, md_to_pdf

from superpilot.examples.ed_tech.teacher_guide.guide_executor import GuideExecutor
import fitz  # PyMuPDF


def read_pdf(file_path):
    # Open the PDF file
    pdf_document = fitz.open(file_path)
    text = ""
    for page in pdf_document:
        text += "\n" + page.get_text()
    print(text)
    # Iterate through pages
    # for page_number in range(pdf_document.page_count):
    #     # Get the page
    #     page = pdf_document[page_number]
    #
    #     # Get the text from the page
    #     text = page.get_text("text")
    #
    #     # Print or manipulate the text as needed
    #     print(f"Page {page_number + 1}:\n{text}\n")
    #
    # # Close the PDF file
    pdf_document.close()

    return text


def write_guide(file_path):
    chapter = read_pdf(file_path)
    guide_executor = GuideExecutor()
    guide = asyncio.run(guide_executor.run(chapter))
    write_md_to_pdf("Teacher’s Guide Class 8", guide)


def write_md_to_pdf(file_name, text: str) -> None:
    file_path = f"/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/guides/{file_name}"
    write_to_file(f"{file_path}.md", text)
    md_to_pdf(f"{file_path}.md", f"{file_path}.pdf")
    print(f"F written to {file_path}.pdf")


if __name__ == "__main__":
    path = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/guides/Computers for Class VI Chapter 1.pdf"

    # math_pics_ocr(path)
    # path = "original/Chegg Ques/Screenshot_2023-10-21_103505.png"
    # path = "original/Chegg Ques/Screenshot 2023-10-21 102000.png"
    write_guide(path)
    # for i in range(1, 5):
    # solve_question(path)
    # extract_text_from_image(path)

    # path = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/"
    # process_directory_images(path)
