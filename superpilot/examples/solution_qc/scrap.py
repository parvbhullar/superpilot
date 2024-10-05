import traceback
import os
import pandas as pd
import json
import requests
import base64
from bs4 import BeautifulSoup as bs
from superpilot.framework.tools.latex import latex_to_text

# from pylatexenc.latex2text import LatexNodes2Text

username = "lauren.pena@spi-global.com"
password = "Straive#160173927"


MATHPIX_APP_ID = os.environ.get("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.environ.get("MATHPIX_APP_KEY")

headers = {}
headers[
    "User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"


def download_file():
    df = pd.read_excel("sample.xlsx")
    records = json.loads(df.T.to_json()).values()
    final_list = []
    for each in list(records)[:500]:
        if each.get("answer_uuid", "") != "":
            session = requests.session()

            login_url = "https://expert.chegg.com/api/auth/login"
            payload = {
                "email": username,
                "password": password
            }
            resp = session.post(login_url, json=payload)
            answer_body = question_body = question_subject = \
                sub_subject_str = topics_str = q_base64 = img_url = q_text = answer_html = ""
            if resp.status_code == 200:
                answer_api = "https://gateway.chegg.com/nestor-graph/graphql"
                answer_payload = {
                    "operationName": "GetQnaQuestionAnswer",
                    "variables": {
                        "uuid": each.get("answer_uuid", ""),
                        # "uuid": "8fb21019-d906-43e2-874c-f4c9b8525956",
                        "filterDeleted": False,
                    },
                    "query": "query GetQnaQuestionAnswer($uuid: UUID!, $filterDeleted: Boolean) {\n  answerByUuid(uuid: $uuid, filterDeleted: $filterDeleted) {\n    id\n    body\n   answeredDate\n    isEditAnswerAllowed\n    template {\n      id\n      __typename\n    }\n    studentRating {\n      positive\n      negative\n      __typename\n    }\n    answeredDate\n    author {\n      firstName\n      lastName\n      imageLink\n      __typename\n    }\n    isDeleted\n    question {\n      id\n      uuid\n      body\n      subject {\n        name\n        subjectGroup {\n          id\n          name\n          __typename\n        }\n        __typename\n      }\n      questionTemplate {\n        templateName\n        templateId\n        __typename\n      }\n      subjectClassification {\n        subSubjects {\n          isTagRecommended\n          subSubject {\n            displayName\n            name\n            uuid\n            __typename\n          }\n          __typename\n        }\n        topics {\n          isTagRecommended\n          topic {\n            displayName\n            name\n            uuid\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      createdDate\n      title\n      langTranslation {\n        body\n        headline\n        translationLanguage\n        __typename\n      }\n      language\n      __typename\n    }\n    qcReview {\n      overallQcRating\n      review {\n        comment\n        parameters {\n          name\n          problemAreas\n          rating\n          __typename\n        }\n        version\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}"
                }

                headers["Apollographql-Client-Name"] = "chegg-web-producers"

                data = session.post(answer_api, json=answer_payload, headers=headers)
                print(each.get("answer_uuid", ""), each.get("preview_url"))
                if data.status_code == 200:
                    try:
                        json_data = data.json()
                        if "errors" not in json_data:
                            json_data = json_data.get("data").get("answerByUuid", {})
                            if json_data:
                                try:
                                    answer_body = json.loads(json_data.get("body", None))
                                    answer_html = generate_html(answer_body)
                                except Exception as e:
                                    traceback.print_exc()
                                    answer_body = json_data.get("body", None)
                                question = json_data.get("question", {})
                                question_body = question.get("body", "")
                                if "<img" in question_body:
                                    html_content = bs(question_body, "lxml")
                                    img_url = html_content.find("img").get("src")
                                    q_base64, q_text = run_img(img_url)
                                    q_text = q_text.strip().replace("\n", "")
                                question_subject = question.get("subject", {}).get("name")
                                subject_classification = question.get("subjectClassification", {})
                                if subject_classification:
                                    sub_subject = subject_classification.get("subSubjects", [])
                                    if sub_subject:
                                        sub_subject_str = ""
                                        for i in sub_subject:
                                            if i.get("subSubject", {}):
                                                sub_subject_str += i.get("subSubject", {}).get("displayName") + ", "

                                    topics = subject_classification.get("topics", [])
                                    if topics:
                                        topics_str = ""
                                        for i in topics:
                                            if i.get("topic", {}):
                                                topics_str += i.get("topic", {}).get("displayName") + ", "
                    except Exception as e:
                        traceback.print_exc()
            each["Answer Body"] = answer_body
            each["Question Body"] = question_body
            each["Answer HTML"] = answer_html
            each["Question Subject"] = question_subject
            each["Sub Subject"] = sub_subject_str
            each["Topic"] = topics_str
            each["Question Base64"] = q_base64
            each["Image URL"] = img_url
            each["Question Text"] = q_text
            final_list.append(each)
    if len(final_list):
        df = pd.DataFrame(final_list)
        df.to_excel('my_dict.xlsx', index=False)


def convert_to_mathjax(content):
    mathjax_content = ""
    if content:
        for item in content:
            if item['type'] == 'text':
                mathjax_content += item['text']
            elif item['type'] == 'inlineMath':
                if item.get("content"):
                    mathjax_content += f"\({item['content'][0]['text']}\)"
    return mathjax_content


def generate_html_all(step, step_count, is_step=True):
    html = ""
    if is_step:
        html += "<h4>Step " + str(step_count) + "</h4>"
    else:
        html += "<h3>Final Answer</h3>"
    for block in step['blocks']:
        if block['type'] == 'TEXT':
            content = block['block']['editorContentState']['content']
            for paragraph in content:
                if paragraph.get("content"):
                    if paragraph['type'] == 'paragraph':
                        html += convert_to_mathjax(paragraph.get("content"))
                    if paragraph['type'] == 'orderedList':
                        if paragraph.get('content'):
                            html += list_order_html(paragraph.get('content'))
                            html += "</br>"
                    elif paragraph['type'] == 'bulletList':
                        if paragraph.get('content'):
                            html += list_order_html(paragraph.get('content'))
                            html += "</br>"
        elif block['type'] == 'EQUATION_RENDERER':
            equation = block['block']['lines'][0]
            html += "<p>"
            html += f"\({equation['left']} = {equation['right']}\)"
            html += "</p>"
        elif block['type'] == 'EXPLANATION':
            html += "<h5>Explanation:</h5>"
            html += "<div style=padding-left:20px;>"
            html += "<i>"
            content = block['block']['editorContentState']['content']
            for paragraph in content:
                if paragraph.get("content"):
                    if paragraph['type'] == 'paragraph':
                        html += "<p>"
                        html += convert_to_mathjax(paragraph['content'])
                        html += "</p>"
                    if paragraph['type'] == 'orderedList':
                        if paragraph.get('content'):
                            html += list_order_html(paragraph.get('content'))
                            html += "</br>"
                    if paragraph['type'] == 'bulletList':
                        if paragraph.get('content'):
                            html += list_order_html(paragraph.get('content'))
                            html += "</br>"
            html += "</i></div>"
    return html


def list_order_html(data):
    html = ""
    for each_para_content in data:
        if each_para_content.get("type") == "text":
            html += "<p>" + each_para_content.get("text") + "</p>"
        if each_para_content.get("type") == "listItem":
            html += list_item_html(each_para_content.get("content"))
        if each_para_content.get("content") == "inlineMath":
            for each_inner_content in each_para_content.get("content"):
                html += "<p>" + convert_to_mathjax(each_inner_content.get('content')) + "</p>"
    return html


# Function to generate HTML from JSON data
def generate_html(data):
    html = ""
    step_count = 1
    k = ""
    if data.get("stepByStep", {}).get("steps", []):
        for step in data['stepByStep']['steps']:
            k += generate_html_all(step, step_count, is_step=True)
            step_count += 1
        html += k
        html += generate_html_all(data['finalAnswer'], step_count, False)
    return html


def list_item_html(data):
    content = ""
    for i in data:
        if i.get("type") == "bulletList":
            for j in i.get("content"):
                if j.get("type") == "listItem":
                    content += "<ul>" + list_item_html(j.get("content")) + "</ul>"
        if i.get("type") == "paragraph":
            content += "<li>" + convert_to_mathjax(i.get("content")) + "</li>"
    return content


def extract_text_from_image(path):
    # !/usr/bin/env python
    import requests
    import json
    import os

    r = requests.post(
        "https://api.mathpix.com/v3/text",
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
    # print(r.text, "Mathpix response")
    return r.json().get("text", "")


def image_to_text(image_path):
    from PIL import Image
    import pytesseract

    # Load the image from file
    img_path = image_path
    img = Image.open(img_path)
    # Use Tesseract to do OCR on the image
    text = pytesseract.image_to_string(img)
    return text


def run_img(image_path):
    try:
        content = requests.get(image_path)
        with open("image.png", "wb") as f:
            f.write(content.content)
        # query = self.image_to_text(image_path)
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
        return base64_string, query
    except Exception as e:
        print("Image error", str(image_path))
        return "", ""


def image_to_base64(content):
    base64_data = base64.b64encode(content).decode()
    return base64_data

# 
# def latex_to_text(latex):
#     if latex is None:
#         return latex
#     return LatexNodes2Text().latex_to_text(latex)


def create_mathjax_span(item_text):
    span_html = f'''<span>\({item_text}\)</span>'''
    return span_html


download_file()
