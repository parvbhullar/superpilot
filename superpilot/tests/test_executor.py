# flake8: noqa
import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.executor import (
    StableDiffusionPromptExecutor,
    MidjourneyPromptPromptExecutor,
    StableDiffusionImageExecutor,
    QuestionIdentifierPromptExecutor,
    LatexCodeGenExecutor,
    ClipDropImageExecutor,
    QuestionExtractorExecutor
)
from superpilot.framework.tools.latex import latex_to_text
import pandas as pd

# sd_prompt = StableDiffusionPromptExecutor()
# print("\n", "*" * 32, "Running StableDiffusionPromptExecutor", "*" * 32, "\n\n")
# res = asyncio.run(sd_prompt.run("a photo of a cat"))
# print(res.content)


# sd_prompt = MidjourneyPromptPromptExecutor()
# print("\n", "*" * 32, "Running MidjourneyPromptPromptExecutor", "*" * 32, "\n\n")
# res = asyncio.run(sd_prompt.run("a photo of a cat"))
# print(res.content)


# sd_prompt = StableDiffusionImageExecutor()
# from PIL import Image

# print("\n", "*" * 32, "Running StableDiffusionImageExecutor", "*" * 32, "\n\n")
# context = asyncio.run(sd_prompt.run("a photo of a cat"))
# for item in context.items:
#     print(item.description)
#     Image.open(item.file_path).show()

# cd_prompt = ClipDropImageExecutor()
# from PIL import Image

# print("\n", "*" * 32, "Running ClipDropImageExecutor", "*" * 32, "\n\n")
# context = asyncio.run(cd_prompt.run("A Man drinking beer & playing with dog"))
# for item in context.items:
#     print(item.description)
#     Image.open(item.file_path).show()

# data_df = pd.read_excel("/home/dora/Downloads/Cloudbird Done Data.xlsx", sheet_name="9 sep")
neg_content = """
A landscape space that is dominated by white, grey, blue, and green colors, suggest which of the following sensory responses of human actions?  A) Gay, lively  B) Relaxing, stable  C) Frightening, inhibiting  D) Regressive, detached
"""

ques = """
The ______exercises all authority over the establishment of education, experience, and other criteria for licensing, certification, and re-certification of qualified appraisers."""

ques1 = """
A technician wants to share a printer on the network but according to the company policy, no PC should have a directly connected printer. Which device would the technician need?"""

ques2 = """
Which of the following modalities has the potential to be used effectively in every phase of the OPT model? Terra-Core Cable machines TRX Rip Trainer Suspended bodyweight training"""

ques3 = """
Movie Recommendation systems are an example of: 1. Classification 2. Clustering 3. Reinforcement Learning 4. Regression Options: B. A. 2 Only C. 1 and 2 D. 1 and 3 E. 2 and 3 F. 1, 2 and 3 H. 1, 2, 3 and 4
"""

ques4 = """
24. End-user data is . a. knowledge about the end users b. raw facts of interest to the end user c. information about a specific subject d. accurate, relevant and timely information
"""

