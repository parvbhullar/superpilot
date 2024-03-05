# flake8: noqa


def convert_to_mathjax(content):
    mathjax_content = ""
    if content:
        for item in content:
            if item["type"] == "text":
                mathjax_content += item["text"]
            elif item["type"] == "inlineMath":
                if item.get("content"):
                    mathjax_content += f"\({item['content'][0]['text']}\)"
    return mathjax_content


def generate_html_all(step, step_count, is_step=True):
    html = ""
    if is_step:
        html += "<h4>Step " + str(step_count) + "</h4>"
    else:
        html += "<h3>Final Answer</h3>"
    for block in step["blocks"]:
        if block["type"] == "TEXT":
            content = block["block"]["editorContentState"]["content"]
            for paragraph in content:
                if paragraph.get("content"):
                    if paragraph["type"] == "paragraph":
                        html += convert_to_mathjax(paragraph.get("content"))
                    if paragraph["type"] == "orderedList":
                        if paragraph.get("content"):
                            html += list_order_html(paragraph.get("content"))
                            html += "</br>"
                    elif paragraph["type"] == "bulletList":
                        if paragraph.get("content"):
                            html += list_order_html(paragraph.get("content"))
                            html += "</br>"
        elif block["type"] == "EQUATION_RENDERER":
            equation = block["block"]["lines"][0]
            html += "<p>"
            html += f"\({equation['left']} = {equation['right']}\)"
            html += "</p>"
        elif block["type"] == "EXPLANATION":
            html += "<h5>Explanation:</h5>"
            html += "<div style=padding-left:20px;>"
            html += "<i>"
            content = block["block"]["editorContentState"]["content"]
            for paragraph in content:
                if paragraph.get("content"):
                    if paragraph["type"] == "paragraph":
                        html += "<p>"
                        html += convert_to_mathjax(paragraph["content"])
                        html += "</p>"
                    if paragraph["type"] == "orderedList":
                        if paragraph.get("content"):
                            html += list_order_html(paragraph.get("content"))
                            html += "</br>"
                    if paragraph["type"] == "bulletList":
                        if paragraph.get("content"):
                            html += list_order_html(paragraph.get("content"))
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
                html += (
                    "<p>"
                    + convert_to_mathjax(each_inner_content.get("content"))
                    + "</p>"
                )
    return html


# Function to generate HTML from JSON data
def generate_html(data):
    html = ""
    step_count = 1
    k = ""
    if data.get("stepByStep", {}).get("steps", []):
        for step in data["stepByStep"]["steps"]:
            k += generate_html_all(step, step_count, is_step=True)
            step_count += 1
        html += k
        html += generate_html_all(data["finalAnswer"], step_count, False)
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


def create_mathjax_span(item_text):
    span_html = f"""<span>\({item_text}\)</span>"""
    return span_html


class EmptyObject(object):
    pass
