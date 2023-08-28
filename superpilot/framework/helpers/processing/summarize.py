
from summarizer.sbert import SBertSummarizer
summarize_model = SBertSummarizer("paraphrase-MiniLM-L6-v2")
from summarizer import Summarizer


def summarize_text(text):
    result = summarize_model(text, min_length=500)
    full_text = "".join(result)
    return full_text

def fulltext(text):
    model = Summarizer()
    result = model(text, min_length=600)
    full_text = ''.join(result)
    return full_text