ques5 = """
<div class="styled__KatexContent-sc-1k7k16x-5 cqEgSP">13. The compression ratio of a diesel engine is 20.0 to 1 ; that is, air in a cylinder is compressed to <span class="katex"><span class="katex-html"><span class="base"><span class="strut" style="height:1em;vertical-align:-0.25em;"></span><span class="mord">1/20.0</span></span></span></span> of its initial volume. (a) if the initial pressure is <span class="katex"><span class="katex-html"><span class="base"><span class="strut" style="height:0.7278em;vertical-align:-0.0833em;"></span><span class="mord">1.01</span><span class="mspace" style="margin-right:0.2222em;"></span><span class="mbin">×</span><span class="mspace" style="margin-right:0.2222em;"></span></span><span class="base"><span class="strut" style="height:0.8141em;"></span><span class="mord">1</span><span class="mord"><span class="mord">0</span><span class="msupsub"><span class="vlist-t"><span class="vlist-r"><span class="vlist" style="height:0.8141em;"><span style="top:-3.063em;margin-right:0.05em;"><span class="pstrut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mtight">5</span></span></span></span></span></span></span></span></span><span class="mord"><span class="mspace nobreak">&nbsp;</span><span class="mord mathrm">Pa</span></span></span></span></span> and the initial temperature is <span class="katex"><span class="katex-html"><span class="base"><span class="strut" style="height:0.6833em;"></span><span class="mord">2</span><span class="mord"><span class="mord">0</span><span class="msupsub"><span class="vlist-t"><span class="vlist-r"><span class="vlist" style="height:0.6741em;"><span style="top:-3.063em;margin-right:0.05em;"><span class="pstrut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mtight">∘</span></span></span></span></span></span></span></span></span><span class="mord mathrm">C</span></span></span></span>, find the final pressure and the temperature after adiabatic compression. (b) How much work does the gas do during the compression if the initial volume of the cylinder is <span class="katex"><span class="katex-html"><span class="base"><span class="strut" style="height:0.6833em;"></span><span class="mord">1.00</span><span class="mord"><span class="mspace nobreak">&nbsp;</span><span class="mord mathrm">L</span></span><span class="mspace" style="margin-right:0.2778em;"></span><span class="mrel">=</span><span class="mspace" style="margin-right:0.2778em;"></span></span><span class="base"><span class="strut" style="height:0.7278em;vertical-align:-0.0833em;"></span><span class="mord">1.00</span><span class="mspace" style="margin-right:0.2222em;"></span><span class="mbin">×</span><span class="mspace" style="margin-right:0.2222em;"></span></span><span class="base"><span class="strut" style="height:0.8141em;"></span><span class="mord">1</span><span class="mord"><span class="mord">0</span><span class="msupsub"><span class="vlist-t"><span class="vlist-r"><span class="vlist" style="height:0.8141em;"><span style="top:-3.063em;margin-right:0.05em;"><span class="pstrut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mtight">3</span></span></span></span></span></span></span></span></span><span class="mord">3</span><span class="mord"><span class="mord"><span class="mspace nobreak">&nbsp;</span><span class="mord mathrm">m</span></span><span class="msupsub"><span class="vlist-t"><span class="vlist-r"><span class="vlist" style="height:0.8141em;"><span style="top:-3.063em;margin-right:0.05em;"><span class="pstrut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mtight">3</span></span></span></span></span></span></span></span></span></span></span></span> ? Use the values <span class="katex"><span class="katex-html"><span class="base"><span class="strut" style="height:0.9694em;vertical-align:-0.2861em;"></span><span class="mord"><span class="mord mathrm">C</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist" style="height:0.1514em;"><span style="top:-2.55em;margin-left:0em;margin-right:0.05em;"><span class="pstrut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight" style="margin-right:0.05556em;">γ</span></span></span></span></span><span class="vlist-s">​</span></span><span class="vlist-r"><span class="vlist" style="height:0.2861em;"><span></span></span></span></span></span></span><span class="mspace" style="margin-right:0.2778em;"></span><span class="mrel">=</span><span class="mspace" style="margin-right:0.2778em;"></span></span><span class="base"><span class="strut" style="height:1em;vertical-align:-0.25em;"></span><span class="mord">20.8</span><span class="mord"><span class="mspace nobreak">&nbsp;</span><span class="mord mathrm">J</span></span><span class="mord">/</span><span class="mord"><span class="mord mathrm">mol</span></span><span class="mord mathrm">K</span></span></span></span> and <span class="katex"><span class="katex-html"><span class="base"><span class="strut" style="height:0.625em;vertical-align:-0.1944em;"></span><span class="mord mathnormal" style="margin-right:0.03588em;">y</span><span class="mspace" style="margin-right:0.2778em;"></span><span class="mrel">=</span><span class="mspace" style="margin-right:0.2778em;"></span></span><span class="base"><span class="strut" style="height:0.6444em;"></span><span class="mord">1.400</span></span></span></span> for air.</div>"""


def fix_question(content):
    t1 = time.time()
    # sd_prompt = QuestionIdentifierPromptExecutor()
    sd_prompt = LatexCodeGenExecutor()
    print("\n", "*" * 32, "Running LatexCodeGenExecutor", "*" * 32, "\n\n")
    res = asyncio.run(sd_prompt.run(content))
    print(res)
    # print(res.content.get("status"))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")


# fix_question(ques5)

def run_file():
    data_df = pd.read_csv(
        "/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/QuestionsData-Sheet3.csv",
    )
    smaple_data = data_df.reindex(columns=["Original Keyword"])
    print(smaple_data.shape)
    t1 = time.time()
    sd_prompt = QuestionIdentifierPromptExecutor()
    print("\n", "*" * 32, "Running QuestionIdentifierPromptExecutor", "*" * 32, "\n\n")
    res = asyncio.run(sd_prompt.run_list(smaple_data.to_dict("records")))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")
    final_df = pd.DataFrame(res)
    final_df.to_excel("final_response.xlsx")


# run_file()

# quest = "The compression ratio of a petrol engine is 20.0 to 1 ; that is, air in a cylinder is compressed adiabatically to \( \frac{1}{20.0} \) of its initial volume. (a) If the initial pressure is \( 1.01"
quest = """
For the circuit shown in the figure, determine the magnitude of
the currents 𝐼2 , 𝐼3 , and 𝐼4 passing through batteries 2, 3, and
4, respectively. In each case, determine whether the battery
"""

quest = """
 Find all real solutions or the equation 2s^(2)=5s+3
"""

