from .pylatexenc.latex2text import LatexNodes2Text


def latex_to_text(latex):
    if latex is None:
        return latex
    return LatexNodes2Text().latex_to_text(latex)
