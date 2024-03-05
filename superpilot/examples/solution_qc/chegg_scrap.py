import json
import os
import traceback
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs

from superpilot.examples.solution_qc.utils import generate_html
from superpilot.framework.helpers.processing.image import read_image


CHEGG_USERNAME = os.environ.get("CHEGG_USERNAME")
CHEGG_PASSWORD = os.environ.get("CHEGG_PASSWORD")

MATHPIX_APP_ID = os.environ.get("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.environ.get("MATHPIX_APP_KEY")

SESSION_HEADERS = {}
SESSION_HEADERS[
    "User-Agent"
] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

CHEGG_URL = "https://expert.chegg.com/api/auth/login"
ANSWER_API = "https://gateway.chegg.com/nestor-graph/graphql"


def request_chegg(each):
    session = requests.session()
    payload = {"email": CHEGG_USERNAME, "password": CHEGG_PASSWORD}
    resp = session.post(CHEGG_URL, json=payload)
    if resp.status_code == 200:
        answer_payload = {
            "operationName": "GetQnaQuestionAnswer",
            "variables": {
                "uuid": each.get("answer_uuid", ""),
                "filterDeleted": False,
            },
            "query": "query GetQnaQuestionAnswer($uuid: UUID!, $filterDeleted: Boolean) {\n  answerByUuid(uuid: $uuid, filterDeleted: $filterDeleted) {\n    id\n    body\n   answeredDate\n    isEditAnswerAllowed\n    template {\n      id\n      __typename\n    }\n    studentRating {\n      positive\n      negative\n      __typename\n    }\n    answeredDate\n    author {\n      firstName\n      lastName\n      imageLink\n      __typename\n    }\n    isDeleted\n    question {\n      id\n      uuid\n      body\n      subject {\n        name\n        subjectGroup {\n          id\n          name\n          __typename\n        }\n        __typename\n      }\n      questionTemplate {\n        templateName\n        templateId\n        __typename\n      }\n      subjectClassification {\n        subSubjects {\n          isTagRecommended\n          subSubject {\n            displayName\n            name\n            uuid\n            __typename\n          }\n          __typename\n        }\n        topics {\n          isTagRecommended\n          topic {\n            displayName\n            name\n            uuid\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      createdDate\n      title\n      langTranslation {\n        body\n        headline\n        translationLanguage\n        __typename\n      }\n      language\n      __typename\n    }\n    qcReview {\n      overallQcRating\n      review {\n        comment\n        parameters {\n          name\n          problemAreas\n          rating\n          __typename\n        }\n        version\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}",
        }
        SESSION_HEADERS["Apollographql-Client-Name"] = "chegg-web-producers"
        data = session.post(ANSWER_API, json=answer_payload, headers=SESSION_HEADERS)
        # print(each.get("answer_uuid", ""), each.get("preview_url"))
        return data
    return resp


def process_chegg_file(input_path, output_path):
    df = pd.read_excel(input_path)
    records = json.loads(df.T.to_json()).values()
    total_count = len(records)
    final_list = []
    for each in list(records)[:500]:
        if each.get("answer_uuid", "") != "":
            data = request_chegg(each)
            answer_body = (
                question_body
            ) = (
                question_subject
            ) = (
                sub_subject_str
            ) = topics_str = q_base64 = img_url = q_text = answer_html = ""
            print(
                each.get("answer_uuid", ""), each.get("preview_url"), data.status_code
            )
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
                                q_base64, q_text = read_image(img_url)
                                q_text = q_text.strip().replace("\n", "")
                            question_subject = question.get("subject", {}).get("name")
                            subject_classification = question.get(
                                "subjectClassification", {}
                            )
                            if subject_classification:
                                sub_subject = subject_classification.get(
                                    "subSubjects", []
                                )
                                if sub_subject:
                                    sub_subject_str = ""
                                    for i in sub_subject:
                                        if i.get("subSubject", {}):
                                            sub_subject_str += (
                                                i.get("subSubject", {}).get(
                                                    "displayName"
                                                )
                                                + ", "
                                            )

                                topics = subject_classification.get("topics", [])
                                if topics:
                                    topics_str = ""
                                    for i in topics:
                                        if i.get("topic", {}):
                                            topics_str += (
                                                i.get("topic", {}).get("displayName")
                                                + ", "
                                            )
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
        df.to_excel(output_path, index=False)
    return output_path, len(final_list), total_count