quest = """
10. Consider a charge of \( +8.0 \mathrm{nC} \) is placed at \( x=-3.0 \mathrm{~m} \). A second charge of \( -24.0 \mathrm{nC} \) is placed at \( y=-6.0 \mathrm{~m} \), as shown to the right. What is
"""

quest = """
Question B2: Let \( s(x)=\sin \left(\frac{\pi}{180} x\right) \), defined on the domain \( [-100,400] \). (a) Use the chain rule to evaluate \( s^{\prime}(x) \) and \( s^{\prime \prime}(x) \). (b) Find
"""


def search_question():
    t1 = time.time()
    sd_prompt = QuestionExtractorExecutor()
    print("\n", "*" * 32, "Running QuestionExtractorExecutor", "*" * 32, "\n\n")
    res = asyncio.run(sd_prompt.run(quest))
    print(res)
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")

search_question()


def run_file_with_search():
    # data_df = pd.read_csv("/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/QuestionsData-Sheet3.csv")
    # data_df = pd.read_csv("/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/QuestionsData - Sheet4.csv")
    data_df = pd.read_csv("/Users/parvbhullar/Drives/Vault/Projects/Unpod/superpilot/superpilot/docs/Parvinder Testing - Test 25 Sep 2050.csv")
    smaple_data = data_df[:100].reindex(columns=["Original Keyword"])
    print(smaple_data.shape)
    t1 = time.time()
    sd_prompt = QuestionExtractorExecutor()
    print("\n", "*" * 32, "Running QuestionExtractorExecutor", "*" * 32, "\n\n")
    res = asyncio.run(sd_prompt.run_list(smaple_data.to_dict("records")))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")
    final_df = pd.DataFrame(res)
    final_df.to_excel("search_latex_response.xlsx")


# run_file_with_search()

def get_page_content(page: str):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page, "html.parser")
    ele = soup.find("div", {"id": "question-transcript"})
    if ele:
        # print("Found in question-transcript", ele)
        return ele
    print("Not Found in question-transcript")
    # desired_ids = ["question-transcript", "q-body"]
    # return soup.find_all("div", id=lambda x: x in desired_ids)
    desired_classes = ["styled__QuestionBody-sc-1f9k7g9-2", "question"]  # replace with your class names
    divs = soup.find_all("div", class_=lambda x: x in desired_classes)
    return "\n".join(i.text.strip() for i in divs)


async def try_browser_view():
    from superpilot.framework.tools.web_browser.web_browser_engine_type import WebBrowserEngineType
    from superpilot.framework.tools.web_browser import WebBrowserEngine
    from superpilot.examples.abilities.utlis.scraperapi import scrape_page
    # url = "https://www.chegg.com/homework-help/questions-and-answers/free-fall-acceleration-surface-moon-mass-moon-735-x-10-22-kg-radius-moon-1-737-km-q110726410"
    # url = "https://www.chegg.com/homework-help/questions-and-answers/homework-bernoulli-s-equation-unhealthy-valve-please-answer-following-question-s-1-blood-e-q110726353"
    # url = "https://www.chegg.com/homework-help/heart-defibrillator-used-patient-rc-time-constant-100-ms-due-chapter-21-problem-69pe-solution-9781938168000-exc"
    # url = "https://www.chegg.com/homework-help/questions-and-answers/2-figure-battery-potential-difference-v-100-mathrm-~v-five-capacitors-capacitance-200-mu-m-q110567592"
    url = "https://www.chegg.com/homework-help/questions-and-answers/5-temperature-170-moles-monoatomic-ideal-gas-ratio-gamma-1600-confined-cylinder-increased--q110725755"
    # url = "https://www.chegg.com/homework-help/questions-and-answers/10-consider-charge-80-mathrm-nc-placed-x-30-mathrm-~m--second-charge-240-mathrm-nc-placed--q110726408"
    # data = await WebBrowserEngine(parse_func=get_page_content).run(url)
    data = scrape_page(url, "e559ca66333058ac72328e90baed87c2")
    data = get_page_content(data)
    print(data)


# asyncio.run(try_browser_view())


def latex_txt():
    t1 = time.time()
    text = '$$\\text{The compression ratio of a diesel engine is 20.0 to 1 ; that is, air in a cylinder is compressed to }\\frac{1}{20.0}\\text{ of its initial volume. If the initial pressure is }1.01 \\text{ Pa and the initial temperature is }20°C, \\text{ find the final pressure and the temperature after adiabatic compression. How much work does the gas do during the compression if the initial volume of the cylinder is }1.00 \\text{ L? Use the values }γ = 20.8 \\text{ J/mol-K and }y = 1.400 \\text{ for air.}$$'
    print(latex_to_text(text))
    t2 = time.time()
    print("Time Taken", round(t2 - t1, 2), "seconds")

# latex_txt()

