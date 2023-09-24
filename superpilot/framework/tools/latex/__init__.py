from .pylatexenc.latex2text import LatexNodes2Text


def latex_to_text(latex):
    return LatexNodes2Text().latex_to_text(latex)
