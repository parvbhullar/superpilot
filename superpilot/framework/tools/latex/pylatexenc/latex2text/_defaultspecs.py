# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2019 Philippe Faist
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


from __future__ import print_function, unicode_literals  # , absolute_import

# Internal module. May change without notice.

import unicodedata
import datetime
import sys

if sys.version_info.major >= 3:

    def unicode(string):
        return string

    basestring = str
else:
    pass


from ..latex2text import (
    MacroTextSpec,
    EnvironmentTextSpec,
    SpecialsTextSpec,
    fmt_equation_environment,  # fmt_placeholder_node,
    placeholder_node_formatter,
    fmt_matrix_environment_node,
    fmt_input_macro,
    fmt_math_text_style,
)


def _format_uebung(n, l2tobj):
    s = "\n" + l2tobj.nodelist_to_text([n.nodeargs[0]]) + "\n"
    optarg = n.nodeargs[1]
    if optarg is not None:
        s += "[{}]\n".format(l2tobj.nodelist_to_text([optarg]))
    return s


def _format_maketitle(title, author, date):
    s = title + "\n"
    s += "    " + author + "\n"
    s += "    " + date + "\n"
    s += "=" * max(len(title), 4 + len(author), 4 + len(date)) + "\n\n"
    return s


def _latex_today():
    return "{dt:%B} {dt.day}, {dt.year}".format(dt=datetime.datetime.now())


def _mathxx_formatter(style):
    def formatter(node, l2tobj, style=style):
        arg_text = l2tobj.node_arg_to_text(node, 0)
        return fmt_math_text_style(arg_text, style)

    return formatter


# construct the specs structure, more than the just the following definition


# ==============================================================================


_latex_specs_placeholders = {
    "environments": [
        #  --- as of pylatexenc 2.8, these are now approximated ---
        #        EnvironmentTextSpec('array', simplify_repl=fmt_placeholder_node),
        #        EnvironmentTextSpec('pmatrix', simplify_repl=fmt_placeholder_node),
        #        EnvironmentTextSpec('bmatrix', simplify_repl=fmt_placeholder_node),
        #        EnvironmentTextSpec('smallmatrix', simplify_repl=fmt_placeholder_node),
        #        EnvironmentTextSpec('psmallmatrix', simplify_repl=fmt_placeholder_node),
        #        EnvironmentTextSpec('bsmallmatrix', simplify_repl=fmt_placeholder_node),
    ],
    "specials": [],
    "macros": []
    + [
        MacroTextSpec(x, simplify_repl=y)
        for x, y in (
            ("includegraphics", placeholder_node_formatter("graphics")),
            ("ref", "<ref>"),
            ("autoref", "<ref>"),
            ("cref", "<ref>"),
            ("Cref", "<Ref>"),
            ("eqref", "(<ref>)"),
            ("cite", "<cit.>"),
            ("citet", "<cit.>"),
            ("citep", "<cit.>"),
        )
    ],
}

_latex_specs_approximations = {
    "environments": [
        EnvironmentTextSpec("center", simplify_repl="\n%s\n"),
        EnvironmentTextSpec("flushleft", simplify_repl="\n%s\n"),
        EnvironmentTextSpec("flushright", simplify_repl="\n%s\n"),
        EnvironmentTextSpec("exenumerate", discard=False),
        EnvironmentTextSpec("enumerate", discard=False),
        EnvironmentTextSpec("list", discard=False),
        EnvironmentTextSpec("itemize", discard=False),
        EnvironmentTextSpec("subequations", discard=False),
        EnvironmentTextSpec("figure", discard=False),
        EnvironmentTextSpec("table", discard=False),
        EnvironmentTextSpec("array", simplify_repl=fmt_matrix_environment_node),
        EnvironmentTextSpec("pmatrix", simplify_repl=fmt_matrix_environment_node),
        EnvironmentTextSpec("bmatrix", simplify_repl=fmt_matrix_environment_node),
        EnvironmentTextSpec("smallmatrix", simplify_repl=fmt_matrix_environment_node),
        EnvironmentTextSpec("psmallmatrix", simplify_repl=fmt_matrix_environment_node),
        EnvironmentTextSpec("bsmallmatrix", simplify_repl=fmt_matrix_environment_node),
        #
        # math environments used to be categorized as 'placeholders' in
        # pylatexenc <= 2.9, but I think it's more accurate to have them in
        # 'approximations'.
        #
        EnvironmentTextSpec("equation", simplify_repl=fmt_equation_environment),
        # note {equation*} is actually defined by amsmath
        EnvironmentTextSpec("equation*", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("eqnarray", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("eqnarray*", simplify_repl=fmt_equation_environment),
        #
        EnvironmentTextSpec("align", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("multline", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("gather", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("align*", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("multline*", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("gather*", simplify_repl=fmt_equation_environment),
        #
        # breqn math
        EnvironmentTextSpec("dmath", simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec("dmath*", simplify_repl=fmt_equation_environment),
    ],
    "specials": [
        SpecialsTextSpec(
            "&", "   "
        ),  # ignore tabular alignments, just add a little space
    ],
    "macros": [
        # NOTE: macro will only be assigned arguments if they are explicitly
        #       defined as accepting arguments in the `LatexWalker` (see
        #       `macrospec` module).
        MacroTextSpec("emph", discard=False),
        MacroTextSpec("textrm", discard=False),
        MacroTextSpec("textit", discard=False),
        MacroTextSpec("textbf", discard=False),
        MacroTextSpec("textsc", discard=False),
        MacroTextSpec("textsl", discard=False),
        MacroTextSpec("text", discard=False),
    ]
    + [
        MacroTextSpec(x, simplify_repl=y)
        for x, y in (
            (
                "title",
                lambda n, l2tobj: setattr(
                    l2tobj,
                    "_doc_title",
                    l2tobj.nodelist_to_text(n.nodeargd.argnlist[0:1]),
                ),
            ),
            (
                "author",
                lambda n, l2tobj: setattr(
                    l2tobj,
                    "_doc_author",
                    l2tobj.nodelist_to_text(n.nodeargd.argnlist[0:1]),
                ),
            ),
            (
                "date",
                lambda n, l2tobj: setattr(
                    l2tobj,
                    "_doc_date",
                    l2tobj.nodelist_to_text(n.nodeargd.argnlist[0:1]),
                ),
            ),
            (
                "maketitle",
                lambda n, l2tobj: _format_maketitle(
                    getattr(l2tobj, "_doc_title", r"[NO \title GIVEN]"),
                    getattr(l2tobj, "_doc_author", r"[NO \author GIVEN]"),
                    getattr(l2tobj, "_doc_date", _latex_today()),
                ),
            ),
            ("url", "<%s>"),
            (
                "item",
                lambda r, l2tobj: "\n  "
                + (l2tobj.nodelist_to_text([r.nodeoptarg]) if r.nodeoptarg else "* "),
            ),
            ("footnote", "[%(2)s]"),  # \footnote[optional mark]{footnote text}
            (
                "href",
                lambda n, l2tobj: "{} <{}>".format(
                    l2tobj.nodelist_to_text([n.nodeargd.argnlist[1]]),
                    l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]),
                ),
            ),
            (
                "part",
                lambda n, l2tobj: "\n\nPART: {}\n".format(
                    l2tobj.node_arg_to_text(n, 2).upper()
                ),
            ),
            (
                "chapter",
                lambda n, l2tobj: "\n\nCHAPTER: {}\n".format(
                    l2tobj.node_arg_to_text(n, 2).upper()
                ),
            ),
            (
                "section",
                lambda n, l2tobj: "\n\n\N{SECTION SIGN} {}\n".format(
                    l2tobj.node_arg_to_text(n, 2).upper()
                ),
            ),
            (
                "subsection",
                lambda n, l2tobj: "\n\n \N{SECTION SIGN}.\N{SECTION SIGN} {}\n".format(
                    l2tobj.node_arg_to_text(n, 2)
                ),
            ),
            (
                "subsubsection",
                lambda n, l2tobj: "\n\n  \N{SECTION SIGN}.\N{SECTION SIGN}.\N{SECTION SIGN} {}\n".format(
                    l2tobj.node_arg_to_text(n, 2)
                ),
            ),
            (
                "paragraph",
                lambda n, l2tobj: "\n\n  {}\n".format(l2tobj.node_arg_to_text(n, 2)),
            ),
            (
                "subparagraph",
                lambda n, l2tobj: "\n\n    {}\n".format(l2tobj.node_arg_to_text(n, 2)),
            ),
            ("textcolor", "%(3)s"),
            ("colorbox", "%(3)s"),
            ("fcolorbox", "%(5)s"),
            ("hspace", ""),
            ("vspace", "\n"),
            # \\ is treated as an "approximation" because a good text renderer would
            # have to actually note that this is a end-of-line marker which is not
            # to be confused with other newlines in the paragraph (which can be
            # reflowed)
            ("\\", "\n"),
            ("frac", "%s/%s"),
            ("nicefrac", "%s/%s"),
            ("textfrac", "%s/%s"),
            ("overline", "%s"),
            ("underline", "%s"),
            ("widehat", "%s"),
            ("widetilde", "%s"),
            ("wideparen", "%s"),
            ("overleftarrow", "%s"),
            ("overrightarrow", "%s"),
            ("overleftrightarrow", "%s"),
            ("underleftarrow", "%s"),
            ("underrightarrow", "%s"),
            ("underleftrightarrow", "%s"),
            ("overbrace", "%s"),
            ("underbrace", "%s"),
            ("overgroup", "%s"),
            ("undergroup", "%s"),
            ("overbracket", "%s"),
            ("underbracket", "%s"),
            ("overlinesegment", "%s"),
            ("underlinesegment", "%s"),
            ("overleftharpoon", "%s"),
            ("overrightharpoon", "%s"),
        )
    ],
}

_latex_specs_base = {
    "environments": [],
    "specials": [],
    "macros": [
        MacroTextSpec("mathrm", discard=False),
        MacroTextSpec("mathbf", simplify_repl=_mathxx_formatter("bold")),
        MacroTextSpec("mathit", simplify_repl=_mathxx_formatter("italic")),
        MacroTextSpec("mathsf", simplify_repl=_mathxx_formatter("sans")),
        MacroTextSpec("mathbb", simplify_repl=_mathxx_formatter("doublestruck")),
        MacroTextSpec("mathtt", simplify_repl=_mathxx_formatter("monospace")),
        MacroTextSpec("mathcal", simplify_repl=_mathxx_formatter("script")),
        MacroTextSpec("mathscr", simplify_repl=_mathxx_formatter("script")),
        MacroTextSpec("mathfrak", simplify_repl=_mathxx_formatter("fraktur")),
        MacroTextSpec("input", simplify_repl=fmt_input_macro),
        MacroTextSpec("include", simplify_repl=fmt_input_macro),
    ]
    + [
        MacroTextSpec(x, simplify_repl=y)
        for x, y in (
            ("today", _latex_today()),
            # use second argument:
            (
                "texorpdfstring",
                lambda node, l2tobj: l2tobj.nodelist_to_text(node.nodeargs[1:2]),
            ),
            ("oe", "\u0153"),
            ("OE", "\u0152"),
            ("ae", "\u00e6"),
            ("AE", "\u00c6"),
            ("aa", "\u00e5"),  # a norvegien/nordique
            ("AA", "\u00c5"),  # A norvegien/nordique
            ("o", "\u00f8"),  # o norvegien/nordique
            ("O", "\u00d8"),  # O norvegien/nordique
            ("ss", "\u00df"),  # s-z allemand
            ("L", "\N{LATIN CAPITAL LETTER L WITH STROKE}"),
            ("l", "\N{LATIN SMALL LETTER L WITH STROKE}"),
            ("i", "\N{LATIN SMALL LETTER DOTLESS I}"),
            ("j", "\N{LATIN SMALL LETTER DOTLESS J}"),
            ("~", "~"),
            ("&", "&"),
            ("$", "$"),
            ("{", "{"),
            ("}", "}"),
            ("%", lambda arg: "%"),  # careful: % is formatting substitution symbol...
            ("#", "#"),
            ("_", "_"),
            ("textquoteleft", "\N{LEFT SINGLE QUOTATION MARK}"),
            ("textquoteright", "\N{RIGHT SINGLE QUOTATION MARK}"),
            ("textquotedblright", "\N{RIGHT DOUBLE QUOTATION MARK}"),
            ("textquotedblleft", "\N{LEFT DOUBLE QUOTATION MARK}"),
            ("textendash", "\N{EN DASH}"),
            ("textemdash", "\N{EM DASH}"),
            ("textpm", "\N{PLUS-MINUS SIGN}"),
            ("textmp", "\N{MINUS-OR-PLUS SIGN}"),
            ("texteuro", "\N{EURO SIGN}"),
            ("backslash", "\\"),
            ("textbackslash", "\\"),
            # math stuff
            ("ensuremath", "%s"),
            ("hbar", "\N{LATIN SMALL LETTER H WITH STROKE}"),
            ("ell", "\N{SCRIPT SMALL L}"),
            ("forall", "\N{FOR ALL}"),
            ("complement", "\N{COMPLEMENT}"),
            ("partial", "\N{PARTIAL DIFFERENTIAL}"),
            ("exists", "\N{THERE EXISTS}"),
            ("nexists", "\N{THERE DOES NOT EXIST}"),
            ("varnothing", "\N{EMPTY SET}"),
            ("emptyset", "\N{EMPTY SET}"),
            ("aleph", "\N{ALEF SYMBOL}"),
            # increment?
            ("nabla", "\N{NABLA}"),
            #
            ("in", "\N{ELEMENT OF}"),
            ("notin", "\N{NOT AN ELEMENT OF}"),
            ("ni", "\N{CONTAINS AS MEMBER}"),
            ("prod", "\N{N-ARY PRODUCT}"),
            ("coprod", "\N{N-ARY COPRODUCT}"),
            ("sum", "\N{N-ARY SUMMATION}"),
            ("setminus", "\N{SET MINUS}"),
            ("smallsetminus", "\N{SET MINUS}"),
            ("ast", "\N{ASTERISK OPERATOR}"),
            ("circ", "\N{RING OPERATOR}"),
            ("bullet", "\N{BULLET OPERATOR}"),
            ("sqrt", "\N{SQUARE ROOT}(%(2)s)"),
            ("propto", "\N{PROPORTIONAL TO}"),
            ("infty", "\N{INFINITY}"),
            ("parallel", "\N{PARALLEL TO}"),
            ("nparallel", "\N{NOT PARALLEL TO}"),
            ("wedge", "\N{LOGICAL AND}"),
            ("vee", "\N{LOGICAL OR}"),
            ("cap", "\N{INTERSECTION}"),
            ("cup", "\N{UNION}"),
            ("int", "\N{INTEGRAL}"),
            ("iint", "\N{DOUBLE INTEGRAL}"),
            ("iiint", "\N{TRIPLE INTEGRAL}"),
            ("oint", "\N{CONTOUR INTEGRAL}"),
            ("sim", "\N{TILDE OPERATOR}"),
            ("backsim", "\N{REVERSED TILDE}"),
            ("simeq", "\N{ASYMPTOTICALLY EQUAL TO}"),
            ("approx", "\N{ALMOST EQUAL TO}"),
            ("neq", "\N{NOT EQUAL TO}"),
            ("equiv", "\N{IDENTICAL TO}"),
            ("le", "\N{LESS-THAN OR EQUAL TO}"),
            ("ge", "\N{GREATER-THAN OR EQUAL TO}"),
            ("leq", "\N{LESS-THAN OR EQUAL TO}"),
            ("geq", "\N{GREATER-THAN OR EQUAL TO}"),
            ("leqslant", "\N{LESS-THAN OR SLANTED EQUAL TO}"),
            ("geqslant", "\N{GREATER-THAN OR SLANTED EQUAL TO}"),
            ("leqq", "\N{LESS-THAN OVER EQUAL TO}"),
            ("geqq", "\N{GREATER-THAN OVER EQUAL TO}"),
            ("lneqq", "\N{LESS-THAN BUT NOT EQUAL TO}"),
            ("gneqq", "\N{GREATER-THAN BUT NOT EQUAL TO}"),
            ("ll", "\N{MUCH LESS-THAN}"),
            ("gg", "\N{MUCH GREATER-THAN}"),
            ("nless", "\N{NOT LESS-THAN}"),
            ("ngtr", "\N{NOT GREATER-THAN}"),
            ("nleq", "\N{NEITHER LESS-THAN NOR EQUAL TO}"),
            ("ngeq", "\N{NEITHER GREATER-THAN NOR EQUAL TO}"),
            ("lesssim", "\N{LESS-THAN OR EQUIVALENT TO}"),
            ("gtrsim", "\N{GREATER-THAN OR EQUIVALENT TO}"),
            ("lessgtr", "\N{LESS-THAN OR GREATER-THAN}"),
            ("gtrless", "\N{GREATER-THAN OR LESS-THAN}"),
            ("prec", "\N{PRECEDES}"),
            ("succ", "\N{SUCCEEDS}"),
            ("preceq", "\N{PRECEDES OR EQUAL TO}"),
            ("succeq", "\N{SUCCEEDS OR EQUAL TO}"),
            ("precsim", "\N{PRECEDES OR EQUIVALENT TO}"),
            ("succsim", "\N{SUCCEEDS OR EQUIVALENT TO}"),
            ("nprec", "\N{DOES NOT PRECEDE}"),
            ("nsucc", "\N{DOES NOT SUCCEED}"),
            ("subset", "\N{SUBSET OF}"),
            ("supset", "\N{SUPERSET OF}"),
            ("subseteq", "\N{SUBSET OF OR EQUAL TO}"),
            ("supseteq", "\N{SUPERSET OF OR EQUAL TO}"),
            ("nsubseteq", "\N{NEITHER A SUBSET OF NOR EQUAL TO}"),
            ("nsupseteq", "\N{NEITHER A SUPERSET OF NOR EQUAL TO}"),
            ("subsetneq", "\N{SUBSET OF WITH NOT EQUAL TO}"),
            ("supsetneq", "\N{SUPERSET OF WITH NOT EQUAL TO}"),
            ("cdot", "\N{MIDDLE DOT}"),
            ("times", "\N{MULTIPLICATION SIGN}"),
            ("otimes", "\N{CIRCLED TIMES}"),
            ("oplus", "\N{CIRCLED PLUS}"),
            ("bigotimes", "\N{CIRCLED TIMES}"),
            ("bigoplus", "\N{CIRCLED PLUS}"),
            ("cos", "cos"),
            ("sin", "sin"),
            ("tan", "tan"),
            ("arccos", "arccos"),
            ("arcsin", "arcsin"),
            ("arctan", "arctan"),
            ("cosh", "cosh"),
            ("sinh", "sinh"),
            ("tanh", "tanh"),
            ("arccosh", "arccosh"),
            ("arcsinh", "arcsinh"),
            ("arctanh", "arctanh"),
            ("ln", "ln"),
            ("log", "log"),
            ("exp", "exp"),
            ("max", "max"),
            ("min", "min"),
            ("sup", "sup"),
            ("inf", "inf"),
            ("lim", "lim"),
            ("limsup", "lim sup"),
            ("liminf", "lim inf"),
            ("prime", "'"),
            ("dag", "\N{DAGGER}"),
            ("dagger", "\N{DAGGER}"),
            ("pm", "\N{PLUS-MINUS SIGN}"),
            ("mp", "\N{MINUS-OR-PLUS SIGN}"),
            (",", " "),
            (";", " "),
            (":", " "),
            (" ", " "),
            ("!", ""),  # sorry, no negative space in ascii
            ("quad", "  "),
            ("qquad", "    "),
            ("ldots", "\N{HORIZONTAL ELLIPSIS}"),
            ("cdots", "\N{MIDLINE HORIZONTAL ELLIPSIS}"),
            ("ddots", "\N{DOWN RIGHT DIAGONAL ELLIPSIS}"),
            ("iddots", "\N{UP RIGHT DIAGONAL ELLIPSIS}"),
            ("vdots", "\N{VERTICAL ELLIPSIS}"),
            ("dots", "\N{HORIZONTAL ELLIPSIS}"),
            ("dotsc", "\N{HORIZONTAL ELLIPSIS}"),
            ("dotsb", "\N{HORIZONTAL ELLIPSIS}"),
            ("dotsm", "\N{HORIZONTAL ELLIPSIS}"),
            ("dotsi", "\N{HORIZONTAL ELLIPSIS}"),
            ("dotso", "\N{HORIZONTAL ELLIPSIS}"),
            ("langle", "\N{MATHEMATICAL LEFT ANGLE BRACKET}"),
            ("rangle", "\N{MATHEMATICAL RIGHT ANGLE BRACKET}"),
            ("lvert", "|"),
            ("rvert", "|"),
            ("vert", "|"),
            ("lVert", "\N{DOUBLE VERTICAL LINE}"),
            ("rVert", "\N{DOUBLE VERTICAL LINE}"),
            ("Vert", "\N{DOUBLE VERTICAL LINE}"),
            ("mid", "|"),
            ("nmid", "\N{DOES NOT DIVIDE}"),
            ("ket", "|%s\N{MATHEMATICAL RIGHT ANGLE BRACKET}"),
            ("bra", "\N{MATHEMATICAL LEFT ANGLE BRACKET}%s|"),
            (
                "braket",
                "\N{MATHEMATICAL LEFT ANGLE BRACKET}%s|%s\N{MATHEMATICAL RIGHT ANGLE BRACKET}",
            ),
            (
                "ketbra",
                "|%s\N{MATHEMATICAL RIGHT ANGLE BRACKET}\N{MATHEMATICAL LEFT ANGLE BRACKET}%s|",
            ),
            ("uparrow", "\N{UPWARDS ARROW}"),
            ("downarrow", "\N{DOWNWARDS ARROW}"),
            ("rightarrow", "\N{RIGHTWARDS ARROW}"),
            ("to", "\N{RIGHTWARDS ARROW}"),
            ("leftarrow", "\N{LEFTWARDS ARROW}"),
            ("longrightarrow", "\N{LONG RIGHTWARDS ARROW}"),
            ("longleftarrow", "\N{LONG LEFTWARDS ARROW}"),
        )
    ],
}


# ==============================================================================

advanced_symbols_macros = [
    # Rules from latexencode defaults 'defaults'
    MacroTextSpec("textasciicircum", "\N{CIRCUMFLEX ACCENT}"),  # ‘^’
    MacroTextSpec("textasciitilde", "\N{TILDE}"),  # ‘~’
    MacroTextSpec("textexclamdown", "\N{INVERTED EXCLAMATION MARK}"),  # ‘¡’
    MacroTextSpec("textcent", "\N{CENT SIGN}"),  # ‘¢’
    MacroTextSpec("textsterling", "\N{POUND SIGN}"),  # ‘£’
    MacroTextSpec("textcurrency", "\N{CURRENCY SIGN}"),  # ‘¤’
    MacroTextSpec("textyen", "\N{YEN SIGN}"),  # ‘¥’
    MacroTextSpec("textbrokenbar", "\N{BROKEN BAR}"),  # ‘¦’
    MacroTextSpec("textsection", "\N{SECTION SIGN}"),  # ‘§’
    MacroTextSpec("textasciidieresis", "\N{DIAERESIS}"),  # ‘¨’
    MacroTextSpec("textcopyright", "\N{COPYRIGHT SIGN}"),  # ‘©’
    MacroTextSpec("textordfeminine", "\N{FEMININE ORDINAL INDICATOR}"),  # ‘ª’
    MacroTextSpec(
        "guillemotleft", "\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}"
    ),  # ‘«’
    MacroTextSpec("textlnot", "\N{NOT SIGN}"),  # ‘¬’
    MacroTextSpec("-", "\N{SOFT HYPHEN}"),  # ‘­’
    MacroTextSpec("textregistered", "\N{REGISTERED SIGN}"),  # ‘®’
    MacroTextSpec("textasciimacron", "\N{MACRON}"),  # ‘¯’
    MacroTextSpec("textdegree", "\N{DEGREE SIGN}"),  # ‘°’
    MacroTextSpec("texttwosuperior", "\N{SUPERSCRIPT TWO}"),  # ‘²’
    MacroTextSpec("textthreesuperior", "\N{SUPERSCRIPT THREE}"),  # ‘³’
    MacroTextSpec("textasciiacute", "\N{ACUTE ACCENT}"),  # ‘´’
    MacroTextSpec("textmu", "\N{MICRO SIGN}"),  # ‘µ’
    MacroTextSpec("textparagraph", "\N{PILCROW SIGN}"),  # ‘¶’
    MacroTextSpec("textperiodcentered", "\N{MIDDLE DOT}"),  # ‘·’
    MacroTextSpec("textonesuperior", "\N{SUPERSCRIPT ONE}"),  # ‘¹’
    MacroTextSpec("textordmasculine", "\N{MASCULINE ORDINAL INDICATOR}"),  # ‘º’
    MacroTextSpec(
        "guillemotright", "\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}"
    ),  # ‘»’
    MacroTextSpec("textonequarter", "\N{VULGAR FRACTION ONE QUARTER}"),  # ‘¼’
    MacroTextSpec("textonehalf", "\N{VULGAR FRACTION ONE HALF}"),  # ‘½’
    MacroTextSpec("textthreequarters", "\N{VULGAR FRACTION THREE QUARTERS}"),  # ‘¾’
    MacroTextSpec("textquestiondown", "\N{INVERTED QUESTION MARK}"),  # ‘¿’
    MacroTextSpec("DH", "\N{LATIN CAPITAL LETTER ETH}"),  # ‘Ð’
    MacroTextSpec("texttimes", "\N{MULTIPLICATION SIGN}"),  # ‘×’
    MacroTextSpec("TH", "\N{LATIN CAPITAL LETTER THORN}"),  # ‘Þ’
    MacroTextSpec("dh", "\N{LATIN SMALL LETTER ETH}"),  # ‘ð’
    MacroTextSpec("textdiv", "\N{DIVISION SIGN}"),  # ‘÷’
    MacroTextSpec("th", "\N{LATIN SMALL LETTER THORN}"),  # ‘þ’
    MacroTextSpec("DJ", "\N{LATIN CAPITAL LETTER D WITH STROKE}"),  # ‘Đ’
    MacroTextSpec("dj", "\N{LATIN SMALL LETTER D WITH STROKE}"),  # ‘đ’
    MacroTextSpec("IJ", "\N{LATIN CAPITAL LIGATURE IJ}"),  # ‘Ĳ’
    MacroTextSpec("ij", "\N{LATIN SMALL LIGATURE IJ}"),  # ‘ĳ’
    MacroTextSpec("NG", "\N{LATIN CAPITAL LETTER ENG}"),  # ‘Ŋ’
    MacroTextSpec("ng", "\N{LATIN SMALL LETTER ENG}"),  # ‘ŋ’
    MacroTextSpec("textflorin", "\N{LATIN SMALL LETTER F WITH HOOK}"),  # ‘ƒ’
    MacroTextSpec("texthvlig", "\N{LATIN SMALL LETTER HV}"),  # ‘ƕ’
    MacroTextSpec("textnrleg", "\N{LATIN SMALL LETTER N WITH LONG RIGHT LEG}"),  # ‘ƞ’
    MacroTextSpec("textschwa", "\N{LATIN SMALL LETTER SCHWA}"),  # ‘ə’
    MacroTextSpec("textphi", "\N{LATIN SMALL LETTER PHI}"),  # ‘ɸ’
    MacroTextSpec("textglotstop", "\N{LATIN LETTER GLOTTAL STOP}"),  # ‘ʔ’
    MacroTextSpec("textturnk", "\N{LATIN SMALL LETTER TURNED K}"),  # ‘ʞ’
    MacroTextSpec("textasciicircum", "\N{MODIFIER LETTER CIRCUMFLEX ACCENT}"),  # ‘ˆ’
    MacroTextSpec("textasciicaron", "\N{CARON}"),  # ‘ˇ’
    MacroTextSpec("textasciibreve", "\N{BREVE}"),  # ‘˘’
    MacroTextSpec("textperiodcentered", "\N{DOT ABOVE}"),  # ‘˙’
    MacroTextSpec("textasciitilde", "\N{SMALL TILDE}"),  # ‘˜’
    MacroTextSpec("textacutedbl", "\N{DOUBLE ACUTE ACCENT}"),  # ‘˝’
    MacroTextSpec("varkappa", "\N{GREEK KAPPA SYMBOL}"),  # ‘ϰ’
    MacroTextSpec("backepsilon", "\N{GREEK REVERSED LUNATE EPSILON SYMBOL}"),  # ‘϶’
    MacroTextSpec("CYRYO", "\N{CYRILLIC CAPITAL LETTER IO}"),  # ‘Ё’
    MacroTextSpec("CYRDJE", "\N{CYRILLIC CAPITAL LETTER DJE}"),  # ‘Ђ’
    MacroTextSpec("CYRIE", "\N{CYRILLIC CAPITAL LETTER UKRAINIAN IE}"),  # ‘Є’
    MacroTextSpec("CYRDZE", "\N{CYRILLIC CAPITAL LETTER DZE}"),  # ‘Ѕ’
    MacroTextSpec(
        "CYRII", "\N{CYRILLIC CAPITAL LETTER BYELORUSSIAN-UKRAINIAN I}"
    ),  # ‘І’
    MacroTextSpec("CYRYI", "\N{CYRILLIC CAPITAL LETTER YI}"),  # ‘Ї’
    MacroTextSpec("CYRJE", "\N{CYRILLIC CAPITAL LETTER JE}"),  # ‘Ј’
    MacroTextSpec("CYRLJE", "\N{CYRILLIC CAPITAL LETTER LJE}"),  # ‘Љ’
    MacroTextSpec("CYRNJE", "\N{CYRILLIC CAPITAL LETTER NJE}"),  # ‘Њ’
    MacroTextSpec("CYRTSHE", "\N{CYRILLIC CAPITAL LETTER TSHE}"),  # ‘Ћ’
    MacroTextSpec("CYRUSHRT", "\N{CYRILLIC CAPITAL LETTER SHORT U}"),  # ‘Ў’
    MacroTextSpec("CYRDZHE", "\N{CYRILLIC CAPITAL LETTER DZHE}"),  # ‘Џ’
    MacroTextSpec("CYRA", "\N{CYRILLIC CAPITAL LETTER A}"),  # ‘А’
    MacroTextSpec("CYRB", "\N{CYRILLIC CAPITAL LETTER BE}"),  # ‘Б’
    MacroTextSpec("CYRV", "\N{CYRILLIC CAPITAL LETTER VE}"),  # ‘В’
    MacroTextSpec("CYRG", "\N{CYRILLIC CAPITAL LETTER GHE}"),  # ‘Г’
    MacroTextSpec("CYRD", "\N{CYRILLIC CAPITAL LETTER DE}"),  # ‘Д’
    MacroTextSpec("CYRE", "\N{CYRILLIC CAPITAL LETTER IE}"),  # ‘Е’
    MacroTextSpec("CYRZH", "\N{CYRILLIC CAPITAL LETTER ZHE}"),  # ‘Ж’
    MacroTextSpec("CYRZ", "\N{CYRILLIC CAPITAL LETTER ZE}"),  # ‘З’
    MacroTextSpec("CYRI", "\N{CYRILLIC CAPITAL LETTER I}"),  # ‘И’
    MacroTextSpec("CYRISHRT", "\N{CYRILLIC CAPITAL LETTER SHORT I}"),  # ‘Й’
    MacroTextSpec("CYRK", "\N{CYRILLIC CAPITAL LETTER KA}"),  # ‘К’
    MacroTextSpec("CYRL", "\N{CYRILLIC CAPITAL LETTER EL}"),  # ‘Л’
    MacroTextSpec("CYRM", "\N{CYRILLIC CAPITAL LETTER EM}"),  # ‘М’
    MacroTextSpec("CYRN", "\N{CYRILLIC CAPITAL LETTER EN}"),  # ‘Н’
    MacroTextSpec("CYRO", "\N{CYRILLIC CAPITAL LETTER O}"),  # ‘О’
    MacroTextSpec("CYRP", "\N{CYRILLIC CAPITAL LETTER PE}"),  # ‘П’
    MacroTextSpec("CYRR", "\N{CYRILLIC CAPITAL LETTER ER}"),  # ‘Р’
    MacroTextSpec("CYRS", "\N{CYRILLIC CAPITAL LETTER ES}"),  # ‘С’
    MacroTextSpec("CYRT", "\N{CYRILLIC CAPITAL LETTER TE}"),  # ‘Т’
    MacroTextSpec("CYRU", "\N{CYRILLIC CAPITAL LETTER U}"),  # ‘У’
    MacroTextSpec("CYRF", "\N{CYRILLIC CAPITAL LETTER EF}"),  # ‘Ф’
    MacroTextSpec("CYRH", "\N{CYRILLIC CAPITAL LETTER HA}"),  # ‘Х’
    MacroTextSpec("CYRC", "\N{CYRILLIC CAPITAL LETTER TSE}"),  # ‘Ц’
    MacroTextSpec("CYRCH", "\N{CYRILLIC CAPITAL LETTER CHE}"),  # ‘Ч’
    MacroTextSpec("CYRSH", "\N{CYRILLIC CAPITAL LETTER SHA}"),  # ‘Ш’
    MacroTextSpec("CYRSHCH", "\N{CYRILLIC CAPITAL LETTER SHCHA}"),  # ‘Щ’
    MacroTextSpec("CYRHRDSN", "\N{CYRILLIC CAPITAL LETTER HARD SIGN}"),  # ‘Ъ’
    MacroTextSpec("CYRERY", "\N{CYRILLIC CAPITAL LETTER YERU}"),  # ‘Ы’
    MacroTextSpec("CYRSFTSN", "\N{CYRILLIC CAPITAL LETTER SOFT SIGN}"),  # ‘Ь’
    MacroTextSpec("CYREREV", "\N{CYRILLIC CAPITAL LETTER E}"),  # ‘Э’
    MacroTextSpec("CYRYU", "\N{CYRILLIC CAPITAL LETTER YU}"),  # ‘Ю’
    MacroTextSpec("CYRYA", "\N{CYRILLIC CAPITAL LETTER YA}"),  # ‘Я’
    MacroTextSpec("cyra", "\N{CYRILLIC SMALL LETTER A}"),  # ‘а’
    MacroTextSpec("cyrb", "\N{CYRILLIC SMALL LETTER BE}"),  # ‘б’
    MacroTextSpec("cyrv", "\N{CYRILLIC SMALL LETTER VE}"),  # ‘в’
    MacroTextSpec("cyrg", "\N{CYRILLIC SMALL LETTER GHE}"),  # ‘г’
    MacroTextSpec("cyrd", "\N{CYRILLIC SMALL LETTER DE}"),  # ‘д’
    MacroTextSpec("cyre", "\N{CYRILLIC SMALL LETTER IE}"),  # ‘е’
    MacroTextSpec("cyrzh", "\N{CYRILLIC SMALL LETTER ZHE}"),  # ‘ж’
    MacroTextSpec("cyrz", "\N{CYRILLIC SMALL LETTER ZE}"),  # ‘з’
    MacroTextSpec("cyri", "\N{CYRILLIC SMALL LETTER I}"),  # ‘и’
    MacroTextSpec("cyrishrt", "\N{CYRILLIC SMALL LETTER SHORT I}"),  # ‘й’
    MacroTextSpec("cyrk", "\N{CYRILLIC SMALL LETTER KA}"),  # ‘к’
    MacroTextSpec("cyrl", "\N{CYRILLIC SMALL LETTER EL}"),  # ‘л’
    MacroTextSpec("cyrm", "\N{CYRILLIC SMALL LETTER EM}"),  # ‘м’
    MacroTextSpec("cyrn", "\N{CYRILLIC SMALL LETTER EN}"),  # ‘н’
    MacroTextSpec("cyro", "\N{CYRILLIC SMALL LETTER O}"),  # ‘о’
    MacroTextSpec("cyrp", "\N{CYRILLIC SMALL LETTER PE}"),  # ‘п’
    MacroTextSpec("cyrr", "\N{CYRILLIC SMALL LETTER ER}"),  # ‘р’
    MacroTextSpec("cyrs", "\N{CYRILLIC SMALL LETTER ES}"),  # ‘с’
    MacroTextSpec("cyrt", "\N{CYRILLIC SMALL LETTER TE}"),  # ‘т’
    MacroTextSpec("cyru", "\N{CYRILLIC SMALL LETTER U}"),  # ‘у’
    MacroTextSpec("cyrf", "\N{CYRILLIC SMALL LETTER EF}"),  # ‘ф’
    MacroTextSpec("cyrh", "\N{CYRILLIC SMALL LETTER HA}"),  # ‘х’
    MacroTextSpec("cyrc", "\N{CYRILLIC SMALL LETTER TSE}"),  # ‘ц’
    MacroTextSpec("cyrch", "\N{CYRILLIC SMALL LETTER CHE}"),  # ‘ч’
    MacroTextSpec("cyrsh", "\N{CYRILLIC SMALL LETTER SHA}"),  # ‘ш’
    MacroTextSpec("cyrshch", "\N{CYRILLIC SMALL LETTER SHCHA}"),  # ‘щ’
    MacroTextSpec("cyrhrdsn", "\N{CYRILLIC SMALL LETTER HARD SIGN}"),  # ‘ъ’
    MacroTextSpec("cyrery", "\N{CYRILLIC SMALL LETTER YERU}"),  # ‘ы’
    MacroTextSpec("cyrsftsn", "\N{CYRILLIC SMALL LETTER SOFT SIGN}"),  # ‘ь’
    MacroTextSpec("cyrerev", "\N{CYRILLIC SMALL LETTER E}"),  # ‘э’
    MacroTextSpec("cyryu", "\N{CYRILLIC SMALL LETTER YU}"),  # ‘ю’
    MacroTextSpec("cyrya", "\N{CYRILLIC SMALL LETTER YA}"),  # ‘я’
    MacroTextSpec("cyryo", "\N{CYRILLIC SMALL LETTER IO}"),  # ‘ё’
    MacroTextSpec("cyrdje", "\N{CYRILLIC SMALL LETTER DJE}"),  # ‘ђ’
    MacroTextSpec("cyrie", "\N{CYRILLIC SMALL LETTER UKRAINIAN IE}"),  # ‘є’
    MacroTextSpec("cyrdze", "\N{CYRILLIC SMALL LETTER DZE}"),  # ‘ѕ’
    MacroTextSpec("cyrii", "\N{CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I}"),  # ‘і’
    MacroTextSpec("cyryi", "\N{CYRILLIC SMALL LETTER YI}"),  # ‘ї’
    MacroTextSpec("cyrje", "\N{CYRILLIC SMALL LETTER JE}"),  # ‘ј’
    MacroTextSpec("cyrlje", "\N{CYRILLIC SMALL LETTER LJE}"),  # ‘љ’
    MacroTextSpec("cyrnje", "\N{CYRILLIC SMALL LETTER NJE}"),  # ‘њ’
    MacroTextSpec("cyrtshe", "\N{CYRILLIC SMALL LETTER TSHE}"),  # ‘ћ’
    MacroTextSpec("cyrushrt", "\N{CYRILLIC SMALL LETTER SHORT U}"),  # ‘ў’
    MacroTextSpec("cyrdzhe", "\N{CYRILLIC SMALL LETTER DZHE}"),  # ‘џ’
    MacroTextSpec("CYRYAT", "\N{CYRILLIC CAPITAL LETTER YAT}"),  # ‘Ѣ’
    MacroTextSpec("cyryat", "\N{CYRILLIC SMALL LETTER YAT}"),  # ‘ѣ’
    MacroTextSpec("CYRBYUS", "\N{CYRILLIC CAPITAL LETTER BIG YUS}"),  # ‘Ѫ’
    MacroTextSpec("cyrbyus", "\N{CYRILLIC SMALL LETTER BIG YUS}"),  # ‘ѫ’
    MacroTextSpec("CYRFITA", "\N{CYRILLIC CAPITAL LETTER FITA}"),  # ‘Ѳ’
    MacroTextSpec("cyrfita", "\N{CYRILLIC SMALL LETTER FITA}"),  # ‘ѳ’
    MacroTextSpec("CYRIZH", "\N{CYRILLIC CAPITAL LETTER IZHITSA}"),  # ‘Ѵ’
    MacroTextSpec("cyrizh", "\N{CYRILLIC SMALL LETTER IZHITSA}"),  # ‘ѵ’
    MacroTextSpec("CYRSEMISFTSN", "\N{CYRILLIC CAPITAL LETTER SEMISOFT SIGN}"),  # ‘Ҍ’
    MacroTextSpec("cyrsemisftsn", "\N{CYRILLIC SMALL LETTER SEMISOFT SIGN}"),  # ‘ҍ’
    MacroTextSpec("CYRRTICK", "\N{CYRILLIC CAPITAL LETTER ER WITH TICK}"),  # ‘Ҏ’
    MacroTextSpec("cyrrtick", "\N{CYRILLIC SMALL LETTER ER WITH TICK}"),  # ‘ҏ’
    MacroTextSpec("CYRGUP", "\N{CYRILLIC CAPITAL LETTER GHE WITH UPTURN}"),  # ‘Ґ’
    MacroTextSpec("cyrgup", "\N{CYRILLIC SMALL LETTER GHE WITH UPTURN}"),  # ‘ґ’
    MacroTextSpec("CYRGHCRS", "\N{CYRILLIC CAPITAL LETTER GHE WITH STROKE}"),  # ‘Ғ’
    MacroTextSpec("cyrghcrs", "\N{CYRILLIC SMALL LETTER GHE WITH STROKE}"),  # ‘ғ’
    MacroTextSpec("CYRGHK", "\N{CYRILLIC CAPITAL LETTER GHE WITH MIDDLE HOOK}"),  # ‘Ҕ’
    MacroTextSpec("cyrghk", "\N{CYRILLIC SMALL LETTER GHE WITH MIDDLE HOOK}"),  # ‘ҕ’
    MacroTextSpec("CYRZHDSC", "\N{CYRILLIC CAPITAL LETTER ZHE WITH DESCENDER}"),  # ‘Җ’
    MacroTextSpec("cyrzhdsc", "\N{CYRILLIC SMALL LETTER ZHE WITH DESCENDER}"),  # ‘җ’
    MacroTextSpec("CYRZDSC", "\N{CYRILLIC CAPITAL LETTER ZE WITH DESCENDER}"),  # ‘Ҙ’
    MacroTextSpec("cyrzdsc", "\N{CYRILLIC SMALL LETTER ZE WITH DESCENDER}"),  # ‘ҙ’
    MacroTextSpec("CYRKDSC", "\N{CYRILLIC CAPITAL LETTER KA WITH DESCENDER}"),  # ‘Қ’
    MacroTextSpec("cyrkdsc", "\N{CYRILLIC SMALL LETTER KA WITH DESCENDER}"),  # ‘қ’
    MacroTextSpec(
        "CYRKVCRS", "\N{CYRILLIC CAPITAL LETTER KA WITH VERTICAL STROKE}"
    ),  # ‘Ҝ’
    MacroTextSpec(
        "cyrkvcrs", "\N{CYRILLIC SMALL LETTER KA WITH VERTICAL STROKE}"
    ),  # ‘ҝ’
    MacroTextSpec("CYRKHCRS", "\N{CYRILLIC CAPITAL LETTER KA WITH STROKE}"),  # ‘Ҟ’
    MacroTextSpec("cyrkhcrs", "\N{CYRILLIC SMALL LETTER KA WITH STROKE}"),  # ‘ҟ’
    MacroTextSpec("CYRKBEAK", "\N{CYRILLIC CAPITAL LETTER BASHKIR KA}"),  # ‘Ҡ’
    MacroTextSpec("cyrkbeak", "\N{CYRILLIC SMALL LETTER BASHKIR KA}"),  # ‘ҡ’
    MacroTextSpec("CYRNDSC", "\N{CYRILLIC CAPITAL LETTER EN WITH DESCENDER}"),  # ‘Ң’
    MacroTextSpec("cyrndsc", "\N{CYRILLIC SMALL LETTER EN WITH DESCENDER}"),  # ‘ң’
    MacroTextSpec("CYRNG", "\N{CYRILLIC CAPITAL LIGATURE EN GHE}"),  # ‘Ҥ’
    MacroTextSpec("cyrng", "\N{CYRILLIC SMALL LIGATURE EN GHE}"),  # ‘ҥ’
    MacroTextSpec("CYRPHK", "\N{CYRILLIC CAPITAL LETTER PE WITH MIDDLE HOOK}"),  # ‘Ҧ’
    MacroTextSpec("cyrphk", "\N{CYRILLIC SMALL LETTER PE WITH MIDDLE HOOK}"),  # ‘ҧ’
    MacroTextSpec("CYRABHHA", "\N{CYRILLIC CAPITAL LETTER ABKHASIAN HA}"),  # ‘Ҩ’
    MacroTextSpec("cyrabhha", "\N{CYRILLIC SMALL LETTER ABKHASIAN HA}"),  # ‘ҩ’
    MacroTextSpec("CYRSDSC", "\N{CYRILLIC CAPITAL LETTER ES WITH DESCENDER}"),  # ‘Ҫ’
    MacroTextSpec("cyrsdsc", "\N{CYRILLIC SMALL LETTER ES WITH DESCENDER}"),  # ‘ҫ’
    MacroTextSpec("CYRTDSC", "\N{CYRILLIC CAPITAL LETTER TE WITH DESCENDER}"),  # ‘Ҭ’
    MacroTextSpec("cyrtdsc", "\N{CYRILLIC SMALL LETTER TE WITH DESCENDER}"),  # ‘ҭ’
    MacroTextSpec("CYRY", "\N{CYRILLIC CAPITAL LETTER STRAIGHT U}"),  # ‘Ү’
    MacroTextSpec("cyry", "\N{CYRILLIC SMALL LETTER STRAIGHT U}"),  # ‘ү’
    MacroTextSpec(
        "CYRYHCRS", "\N{CYRILLIC CAPITAL LETTER STRAIGHT U WITH STROKE}"
    ),  # ‘Ұ’
    MacroTextSpec(
        "cyryhcrs", "\N{CYRILLIC SMALL LETTER STRAIGHT U WITH STROKE}"
    ),  # ‘ұ’
    MacroTextSpec("CYRHDSC", "\N{CYRILLIC CAPITAL LETTER HA WITH DESCENDER}"),  # ‘Ҳ’
    MacroTextSpec("cyrhdsc", "\N{CYRILLIC SMALL LETTER HA WITH DESCENDER}"),  # ‘ҳ’
    MacroTextSpec("CYRTETSE", "\N{CYRILLIC CAPITAL LIGATURE TE TSE}"),  # ‘Ҵ’
    MacroTextSpec("cyrtetse", "\N{CYRILLIC SMALL LIGATURE TE TSE}"),  # ‘ҵ’
    MacroTextSpec("CYRCHRDSC", "\N{CYRILLIC CAPITAL LETTER CHE WITH DESCENDER}"),  # ‘Ҷ’
    MacroTextSpec("cyrchrdsc", "\N{CYRILLIC SMALL LETTER CHE WITH DESCENDER}"),  # ‘ҷ’
    MacroTextSpec(
        "CYRCHVCRS", "\N{CYRILLIC CAPITAL LETTER CHE WITH VERTICAL STROKE}"
    ),  # ‘Ҹ’
    MacroTextSpec(
        "cyrchvcrs", "\N{CYRILLIC SMALL LETTER CHE WITH VERTICAL STROKE}"
    ),  # ‘ҹ’
    MacroTextSpec("CYRSHHA", "\N{CYRILLIC CAPITAL LETTER SHHA}"),  # ‘Һ’
    MacroTextSpec("cyrshha", "\N{CYRILLIC SMALL LETTER SHHA}"),  # ‘һ’
    MacroTextSpec("CYRABHCH", "\N{CYRILLIC CAPITAL LETTER ABKHASIAN CHE}"),  # ‘Ҽ’
    MacroTextSpec("cyrabhch", "\N{CYRILLIC SMALL LETTER ABKHASIAN CHE}"),  # ‘ҽ’
    MacroTextSpec(
        "CYRABHCHDSC", "\N{CYRILLIC CAPITAL LETTER ABKHASIAN CHE WITH DESCENDER}"
    ),  # ‘Ҿ’
    MacroTextSpec(
        "cyrabhchdsc", "\N{CYRILLIC SMALL LETTER ABKHASIAN CHE WITH DESCENDER}"
    ),  # ‘ҿ’
    MacroTextSpec("CYRpalochka", "\N{CYRILLIC LETTER PALOCHKA}"),  # ‘Ӏ’
    MacroTextSpec("CYRKHK", "\N{CYRILLIC CAPITAL LETTER KA WITH HOOK}"),  # ‘Ӄ’
    MacroTextSpec("cyrkhk", "\N{CYRILLIC SMALL LETTER KA WITH HOOK}"),  # ‘ӄ’
    MacroTextSpec("CYRLDSC", "\N{CYRILLIC CAPITAL LETTER EL WITH TAIL}"),  # ‘Ӆ’
    MacroTextSpec("cyrldsc", "\N{CYRILLIC SMALL LETTER EL WITH TAIL}"),  # ‘ӆ’
    MacroTextSpec("CYRNHK", "\N{CYRILLIC CAPITAL LETTER EN WITH HOOK}"),  # ‘Ӈ’
    MacroTextSpec("cyrnhk", "\N{CYRILLIC SMALL LETTER EN WITH HOOK}"),  # ‘ӈ’
    MacroTextSpec("CYRCHLDSC", "\N{CYRILLIC CAPITAL LETTER KHAKASSIAN CHE}"),  # ‘Ӌ’
    MacroTextSpec("cyrchldsc", "\N{CYRILLIC SMALL LETTER KHAKASSIAN CHE}"),  # ‘ӌ’
    MacroTextSpec("CYRMDSC", "\N{CYRILLIC CAPITAL LETTER EM WITH TAIL}"),  # ‘Ӎ’
    MacroTextSpec("cyrmdsc", "\N{CYRILLIC SMALL LETTER EM WITH TAIL}"),  # ‘ӎ’
    MacroTextSpec("CYRAE", "\N{CYRILLIC CAPITAL LIGATURE A IE}"),  # ‘Ӕ’
    MacroTextSpec("cyrae", "\N{CYRILLIC SMALL LIGATURE A IE}"),  # ‘ӕ’
    MacroTextSpec("CYRSCHWA", "\N{CYRILLIC CAPITAL LETTER SCHWA}"),  # ‘Ә’
    MacroTextSpec("cyrschwa", "\N{CYRILLIC SMALL LETTER SCHWA}"),  # ‘ә’
    MacroTextSpec("CYRABHDZE", "\N{CYRILLIC CAPITAL LETTER ABKHASIAN DZE}"),  # ‘Ӡ’
    MacroTextSpec("cyrabhdze", "\N{CYRILLIC SMALL LETTER ABKHASIAN DZE}"),  # ‘ӡ’
    MacroTextSpec("CYROTLD", "\N{CYRILLIC CAPITAL LETTER BARRED O}"),  # ‘Ө’
    MacroTextSpec("cyrotld", "\N{CYRILLIC SMALL LETTER BARRED O}"),  # ‘ө’
    MacroTextSpec("CYRGDSC", "\N{CYRILLIC CAPITAL LETTER GHE WITH DESCENDER}"),  # ‘Ӷ’
    MacroTextSpec("cyrgdsc", "\N{CYRILLIC SMALL LETTER GHE WITH DESCENDER}"),  # ‘ӷ’
    MacroTextSpec(
        "CYRGDSCHCRS", "\N{CYRILLIC CAPITAL LETTER GHE WITH STROKE AND HOOK}"
    ),  # ‘Ӻ’
    MacroTextSpec(
        "cyrgdschcrs", "\N{CYRILLIC SMALL LETTER GHE WITH STROKE AND HOOK}"
    ),  # ‘ӻ’
    MacroTextSpec("CYRHHK", "\N{CYRILLIC CAPITAL LETTER HA WITH HOOK}"),  # ‘Ӽ’
    MacroTextSpec("cyrhhk", "\N{CYRILLIC SMALL LETTER HA WITH HOOK}"),  # ‘ӽ’
    MacroTextSpec("CYRHHCRS", "\N{CYRILLIC CAPITAL LETTER HA WITH STROKE}"),  # ‘Ӿ’
    MacroTextSpec("cyrhhcrs", "\N{CYRILLIC SMALL LETTER HA WITH STROKE}"),  # ‘ӿ’
    MacroTextSpec("textbaht", "\N{THAI CURRENCY SYMBOL BAHT}"),  # ‘฿’
    MacroTextSpec("enskip", "\N{EN QUAD}"),  # ‘ ’
    MacroTextSpec("enskip", "\N{EN SPACE}"),  # ‘ ’
    MacroTextSpec("textcompwordmark", "\N{ZERO WIDTH NON-JOINER}"),  # ‘‌’
    MacroTextSpec("quotesinglbase", "\N{SINGLE LOW-9 QUOTATION MARK}"),  # ‘‚’
    MacroTextSpec("quotedblbase", "\N{DOUBLE LOW-9 QUOTATION MARK}"),  # ‘„’
    MacroTextSpec("textdagger", "\N{DAGGER}"),  # ‘†’
    MacroTextSpec("textdaggerdbl", "\N{DOUBLE DAGGER}"),  # ‘‡’
    MacroTextSpec("textbullet", "\N{BULLET}"),  # ‘•’
    MacroTextSpec("textellipsis", "\N{HORIZONTAL ELLIPSIS}"),  # ‘…’
    MacroTextSpec("textperthousand", "\N{PER MILLE SIGN}"),  # ‘‰’
    MacroTextSpec("textpertenthousand", "\N{PER TEN THOUSAND SIGN}"),  # ‘‱’
    MacroTextSpec("backprime", "\N{REVERSED PRIME}"),  # ‘‵’
    MacroTextSpec(
        "guilsinglleft", "\N{SINGLE LEFT-POINTING ANGLE QUOTATION MARK}"
    ),  # ‘‹’
    MacroTextSpec(
        "guilsinglright", "\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}"
    ),  # ‘›’
    MacroTextSpec("textreferencemark", "\N{REFERENCE MARK}"),  # ‘※’
    MacroTextSpec("textinterrobang", "\N{INTERROBANG}"),  # ‘‽’
    MacroTextSpec("textfractionsolidus", "\N{FRACTION SLASH}"),  # ‘⁄’
    MacroTextSpec("textasteriskcentered", "\N{LOW ASTERISK}"),  # ‘⁎’
    MacroTextSpec("textdiscount", "\N{COMMERCIAL MINUS SIGN}"),  # ‘⁒’
    MacroTextSpec("nolinebreak", "\N{WORD JOINER}"),  # ‘⁠’
    MacroTextSpec("textcolonmonetary", "\N{COLON SIGN}"),  # ‘₡’
    MacroTextSpec("textlira", "\N{LIRA SIGN}"),  # ‘₤’
    MacroTextSpec("textnaira", "\N{NAIRA SIGN}"),  # ‘₦’
    MacroTextSpec("textwon", "\N{WON SIGN}"),  # ‘₩’
    MacroTextSpec("textdong", "\N{DONG SIGN}"),  # ‘₫’
    MacroTextSpec("textpeso", "\N{PESO SIGN}"),  # ‘₱’
    MacroTextSpec("textcelsius", "\N{DEGREE CELSIUS}"),  # ‘℃’
    MacroTextSpec("textnumero", "\N{NUMERO SIGN}"),  # ‘№’
    MacroTextSpec("textcircledP", "\N{SOUND RECORDING COPYRIGHT}"),  # ‘℗’
    MacroTextSpec("wp", "\N{SCRIPT CAPITAL P}"),  # ‘℘’
    MacroTextSpec("textrecipe", "\N{PRESCRIPTION TAKE}"),  # ‘℞’
    MacroTextSpec("textservicemark", "\N{SERVICE MARK}"),  # ‘℠’
    MacroTextSpec("texttrademark", "\N{TRADE MARK SIGN}"),  # ‘™’
    MacroTextSpec("textohm", "\N{OHM SIGN}"),  # ‘Ω’
    MacroTextSpec("textmho", "\N{INVERTED OHM SIGN}"),  # ‘℧’
    MacroTextSpec("textestimated", "\N{ESTIMATED SYMBOL}"),  # ‘℮’
    MacroTextSpec("beth", "\N{BET SYMBOL}"),  # ‘ℶ’
    MacroTextSpec("gimel", "\N{GIMEL SYMBOL}"),  # ‘ℷ’
    MacroTextSpec("daleth", "\N{DALET SYMBOL}"),  # ‘ℸ’
    MacroTextSpec("textleftarrow", "\N{LEFTWARDS ARROW}"),  # ‘←’
    MacroTextSpec("textuparrow", "\N{UPWARDS ARROW}"),  # ‘↑’
    MacroTextSpec("textrightarrow", "\N{RIGHTWARDS ARROW}"),  # ‘→’
    MacroTextSpec("textdownarrow", "\N{DOWNWARDS ARROW}"),  # ‘↓’
    MacroTextSpec("leftrightarrow", "\N{LEFT RIGHT ARROW}"),  # ‘↔’
    MacroTextSpec("updownarrow", "\N{UP DOWN ARROW}"),  # ‘↕’
    MacroTextSpec("nwarrow", "\N{NORTH WEST ARROW}"),  # ‘↖’
    MacroTextSpec("nearrow", "\N{NORTH EAST ARROW}"),  # ‘↗’
    MacroTextSpec("searrow", "\N{SOUTH EAST ARROW}"),  # ‘↘’
    MacroTextSpec("swarrow", "\N{SOUTH WEST ARROW}"),  # ‘↙’
    MacroTextSpec("nleftarrow", "\N{LEFTWARDS ARROW WITH STROKE}"),  # ‘↚’
    MacroTextSpec("nrightarrow", "\N{RIGHTWARDS ARROW WITH STROKE}"),  # ‘↛’
    MacroTextSpec("arrowwaveleft", "\N{LEFTWARDS WAVE ARROW}"),  # ‘↜’
    MacroTextSpec("arrowwaveright", "\N{RIGHTWARDS WAVE ARROW}"),  # ‘↝’
    MacroTextSpec("twoheadleftarrow", "\N{LEFTWARDS TWO HEADED ARROW}"),  # ‘↞’
    MacroTextSpec("twoheadrightarrow", "\N{RIGHTWARDS TWO HEADED ARROW}"),  # ‘↠’
    MacroTextSpec("leftarrowtail", "\N{LEFTWARDS ARROW WITH TAIL}"),  # ‘↢’
    MacroTextSpec("rightarrowtail", "\N{RIGHTWARDS ARROW WITH TAIL}"),  # ‘↣’
    MacroTextSpec("mapsto", "\N{RIGHTWARDS ARROW FROM BAR}"),  # ‘↦’
    MacroTextSpec("hookleftarrow", "\N{LEFTWARDS ARROW WITH HOOK}"),  # ‘↩’
    MacroTextSpec("hookrightarrow", "\N{RIGHTWARDS ARROW WITH HOOK}"),  # ‘↪’
    MacroTextSpec("looparrowleft", "\N{LEFTWARDS ARROW WITH LOOP}"),  # ‘↫’
    MacroTextSpec("looparrowright", "\N{RIGHTWARDS ARROW WITH LOOP}"),  # ‘↬’
    MacroTextSpec("leftrightsquigarrow", "\N{LEFT RIGHT WAVE ARROW}"),  # ‘↭’
    MacroTextSpec("nleftrightarrow", "\N{LEFT RIGHT ARROW WITH STROKE}"),  # ‘↮’
    MacroTextSpec("Lsh", "\N{UPWARDS ARROW WITH TIP LEFTWARDS}"),  # ‘↰’
    MacroTextSpec("Rsh", "\N{UPWARDS ARROW WITH TIP RIGHTWARDS}"),  # ‘↱’
    MacroTextSpec("curvearrowleft", "\N{ANTICLOCKWISE TOP SEMICIRCLE ARROW}"),  # ‘↶’
    MacroTextSpec("curvearrowright", "\N{CLOCKWISE TOP SEMICIRCLE ARROW}"),  # ‘↷’
    MacroTextSpec("circlearrowleft", "\N{ANTICLOCKWISE OPEN CIRCLE ARROW}"),  # ‘↺’
    MacroTextSpec("circlearrowright", "\N{CLOCKWISE OPEN CIRCLE ARROW}"),  # ‘↻’
    MacroTextSpec("leftharpoonup", "\N{LEFTWARDS HARPOON WITH BARB UPWARDS}"),  # ‘↼’
    MacroTextSpec(
        "leftharpoondown", "\N{LEFTWARDS HARPOON WITH BARB DOWNWARDS}"
    ),  # ‘↽’
    MacroTextSpec("upharpoonright", "\N{UPWARDS HARPOON WITH BARB RIGHTWARDS}"),  # ‘↾’
    MacroTextSpec("upharpoonleft", "\N{UPWARDS HARPOON WITH BARB LEFTWARDS}"),  # ‘↿’
    MacroTextSpec("rightharpoonup", "\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}"),  # ‘⇀’
    MacroTextSpec(
        "rightharpoondown", "\N{RIGHTWARDS HARPOON WITH BARB DOWNWARDS}"
    ),  # ‘⇁’
    MacroTextSpec(
        "downharpoonright", "\N{DOWNWARDS HARPOON WITH BARB RIGHTWARDS}"
    ),  # ‘⇂’
    MacroTextSpec(
        "downharpoonleft", "\N{DOWNWARDS HARPOON WITH BARB LEFTWARDS}"
    ),  # ‘⇃’
    MacroTextSpec(
        "rightleftarrows", "\N{RIGHTWARDS ARROW OVER LEFTWARDS ARROW}"
    ),  # ‘⇄’
    MacroTextSpec(
        "dblarrowupdown", "\N{UPWARDS ARROW LEFTWARDS OF DOWNWARDS ARROW}"
    ),  # ‘⇅’
    MacroTextSpec(
        "leftrightarrows", "\N{LEFTWARDS ARROW OVER RIGHTWARDS ARROW}"
    ),  # ‘⇆’
    MacroTextSpec("leftleftarrows", "\N{LEFTWARDS PAIRED ARROWS}"),  # ‘⇇’
    MacroTextSpec("upuparrows", "\N{UPWARDS PAIRED ARROWS}"),  # ‘⇈’
    MacroTextSpec("rightrightarrows", "\N{RIGHTWARDS PAIRED ARROWS}"),  # ‘⇉’
    MacroTextSpec("downdownarrows", "\N{DOWNWARDS PAIRED ARROWS}"),  # ‘⇊’
    MacroTextSpec(
        "leftrightharpoons", "\N{LEFTWARDS HARPOON OVER RIGHTWARDS HARPOON}"
    ),  # ‘⇋’
    MacroTextSpec(
        "rightleftharpoons", "\N{RIGHTWARDS HARPOON OVER LEFTWARDS HARPOON}"
    ),  # ‘⇌’
    MacroTextSpec("nLeftarrow", "\N{LEFTWARDS DOUBLE ARROW WITH STROKE}"),  # ‘⇍’
    MacroTextSpec("nLeftrightarrow", "\N{LEFT RIGHT DOUBLE ARROW WITH STROKE}"),  # ‘⇎’
    MacroTextSpec("nRightarrow", "\N{RIGHTWARDS DOUBLE ARROW WITH STROKE}"),  # ‘⇏’
    MacroTextSpec("Leftarrow", "\N{LEFTWARDS DOUBLE ARROW}"),  # ‘⇐’
    MacroTextSpec("Uparrow", "\N{UPWARDS DOUBLE ARROW}"),  # ‘⇑’
    MacroTextSpec("Rightarrow", "\N{RIGHTWARDS DOUBLE ARROW}"),  # ‘⇒’
    MacroTextSpec("Downarrow", "\N{DOWNWARDS DOUBLE ARROW}"),  # ‘⇓’
    MacroTextSpec("Leftrightarrow", "\N{LEFT RIGHT DOUBLE ARROW}"),  # ‘⇔’
    MacroTextSpec("Updownarrow", "\N{UP DOWN DOUBLE ARROW}"),  # ‘⇕’
    MacroTextSpec("Lleftarrow", "\N{LEFTWARDS TRIPLE ARROW}"),  # ‘⇚’
    MacroTextSpec("Rrightarrow", "\N{RIGHTWARDS TRIPLE ARROW}"),  # ‘⇛’
    MacroTextSpec("rightsquigarrow", "\N{RIGHTWARDS SQUIGGLE ARROW}"),  # ‘⇝’
    MacroTextSpec(
        "DownArrowUpArrow", "\N{DOWNWARDS ARROW LEFTWARDS OF UPWARDS ARROW}"
    ),  # ‘⇵’
    MacroTextSpec("blacksquare", "\N{END OF PROOF}"),  # ‘∎’
    MacroTextSpec("dotplus", "\N{DOT PLUS}"),  # ‘∔’
    MacroTextSpec("rightangle", "\N{RIGHT ANGLE}"),  # ‘∟’
    MacroTextSpec("angle", "\N{ANGLE}"),  # ‘∠’
    MacroTextSpec("measuredangle", "\N{MEASURED ANGLE}"),  # ‘∡’
    MacroTextSpec("sphericalangle", "\N{SPHERICAL ANGLE}"),  # ‘∢’
    MacroTextSpec("surfintegral", "\N{SURFACE INTEGRAL}"),  # ‘∯’
    MacroTextSpec("volintegral", "\N{VOLUME INTEGRAL}"),  # ‘∰’
    MacroTextSpec("clwintegral", "\N{CLOCKWISE INTEGRAL}"),  # ‘∱’
    MacroTextSpec("therefore", "\N{THEREFORE}"),  # ‘∴’
    MacroTextSpec("because", "\N{BECAUSE}"),  # ‘∵’
    MacroTextSpec("homothetic", "\N{HOMOTHETIC}"),  # ‘∻’
    MacroTextSpec("lazysinv", "\N{INVERTED LAZY S}"),  # ‘∾’
    MacroTextSpec("wr", "\N{WREATH PRODUCT}"),  # ‘≀’
    MacroTextSpec("cong", "\N{APPROXIMATELY EQUAL TO}"),  # ‘≅’
    MacroTextSpec(
        "approxnotequal", "\N{APPROXIMATELY BUT NOT ACTUALLY EQUAL TO}"
    ),  # ‘≆’
    MacroTextSpec("approxeq", "\N{ALMOST EQUAL OR EQUAL TO}"),  # ‘≊’
    MacroTextSpec("tildetrpl", "\N{TRIPLE TILDE}"),  # ‘≋’
    MacroTextSpec("allequal", "\N{ALL EQUAL TO}"),  # ‘≌’
    MacroTextSpec("asymp", "\N{EQUIVALENT TO}"),  # ‘≍’
    MacroTextSpec("Bumpeq", "\N{GEOMETRICALLY EQUIVALENT TO}"),  # ‘≎’
    MacroTextSpec("bumpeq", "\N{DIFFERENCE BETWEEN}"),  # ‘≏’
    MacroTextSpec("doteq", "\N{APPROACHES THE LIMIT}"),  # ‘≐’
    MacroTextSpec("doteqdot", "\N{GEOMETRICALLY EQUAL TO}"),  # ‘≑’
    MacroTextSpec("fallingdotseq", "\N{APPROXIMATELY EQUAL TO OR THE IMAGE OF}"),  # ‘≒’
    MacroTextSpec("risingdotseq", "\N{IMAGE OF OR APPROXIMATELY EQUAL TO}"),  # ‘≓’
    MacroTextSpec("eqcirc", "\N{RING IN EQUAL TO}"),  # ‘≖’
    MacroTextSpec("circeq", "\N{RING EQUAL TO}"),  # ‘≗’
    MacroTextSpec("estimates", "\N{ESTIMATES}"),  # ‘≙’
    MacroTextSpec("starequal", "\N{STAR EQUALS}"),  # ‘≛’
    MacroTextSpec("triangleq", "\N{DELTA EQUAL TO}"),  # ‘≜’
    MacroTextSpec("between", "\N{BETWEEN}"),  # ‘≬’
    MacroTextSpec("notlessgreater", "\N{NEITHER LESS-THAN NOR GREATER-THAN}"),  # ‘≸’
    MacroTextSpec("notgreaterless", "\N{NEITHER GREATER-THAN NOR LESS-THAN}"),  # ‘≹’
    MacroTextSpec("uplus", "\N{MULTISET UNION}"),  # ‘⊎’
    MacroTextSpec("sqsubset", "\N{SQUARE IMAGE OF}"),  # ‘⊏’
    MacroTextSpec("sqsupset", "\N{SQUARE ORIGINAL OF}"),  # ‘⊐’
    MacroTextSpec("sqsubseteq", "\N{SQUARE IMAGE OF OR EQUAL TO}"),  # ‘⊑’
    MacroTextSpec("sqsupseteq", "\N{SQUARE ORIGINAL OF OR EQUAL TO}"),  # ‘⊒’
    MacroTextSpec("sqcap", "\N{SQUARE CAP}"),  # ‘⊓’
    MacroTextSpec("sqcup", "\N{SQUARE CUP}"),  # ‘⊔’
    MacroTextSpec("ominus", "\N{CIRCLED MINUS}"),  # ‘⊖’
    MacroTextSpec("oslash", "\N{CIRCLED DIVISION SLASH}"),  # ‘⊘’
    MacroTextSpec("odot", "\N{CIRCLED DOT OPERATOR}"),  # ‘⊙’
    MacroTextSpec("circledcirc", "\N{CIRCLED RING OPERATOR}"),  # ‘⊚’
    MacroTextSpec("circledast", "\N{CIRCLED ASTERISK OPERATOR}"),  # ‘⊛’
    MacroTextSpec("circleddash", "\N{CIRCLED DASH}"),  # ‘⊝’
    MacroTextSpec("boxplus", "\N{SQUARED PLUS}"),  # ‘⊞’
    MacroTextSpec("boxminus", "\N{SQUARED MINUS}"),  # ‘⊟’
    MacroTextSpec("boxtimes", "\N{SQUARED TIMES}"),  # ‘⊠’
    MacroTextSpec("boxdot", "\N{SQUARED DOT OPERATOR}"),  # ‘⊡’
    MacroTextSpec("vdash", "\N{RIGHT TACK}"),  # ‘⊢’
    MacroTextSpec("dashv", "\N{LEFT TACK}"),  # ‘⊣’
    MacroTextSpec("top", "\N{DOWN TACK}"),  # ‘⊤’
    MacroTextSpec("perp", "\N{UP TACK}"),  # ‘⊥’
    MacroTextSpec("truestate", "\N{MODELS}"),  # ‘⊧’
    MacroTextSpec("forcesextra", "\N{TRUE}"),  # ‘⊨’
    MacroTextSpec("Vdash", "\N{FORCES}"),  # ‘⊩’
    MacroTextSpec("Vvdash", "\N{TRIPLE VERTICAL BAR RIGHT TURNSTILE}"),  # ‘⊪’
    MacroTextSpec("VDash", "\N{DOUBLE VERTICAL BAR DOUBLE RIGHT TURNSTILE}"),  # ‘⊫’
    MacroTextSpec("nvdash", "\N{DOES NOT PROVE}"),  # ‘⊬’
    MacroTextSpec("nvDash", "\N{NOT TRUE}"),  # ‘⊭’
    MacroTextSpec("nVdash", "\N{DOES NOT FORCE}"),  # ‘⊮’
    MacroTextSpec(
        "nVDash", "\N{NEGATED DOUBLE VERTICAL BAR DOUBLE RIGHT TURNSTILE}"
    ),  # ‘⊯’
    MacroTextSpec("vartriangleleft", "\N{NORMAL SUBGROUP OF}"),  # ‘⊲’
    MacroTextSpec("vartriangleright", "\N{CONTAINS AS NORMAL SUBGROUP}"),  # ‘⊳’
    MacroTextSpec("trianglelefteq", "\N{NORMAL SUBGROUP OF OR EQUAL TO}"),  # ‘⊴’
    MacroTextSpec(
        "trianglerighteq", "\N{CONTAINS AS NORMAL SUBGROUP OR EQUAL TO}"
    ),  # ‘⊵’
    MacroTextSpec("original", "\N{ORIGINAL OF}"),  # ‘⊶’
    MacroTextSpec("image", "\N{IMAGE OF}"),  # ‘⊷’
    MacroTextSpec("multimap", "\N{MULTIMAP}"),  # ‘⊸’
    MacroTextSpec("hermitconjmatrix", "\N{HERMITIAN CONJUGATE MATRIX}"),  # ‘⊹’
    MacroTextSpec("intercal", "\N{INTERCALATE}"),  # ‘⊺’
    MacroTextSpec("veebar", "\N{XOR}"),  # ‘⊻’
    MacroTextSpec("rightanglearc", "\N{RIGHT ANGLE WITH ARC}"),  # ‘⊾’
    MacroTextSpec("bigwedge", "\N{N-ARY LOGICAL AND}"),  # ‘⋀’
    MacroTextSpec("bigvee", "\N{N-ARY LOGICAL OR}"),  # ‘⋁’
    MacroTextSpec("bigcap", "\N{N-ARY INTERSECTION}"),  # ‘⋂’
    MacroTextSpec("bigcup", "\N{N-ARY UNION}"),  # ‘⋃’
    MacroTextSpec("diamond", "\N{DIAMOND OPERATOR}"),  # ‘⋄’
    MacroTextSpec("star", "\N{STAR OPERATOR}"),  # ‘⋆’
    MacroTextSpec("divideontimes", "\N{DIVISION TIMES}"),  # ‘⋇’
    MacroTextSpec("bowtie", "\N{BOWTIE}"),  # ‘⋈’
    MacroTextSpec("ltimes", "\N{LEFT NORMAL FACTOR SEMIDIRECT PRODUCT}"),  # ‘⋉’
    MacroTextSpec("rtimes", "\N{RIGHT NORMAL FACTOR SEMIDIRECT PRODUCT}"),  # ‘⋊’
    MacroTextSpec("leftthreetimes", "\N{LEFT SEMIDIRECT PRODUCT}"),  # ‘⋋’
    MacroTextSpec("rightthreetimes", "\N{RIGHT SEMIDIRECT PRODUCT}"),  # ‘⋌’
    MacroTextSpec("backsimeq", "\N{REVERSED TILDE EQUALS}"),  # ‘⋍’
    MacroTextSpec("curlyvee", "\N{CURLY LOGICAL OR}"),  # ‘⋎’
    MacroTextSpec("curlywedge", "\N{CURLY LOGICAL AND}"),  # ‘⋏’
    MacroTextSpec("Subset", "\N{DOUBLE SUBSET}"),  # ‘⋐’
    MacroTextSpec("Supset", "\N{DOUBLE SUPERSET}"),  # ‘⋑’
    MacroTextSpec("Cap", "\N{DOUBLE INTERSECTION}"),  # ‘⋒’
    MacroTextSpec("Cup", "\N{DOUBLE UNION}"),  # ‘⋓’
    MacroTextSpec("pitchfork", "\N{PITCHFORK}"),  # ‘⋔’
    MacroTextSpec("lessdot", "\N{LESS-THAN WITH DOT}"),  # ‘⋖’
    MacroTextSpec("gtrdot", "\N{GREATER-THAN WITH DOT}"),  # ‘⋗’
    MacroTextSpec("verymuchless", "\N{VERY MUCH LESS-THAN}"),  # ‘⋘’
    MacroTextSpec("verymuchgreater", "\N{VERY MUCH GREATER-THAN}"),  # ‘⋙’
    MacroTextSpec("lesseqgtr", "\N{LESS-THAN EQUAL TO OR GREATER-THAN}"),  # ‘⋚’
    MacroTextSpec("gtreqless", "\N{GREATER-THAN EQUAL TO OR LESS-THAN}"),  # ‘⋛’
    MacroTextSpec("curlyeqprec", "\N{EQUAL TO OR PRECEDES}"),  # ‘⋞’
    MacroTextSpec("curlyeqsucc", "\N{EQUAL TO OR SUCCEEDS}"),  # ‘⋟’
    MacroTextSpec("lnsim", "\N{LESS-THAN BUT NOT EQUIVALENT TO}"),  # ‘⋦’
    MacroTextSpec("gnsim", "\N{GREATER-THAN BUT NOT EQUIVALENT TO}"),  # ‘⋧’
    MacroTextSpec("precedesnotsimilar", "\N{PRECEDES BUT NOT EQUIVALENT TO}"),  # ‘⋨’
    MacroTextSpec("succnsim", "\N{SUCCEEDS BUT NOT EQUIVALENT TO}"),  # ‘⋩’
    MacroTextSpec("ntriangleleft", "\N{NOT NORMAL SUBGROUP OF}"),  # ‘⋪’
    MacroTextSpec("ntriangleright", "\N{DOES NOT CONTAIN AS NORMAL SUBGROUP}"),  # ‘⋫’
    MacroTextSpec("ntrianglelefteq", "\N{NOT NORMAL SUBGROUP OF OR EQUAL TO}"),  # ‘⋬’
    MacroTextSpec(
        "ntrianglerighteq", "\N{DOES NOT CONTAIN AS NORMAL SUBGROUP OR EQUAL}"
    ),  # ‘⋭’
    MacroTextSpec("vdots", "\N{VERTICAL ELLIPSIS}"),  # ‘⋮’
    MacroTextSpec("udots", "\N{UP RIGHT DIAGONAL ELLIPSIS}"),  # ‘⋰’
    MacroTextSpec("barwedge", "\N{PROJECTIVE}"),  # ‘⌅’
    MacroTextSpec("varperspcorrespond", "\N{PERSPECTIVE}"),  # ‘⌆’
    MacroTextSpec("lceil", "\N{LEFT CEILING}"),  # ‘⌈’
    MacroTextSpec("rceil", "\N{RIGHT CEILING}"),  # ‘⌉’
    MacroTextSpec("lfloor", "\N{LEFT FLOOR}"),  # ‘⌊’
    MacroTextSpec("rfloor", "\N{RIGHT FLOOR}"),  # ‘⌋’
    MacroTextSpec("recorder", "\N{TELEPHONE RECORDER}"),  # ‘⌕’
    MacroTextSpec("ulcorner", "\N{TOP LEFT CORNER}"),  # ‘⌜’
    MacroTextSpec("urcorner", "\N{TOP RIGHT CORNER}"),  # ‘⌝’
    MacroTextSpec("llcorner", "\N{BOTTOM LEFT CORNER}"),  # ‘⌞’
    MacroTextSpec("lrcorner", "\N{BOTTOM RIGHT CORNER}"),  # ‘⌟’
    MacroTextSpec("frown", "\N{FROWN}"),  # ‘⌢’
    MacroTextSpec("smile", "\N{SMILE}"),  # ‘⌣’
    MacroTextSpec(
        "lmoustache", "\N{UPPER LEFT OR LOWER RIGHT CURLY BRACKET SECTION}"
    ),  # ‘⎰’
    MacroTextSpec(
        "rmoustache", "\N{UPPER RIGHT OR LOWER LEFT CURLY BRACKET SECTION}"
    ),  # ‘⎱’
    MacroTextSpec("textlangle", "\N{LEFT-POINTING ANGLE BRACKET}"),  # ‘〈’
    MacroTextSpec("textrangle", "\N{RIGHT-POINTING ANGLE BRACKET}"),  # ‘〉’
    MacroTextSpec("textblank", "\N{BLANK SYMBOL}"),  # ‘␢’
    MacroTextSpec("textvisiblespace", "\N{OPEN BOX}"),  # ‘␣’
    MacroTextSpec("blacksquare", "\N{BLACK SQUARE}"),  # ‘■’
    MacroTextSpec("square", "\N{WHITE SQUARE}"),  # ‘□’
    MacroTextSpec("bigtriangleup", "\N{WHITE UP-POINTING TRIANGLE}"),  # ‘△’
    MacroTextSpec("blacktriangle", "\N{BLACK UP-POINTING SMALL TRIANGLE}"),  # ‘▴’
    MacroTextSpec("vartriangle", "\N{WHITE UP-POINTING SMALL TRIANGLE}"),  # ‘▵’
    MacroTextSpec(
        "blacktriangleright", "\N{BLACK RIGHT-POINTING SMALL TRIANGLE}"
    ),  # ‘▸’
    MacroTextSpec("triangleright", "\N{WHITE RIGHT-POINTING SMALL TRIANGLE}"),  # ‘▹’
    MacroTextSpec("bigtriangledown", "\N{WHITE DOWN-POINTING TRIANGLE}"),  # ‘▽’
    MacroTextSpec("blacktriangledown", "\N{BLACK DOWN-POINTING SMALL TRIANGLE}"),  # ‘▾’
    MacroTextSpec("triangledown", "\N{WHITE DOWN-POINTING SMALL TRIANGLE}"),  # ‘▿’
    MacroTextSpec("blacktriangleleft", "\N{BLACK LEFT-POINTING SMALL TRIANGLE}"),  # ‘◂’
    MacroTextSpec("triangleleft", "\N{WHITE LEFT-POINTING SMALL TRIANGLE}"),  # ‘◃’
    MacroTextSpec("lozenge", "\N{LOZENGE}"),  # ‘◊’
    MacroTextSpec("bigcirc", "\N{WHITE CIRCLE}"),  # ‘○’
    MacroTextSpec("textopenbullet", "\N{WHITE BULLET}"),  # ‘◦’
    MacroTextSpec("textbigcircle", "\N{LARGE CIRCLE}"),  # ‘◯’
    MacroTextSpec("diamond", "\N{WHITE DIAMOND SUIT}"),  # ‘♢’
    MacroTextSpec("textmusicalnote", "\N{EIGHTH NOTE}"),  # ‘♪’
    MacroTextSpec("quarternote", "\N{QUARTER NOTE}"),  # ‘♩’
    MacroTextSpec("flat", "\N{MUSIC FLAT SIGN}"),  # ‘♭’
    MacroTextSpec("natural", "\N{MUSIC NATURAL SIGN}"),  # ‘♮’
    MacroTextSpec("sharp", "\N{MUSIC SHARP SIGN}"),  # ‘♯’
    MacroTextSpec("longleftrightarrow", "\N{LONG LEFT RIGHT ARROW}"),  # ‘⟷’
    MacroTextSpec("Longleftarrow", "\N{LONG LEFTWARDS DOUBLE ARROW}"),  # ‘⟸’
    MacroTextSpec("Longrightarrow", "\N{LONG RIGHTWARDS DOUBLE ARROW}"),  # ‘⟹’
    MacroTextSpec("Longleftrightarrow", "\N{LONG LEFT RIGHT DOUBLE ARROW}"),  # ‘⟺’
    MacroTextSpec("longmapsto", "\N{LONG RIGHTWARDS ARROW FROM BAR}"),  # ‘⟼’
    MacroTextSpec("blacklozenge", "\N{BLACK LOZENGE}"),  # ‘⧫’
    MacroTextSpec("clockoint", "\N{INTEGRAL AVERAGE WITH SLASH}"),  # ‘⨏’
    MacroTextSpec("sqrint", "\N{QUATERNION INTEGRAL OPERATOR}"),  # ‘⨖’
    MacroTextSpec("amalg", "\N{AMALGAMATION OR COPRODUCT}"),  # ‘⨿’
    MacroTextSpec("lessapprox", "\N{LESS-THAN OR APPROXIMATE}"),  # ‘⪅’
    MacroTextSpec("gtrapprox", "\N{GREATER-THAN OR APPROXIMATE}"),  # ‘⪆’
    MacroTextSpec("lneq", "\N{LESS-THAN AND SINGLE-LINE NOT EQUAL TO}"),  # ‘⪇’
    MacroTextSpec("gneq", "\N{GREATER-THAN AND SINGLE-LINE NOT EQUAL TO}"),  # ‘⪈’
    MacroTextSpec("lnapprox", "\N{LESS-THAN AND NOT APPROXIMATE}"),  # ‘⪉’
    MacroTextSpec("gnapprox", "\N{GREATER-THAN AND NOT APPROXIMATE}"),  # ‘⪊’
    MacroTextSpec(
        "lesseqqgtr", "\N{LESS-THAN ABOVE DOUBLE-LINE EQUAL ABOVE GREATER-THAN}"
    ),  # ‘⪋’
    MacroTextSpec(
        "gtreqqless", "\N{GREATER-THAN ABOVE DOUBLE-LINE EQUAL ABOVE LESS-THAN}"
    ),  # ‘⪌’
    MacroTextSpec("eqslantless", "\N{SLANTED EQUAL TO OR LESS-THAN}"),  # ‘⪕’
    MacroTextSpec("eqslantgtr", "\N{SLANTED EQUAL TO OR GREATER-THAN}"),  # ‘⪖’
    MacroTextSpec("precneqq", "\N{PRECEDES ABOVE NOT EQUAL TO}"),  # ‘⪵’
    MacroTextSpec("succneqq", "\N{SUCCEEDS ABOVE NOT EQUAL TO}"),  # ‘⪶’
    MacroTextSpec("precapprox", "\N{PRECEDES ABOVE ALMOST EQUAL TO}"),  # ‘⪷’
    MacroTextSpec("succapprox", "\N{SUCCEEDS ABOVE ALMOST EQUAL TO}"),  # ‘⪸’
    MacroTextSpec("precnapprox", "\N{PRECEDES ABOVE NOT ALMOST EQUAL TO}"),  # ‘⪹’
    MacroTextSpec("succnapprox", "\N{SUCCEEDS ABOVE NOT ALMOST EQUAL TO}"),  # ‘⪺’
    MacroTextSpec("subseteqq", "\N{SUBSET OF ABOVE EQUALS SIGN}"),  # ‘⫅’
    MacroTextSpec("supseteqq", "\N{SUPERSET OF ABOVE EQUALS SIGN}"),  # ‘⫆’
    MacroTextSpec("subsetneqq", "\N{SUBSET OF ABOVE NOT EQUAL TO}"),  # ‘⫋’
    MacroTextSpec("supsetneqq", "\N{SUPERSET OF ABOVE NOT EQUAL TO}"),  # ‘⫌’
    # Rules from latexencode defaults 'unicode-xml'
    MacroTextSpec("textdollar", "\N{DOLLAR SIGN}"),  # ‘$’
    MacroTextSpec("textquotesingle", "\N{APOSTROPHE}"),  # ‘'’
    MacroTextSpec("textasciigrave", "\N{GRAVE ACCENT}"),  # ‘`’
    MacroTextSpec("lbrace", "\N{LEFT CURLY BRACKET}"),  # ‘{’
    MacroTextSpec("rbrace", "\N{RIGHT CURLY BRACKET}"),  # ‘}’
    MacroTextSpec("textasciitilde", "\N{TILDE}"),  # ‘~’
    MacroTextSpec("textexclamdown", "\N{INVERTED EXCLAMATION MARK}"),  # ‘¡’
    MacroTextSpec("textcent", "\N{CENT SIGN}"),  # ‘¢’
    MacroTextSpec("textsterling", "\N{POUND SIGN}"),  # ‘£’
    MacroTextSpec("textcurrency", "\N{CURRENCY SIGN}"),  # ‘¤’
    MacroTextSpec("textyen", "\N{YEN SIGN}"),  # ‘¥’
    MacroTextSpec("textbrokenbar", "\N{BROKEN BAR}"),  # ‘¦’
    MacroTextSpec("textsection", "\N{SECTION SIGN}"),  # ‘§’
    MacroTextSpec("textasciidieresis", "\N{DIAERESIS}"),  # ‘¨’
    MacroTextSpec("textcopyright", "\N{COPYRIGHT SIGN}"),  # ‘©’
    MacroTextSpec("textordfeminine", "\N{FEMININE ORDINAL INDICATOR}"),  # ‘ª’
    MacroTextSpec(
        "guillemotleft", "\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}"
    ),  # ‘«’
    MacroTextSpec("lnot", "\N{NOT SIGN}"),  # ‘¬’
    MacroTextSpec("-", "\N{SOFT HYPHEN}"),  # ‘­’
    MacroTextSpec("textregistered", "\N{REGISTERED SIGN}"),  # ‘®’
    MacroTextSpec("textasciimacron", "\N{MACRON}"),  # ‘¯’
    MacroTextSpec("textdegree", "\N{DEGREE SIGN}"),  # ‘°’
    MacroTextSpec("textasciiacute", "\N{ACUTE ACCENT}"),  # ‘´’
    MacroTextSpec("textparagraph", "\N{PILCROW SIGN}"),  # ‘¶’
    MacroTextSpec("textordmasculine", "\N{MASCULINE ORDINAL INDICATOR}"),  # ‘º’
    MacroTextSpec(
        "guillemotright", "\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}"
    ),  # ‘»’
    MacroTextSpec("textonequarter", "\N{VULGAR FRACTION ONE QUARTER}"),  # ‘¼’
    MacroTextSpec("textonehalf", "\N{VULGAR FRACTION ONE HALF}"),  # ‘½’
    MacroTextSpec("textthreequarters", "\N{VULGAR FRACTION THREE QUARTERS}"),  # ‘¾’
    MacroTextSpec("textquestiondown", "\N{INVERTED QUESTION MARK}"),  # ‘¿’
    MacroTextSpec("DH", "\N{LATIN CAPITAL LETTER ETH}"),  # ‘Ð’
    MacroTextSpec("texttimes", "\N{MULTIPLICATION SIGN}"),  # ‘×’
    MacroTextSpec("TH", "\N{LATIN CAPITAL LETTER THORN}"),  # ‘Þ’
    MacroTextSpec("dh", "\N{LATIN SMALL LETTER ETH}"),  # ‘ð’
    MacroTextSpec("div", "\N{DIVISION SIGN}"),  # ‘÷’
    MacroTextSpec("th", "\N{LATIN SMALL LETTER THORN}"),  # ‘þ’
    MacroTextSpec("DJ", "\N{LATIN CAPITAL LETTER D WITH STROKE}"),  # ‘Đ’
    MacroTextSpec("dj", "\N{LATIN SMALL LETTER D WITH STROKE}"),  # ‘đ’
    MacroTextSpec("NG", "\N{LATIN CAPITAL LETTER ENG}"),  # ‘Ŋ’
    MacroTextSpec("ng", "\N{LATIN SMALL LETTER ENG}"),  # ‘ŋ’
    MacroTextSpec("texthvlig", "\N{LATIN SMALL LETTER HV}"),  # ‘ƕ’
    MacroTextSpec("textnrleg", "\N{LATIN SMALL LETTER N WITH LONG RIGHT LEG}"),  # ‘ƞ’
    MacroTextSpec("eth", "\N{LATIN LETTER REVERSED ESH LOOP}"),  # ‘ƪ’
    MacroTextSpec("textdoublepipe", "\N{LATIN LETTER ALVEOLAR CLICK}"),  # ‘ǂ’
    MacroTextSpec("textphi", "\N{LATIN SMALL LETTER PHI}"),  # ‘ɸ’
    MacroTextSpec("textturnk", "\N{LATIN SMALL LETTER TURNED K}"),  # ‘ʞ’
    MacroTextSpec("textasciicaron", "\N{CARON}"),  # ‘ˇ’
    MacroTextSpec("textasciibreve", "\N{BREVE}"),  # ‘˘’
    MacroTextSpec("textperiodcentered", "\N{DOT ABOVE}"),  # ‘˙’
    MacroTextSpec("texttildelow", "\N{SMALL TILDE}"),  # ‘˜’
    MacroTextSpec("texttheta", "\N{GREEK SMALL LETTER THETA}"),  # ‘θ’
    MacroTextSpec("textvartheta", "\N{GREEK THETA SYMBOL}"),  # ‘ϑ’
    MacroTextSpec("Stigma", "\N{GREEK LETTER STIGMA}"),  # ‘Ϛ’
    MacroTextSpec("Digamma", "\N{GREEK LETTER DIGAMMA}"),  # ‘Ϝ’
    MacroTextSpec("digamma", "\N{GREEK SMALL LETTER DIGAMMA}"),  # ‘ϝ’
    MacroTextSpec("Koppa", "\N{GREEK LETTER KOPPA}"),  # ‘Ϟ’
    MacroTextSpec("Sampi", "\N{GREEK LETTER SAMPI}"),  # ‘Ϡ’
    MacroTextSpec("varkappa", "\N{GREEK KAPPA SYMBOL}"),  # ‘ϰ’
    MacroTextSpec("textTheta", "\N{GREEK CAPITAL THETA SYMBOL}"),  # ‘ϴ’
    MacroTextSpec("backepsilon", "\N{GREEK REVERSED LUNATE EPSILON SYMBOL}"),  # ‘϶’
    MacroTextSpec("textdagger", "\N{DAGGER}"),  # ‘†’
    MacroTextSpec("textdaggerdbl", "\N{DOUBLE DAGGER}"),  # ‘‡’
    MacroTextSpec("textbullet", "\N{BULLET}"),  # ‘•’
    MacroTextSpec("textperthousand", "\N{PER MILLE SIGN}"),  # ‘‰’
    MacroTextSpec("textpertenthousand", "\N{PER TEN THOUSAND SIGN}"),  # ‘‱’
    MacroTextSpec("backprime", "\N{REVERSED PRIME}"),  # ‘‵’
    MacroTextSpec(
        "guilsinglleft", "\N{SINGLE LEFT-POINTING ANGLE QUOTATION MARK}"
    ),  # ‘‹’
    MacroTextSpec(
        "guilsinglright", "\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}"
    ),  # ‘›’
    MacroTextSpec("nolinebreak", "\N{WORD JOINER}"),  # ‘⁠’
    MacroTextSpec("dddot", "\N{COMBINING THREE DOTS ABOVE}"),  # ‘⃛’
    MacroTextSpec("ddddot", "\N{COMBINING FOUR DOTS ABOVE}"),  # ‘⃜’
    MacroTextSpec("hslash", "\N{PLANCK CONSTANT OVER TWO PI}"),  # ‘ℏ’
    MacroTextSpec("wp", "\N{SCRIPT CAPITAL P}"),  # ‘℘’
    MacroTextSpec("texttrademark", "\N{TRADE MARK SIGN}"),  # ‘™’
    MacroTextSpec("mho", "\N{INVERTED OHM SIGN}"),  # ‘℧’
    MacroTextSpec("beth", "\N{BET SYMBOL}"),  # ‘ℶ’
    MacroTextSpec("gimel", "\N{GIMEL SYMBOL}"),  # ‘ℷ’
    MacroTextSpec("daleth", "\N{DALET SYMBOL}"),  # ‘ℸ’
    MacroTextSpec("leftrightarrow", "\N{LEFT RIGHT ARROW}"),  # ‘↔’
    MacroTextSpec("updownarrow", "\N{UP DOWN ARROW}"),  # ‘↕’
    MacroTextSpec("nwarrow", "\N{NORTH WEST ARROW}"),  # ‘↖’
    MacroTextSpec("nearrow", "\N{NORTH EAST ARROW}"),  # ‘↗’
    MacroTextSpec("searrow", "\N{SOUTH EAST ARROW}"),  # ‘↘’
    MacroTextSpec("swarrow", "\N{SOUTH WEST ARROW}"),  # ‘↙’
    MacroTextSpec("nleftarrow", "\N{LEFTWARDS ARROW WITH STROKE}"),  # ‘↚’
    MacroTextSpec("nrightarrow", "\N{RIGHTWARDS ARROW WITH STROKE}"),  # ‘↛’
    MacroTextSpec("arrowwaveleft", "\N{LEFTWARDS WAVE ARROW}"),  # ‘↜’
    MacroTextSpec("arrowwaveright", "\N{RIGHTWARDS WAVE ARROW}"),  # ‘↝’
    MacroTextSpec("twoheadleftarrow", "\N{LEFTWARDS TWO HEADED ARROW}"),  # ‘↞’
    MacroTextSpec("twoheadrightarrow", "\N{RIGHTWARDS TWO HEADED ARROW}"),  # ‘↠’
    MacroTextSpec("leftarrowtail", "\N{LEFTWARDS ARROW WITH TAIL}"),  # ‘↢’
    MacroTextSpec("rightarrowtail", "\N{RIGHTWARDS ARROW WITH TAIL}"),  # ‘↣’
    MacroTextSpec("mapsto", "\N{RIGHTWARDS ARROW FROM BAR}"),  # ‘↦’
    MacroTextSpec("hookleftarrow", "\N{LEFTWARDS ARROW WITH HOOK}"),  # ‘↩’
    MacroTextSpec("hookrightarrow", "\N{RIGHTWARDS ARROW WITH HOOK}"),  # ‘↪’
    MacroTextSpec("looparrowleft", "\N{LEFTWARDS ARROW WITH LOOP}"),  # ‘↫’
    MacroTextSpec("looparrowright", "\N{RIGHTWARDS ARROW WITH LOOP}"),  # ‘↬’
    MacroTextSpec("leftrightsquigarrow", "\N{LEFT RIGHT WAVE ARROW}"),  # ‘↭’
    MacroTextSpec("nleftrightarrow", "\N{LEFT RIGHT ARROW WITH STROKE}"),  # ‘↮’
    MacroTextSpec("Lsh", "\N{UPWARDS ARROW WITH TIP LEFTWARDS}"),  # ‘↰’
    MacroTextSpec("Rsh", "\N{UPWARDS ARROW WITH TIP RIGHTWARDS}"),  # ‘↱’
    MacroTextSpec("curvearrowleft", "\N{ANTICLOCKWISE TOP SEMICIRCLE ARROW}"),  # ‘↶’
    MacroTextSpec("curvearrowright", "\N{CLOCKWISE TOP SEMICIRCLE ARROW}"),  # ‘↷’
    MacroTextSpec("circlearrowleft", "\N{ANTICLOCKWISE OPEN CIRCLE ARROW}"),  # ‘↺’
    MacroTextSpec("circlearrowright", "\N{CLOCKWISE OPEN CIRCLE ARROW}"),  # ‘↻’
    MacroTextSpec("leftharpoonup", "\N{LEFTWARDS HARPOON WITH BARB UPWARDS}"),  # ‘↼’
    MacroTextSpec(
        "leftharpoondown", "\N{LEFTWARDS HARPOON WITH BARB DOWNWARDS}"
    ),  # ‘↽’
    MacroTextSpec("upharpoonright", "\N{UPWARDS HARPOON WITH BARB RIGHTWARDS}"),  # ‘↾’
    MacroTextSpec("upharpoonleft", "\N{UPWARDS HARPOON WITH BARB LEFTWARDS}"),  # ‘↿’
    MacroTextSpec("rightharpoonup", "\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}"),  # ‘⇀’
    MacroTextSpec(
        "rightharpoondown", "\N{RIGHTWARDS HARPOON WITH BARB DOWNWARDS}"
    ),  # ‘⇁’
    MacroTextSpec(
        "downharpoonright", "\N{DOWNWARDS HARPOON WITH BARB RIGHTWARDS}"
    ),  # ‘⇂’
    MacroTextSpec(
        "downharpoonleft", "\N{DOWNWARDS HARPOON WITH BARB LEFTWARDS}"
    ),  # ‘⇃’
    MacroTextSpec(
        "rightleftarrows", "\N{RIGHTWARDS ARROW OVER LEFTWARDS ARROW}"
    ),  # ‘⇄’
    MacroTextSpec(
        "dblarrowupdown", "\N{UPWARDS ARROW LEFTWARDS OF DOWNWARDS ARROW}"
    ),  # ‘⇅’
    MacroTextSpec(
        "leftrightarrows", "\N{LEFTWARDS ARROW OVER RIGHTWARDS ARROW}"
    ),  # ‘⇆’
    MacroTextSpec("leftleftarrows", "\N{LEFTWARDS PAIRED ARROWS}"),  # ‘⇇’
    MacroTextSpec("upuparrows", "\N{UPWARDS PAIRED ARROWS}"),  # ‘⇈’
    MacroTextSpec("rightrightarrows", "\N{RIGHTWARDS PAIRED ARROWS}"),  # ‘⇉’
    MacroTextSpec("downdownarrows", "\N{DOWNWARDS PAIRED ARROWS}"),  # ‘⇊’
    MacroTextSpec(
        "leftrightharpoons", "\N{LEFTWARDS HARPOON OVER RIGHTWARDS HARPOON}"
    ),  # ‘⇋’
    MacroTextSpec(
        "rightleftharpoons", "\N{RIGHTWARDS HARPOON OVER LEFTWARDS HARPOON}"
    ),  # ‘⇌’
    MacroTextSpec("nLeftarrow", "\N{LEFTWARDS DOUBLE ARROW WITH STROKE}"),  # ‘⇍’
    MacroTextSpec("nLeftrightarrow", "\N{LEFT RIGHT DOUBLE ARROW WITH STROKE}"),  # ‘⇎’
    MacroTextSpec("nRightarrow", "\N{RIGHTWARDS DOUBLE ARROW WITH STROKE}"),  # ‘⇏’
    MacroTextSpec("Leftarrow", "\N{LEFTWARDS DOUBLE ARROW}"),  # ‘⇐’
    MacroTextSpec("Uparrow", "\N{UPWARDS DOUBLE ARROW}"),  # ‘⇑’
    MacroTextSpec("Rightarrow", "\N{RIGHTWARDS DOUBLE ARROW}"),  # ‘⇒’
    MacroTextSpec("Downarrow", "\N{DOWNWARDS DOUBLE ARROW}"),  # ‘⇓’
    MacroTextSpec("Leftrightarrow", "\N{LEFT RIGHT DOUBLE ARROW}"),  # ‘⇔’
    MacroTextSpec("Updownarrow", "\N{UP DOWN DOUBLE ARROW}"),  # ‘⇕’
    MacroTextSpec("Lleftarrow", "\N{LEFTWARDS TRIPLE ARROW}"),  # ‘⇚’
    MacroTextSpec("Rrightarrow", "\N{RIGHTWARDS TRIPLE ARROW}"),  # ‘⇛’
    MacroTextSpec("rightsquigarrow", "\N{RIGHTWARDS SQUIGGLE ARROW}"),  # ‘⇝’
    MacroTextSpec(
        "DownArrowUpArrow", "\N{DOWNWARDS ARROW LEFTWARDS OF UPWARDS ARROW}"
    ),  # ‘⇵’
    MacroTextSpec("dotplus", "\N{DOT PLUS}"),  # ‘∔’
    MacroTextSpec("surd", "\N{SQUARE ROOT}"),  # ‘√’
    MacroTextSpec("rightangle", "\N{RIGHT ANGLE}"),  # ‘∟’
    MacroTextSpec("angle", "\N{ANGLE}"),  # ‘∠’
    MacroTextSpec("measuredangle", "\N{MEASURED ANGLE}"),  # ‘∡’
    MacroTextSpec("sphericalangle", "\N{SPHERICAL ANGLE}"),  # ‘∢’
    MacroTextSpec("surfintegral", "\N{SURFACE INTEGRAL}"),  # ‘∯’
    MacroTextSpec("volintegral", "\N{VOLUME INTEGRAL}"),  # ‘∰’
    MacroTextSpec("clwintegral", "\N{CLOCKWISE INTEGRAL}"),  # ‘∱’
    MacroTextSpec("therefore", "\N{THEREFORE}"),  # ‘∴’
    MacroTextSpec("because", "\N{BECAUSE}"),  # ‘∵’
    MacroTextSpec("Colon", "\N{PROPORTION}"),  # ‘∷’
    MacroTextSpec("homothetic", "\N{HOMOTHETIC}"),  # ‘∻’
    MacroTextSpec("lazysinv", "\N{INVERTED LAZY S}"),  # ‘∾’
    MacroTextSpec("wr", "\N{WREATH PRODUCT}"),  # ‘≀’
    MacroTextSpec("cong", "\N{APPROXIMATELY EQUAL TO}"),  # ‘≅’
    MacroTextSpec(
        "approxnotequal", "\N{APPROXIMATELY BUT NOT ACTUALLY EQUAL TO}"
    ),  # ‘≆’
    MacroTextSpec("approxeq", "\N{ALMOST EQUAL OR EQUAL TO}"),  # ‘≊’
    MacroTextSpec("tildetrpl", "\N{TRIPLE TILDE}"),  # ‘≋’
    MacroTextSpec("allequal", "\N{ALL EQUAL TO}"),  # ‘≌’
    MacroTextSpec("asymp", "\N{EQUIVALENT TO}"),  # ‘≍’
    MacroTextSpec("Bumpeq", "\N{GEOMETRICALLY EQUIVALENT TO}"),  # ‘≎’
    MacroTextSpec("bumpeq", "\N{DIFFERENCE BETWEEN}"),  # ‘≏’
    MacroTextSpec("doteq", "\N{APPROACHES THE LIMIT}"),  # ‘≐’
    MacroTextSpec("doteqdot", "\N{GEOMETRICALLY EQUAL TO}"),  # ‘≑’
    MacroTextSpec("fallingdotseq", "\N{APPROXIMATELY EQUAL TO OR THE IMAGE OF}"),  # ‘≒’
    MacroTextSpec("risingdotseq", "\N{IMAGE OF OR APPROXIMATELY EQUAL TO}"),  # ‘≓’
    MacroTextSpec("eqcirc", "\N{RING IN EQUAL TO}"),  # ‘≖’
    MacroTextSpec("circeq", "\N{RING EQUAL TO}"),  # ‘≗’
    MacroTextSpec("estimates", "\N{ESTIMATES}"),  # ‘≙’
    MacroTextSpec("starequal", "\N{STAR EQUALS}"),  # ‘≛’
    MacroTextSpec("triangleq", "\N{DELTA EQUAL TO}"),  # ‘≜’
    MacroTextSpec("between", "\N{BETWEEN}"),  # ‘≬’
    MacroTextSpec("lessequivlnt", "\N{LESS-THAN OR EQUIVALENT TO}"),  # ‘≲’
    MacroTextSpec("greaterequivlnt", "\N{GREATER-THAN OR EQUIVALENT TO}"),  # ‘≳’
    MacroTextSpec("notlessgreater", "\N{NEITHER LESS-THAN NOR GREATER-THAN}"),  # ‘≸’
    MacroTextSpec("notgreaterless", "\N{NEITHER GREATER-THAN NOR LESS-THAN}"),  # ‘≹’
    MacroTextSpec("preccurlyeq", "\N{PRECEDES OR EQUAL TO}"),  # ‘≼’
    MacroTextSpec("succcurlyeq", "\N{SUCCEEDS OR EQUAL TO}"),  # ‘≽’
    MacroTextSpec("precapprox", "\N{PRECEDES OR EQUIVALENT TO}"),  # ‘≾’
    MacroTextSpec("succapprox", "\N{SUCCEEDS OR EQUIVALENT TO}"),  # ‘≿’
    MacroTextSpec("uplus", "\N{MULTISET UNION}"),  # ‘⊎’
    MacroTextSpec("sqsubset", "\N{SQUARE IMAGE OF}"),  # ‘⊏’
    MacroTextSpec("sqsupset", "\N{SQUARE ORIGINAL OF}"),  # ‘⊐’
    MacroTextSpec("sqsubseteq", "\N{SQUARE IMAGE OF OR EQUAL TO}"),  # ‘⊑’
    MacroTextSpec("sqsupseteq", "\N{SQUARE ORIGINAL OF OR EQUAL TO}"),  # ‘⊒’
    MacroTextSpec("sqcap", "\N{SQUARE CAP}"),  # ‘⊓’
    MacroTextSpec("sqcup", "\N{SQUARE CUP}"),  # ‘⊔’
    MacroTextSpec("ominus", "\N{CIRCLED MINUS}"),  # ‘⊖’
    MacroTextSpec("oslash", "\N{CIRCLED DIVISION SLASH}"),  # ‘⊘’
    MacroTextSpec("odot", "\N{CIRCLED DOT OPERATOR}"),  # ‘⊙’
    MacroTextSpec("circledcirc", "\N{CIRCLED RING OPERATOR}"),  # ‘⊚’
    MacroTextSpec("circledast", "\N{CIRCLED ASTERISK OPERATOR}"),  # ‘⊛’
    MacroTextSpec("circleddash", "\N{CIRCLED DASH}"),  # ‘⊝’
    MacroTextSpec("boxplus", "\N{SQUARED PLUS}"),  # ‘⊞’
    MacroTextSpec("boxminus", "\N{SQUARED MINUS}"),  # ‘⊟’
    MacroTextSpec("boxtimes", "\N{SQUARED TIMES}"),  # ‘⊠’
    MacroTextSpec("boxdot", "\N{SQUARED DOT OPERATOR}"),  # ‘⊡’
    MacroTextSpec("vdash", "\N{RIGHT TACK}"),  # ‘⊢’
    MacroTextSpec("dashv", "\N{LEFT TACK}"),  # ‘⊣’
    MacroTextSpec("top", "\N{DOWN TACK}"),  # ‘⊤’
    MacroTextSpec("perp", "\N{UP TACK}"),  # ‘⊥’
    MacroTextSpec("truestate", "\N{MODELS}"),  # ‘⊧’
    MacroTextSpec("forcesextra", "\N{TRUE}"),  # ‘⊨’
    MacroTextSpec("Vdash", "\N{FORCES}"),  # ‘⊩’
    MacroTextSpec("Vvdash", "\N{TRIPLE VERTICAL BAR RIGHT TURNSTILE}"),  # ‘⊪’
    MacroTextSpec("VDash", "\N{DOUBLE VERTICAL BAR DOUBLE RIGHT TURNSTILE}"),  # ‘⊫’
    MacroTextSpec("nvdash", "\N{DOES NOT PROVE}"),  # ‘⊬’
    MacroTextSpec("nvDash", "\N{NOT TRUE}"),  # ‘⊭’
    MacroTextSpec("nVdash", "\N{DOES NOT FORCE}"),  # ‘⊮’
    MacroTextSpec(
        "nVDash", "\N{NEGATED DOUBLE VERTICAL BAR DOUBLE RIGHT TURNSTILE}"
    ),  # ‘⊯’
    MacroTextSpec("vartriangleleft", "\N{NORMAL SUBGROUP OF}"),  # ‘⊲’
    MacroTextSpec("vartriangleright", "\N{CONTAINS AS NORMAL SUBGROUP}"),  # ‘⊳’
    MacroTextSpec("trianglelefteq", "\N{NORMAL SUBGROUP OF OR EQUAL TO}"),  # ‘⊴’
    MacroTextSpec(
        "trianglerighteq", "\N{CONTAINS AS NORMAL SUBGROUP OR EQUAL TO}"
    ),  # ‘⊵’
    MacroTextSpec("original", "\N{ORIGINAL OF}"),  # ‘⊶’
    MacroTextSpec("image", "\N{IMAGE OF}"),  # ‘⊷’
    MacroTextSpec("multimap", "\N{MULTIMAP}"),  # ‘⊸’
    MacroTextSpec("hermitconjmatrix", "\N{HERMITIAN CONJUGATE MATRIX}"),  # ‘⊹’
    MacroTextSpec("intercal", "\N{INTERCALATE}"),  # ‘⊺’
    MacroTextSpec("veebar", "\N{XOR}"),  # ‘⊻’
    MacroTextSpec("rightanglearc", "\N{RIGHT ANGLE WITH ARC}"),  # ‘⊾’
    MacroTextSpec("bigcap", "\N{N-ARY INTERSECTION}"),  # ‘⋂’
    MacroTextSpec("bigcup", "\N{N-ARY UNION}"),  # ‘⋃’
    MacroTextSpec("diamond", "\N{DIAMOND OPERATOR}"),  # ‘⋄’
    MacroTextSpec("star", "\N{STAR OPERATOR}"),  # ‘⋆’
    MacroTextSpec("divideontimes", "\N{DIVISION TIMES}"),  # ‘⋇’
    MacroTextSpec("bowtie", "\N{BOWTIE}"),  # ‘⋈’
    MacroTextSpec("ltimes", "\N{LEFT NORMAL FACTOR SEMIDIRECT PRODUCT}"),  # ‘⋉’
    MacroTextSpec("rtimes", "\N{RIGHT NORMAL FACTOR SEMIDIRECT PRODUCT}"),  # ‘⋊’
    MacroTextSpec("leftthreetimes", "\N{LEFT SEMIDIRECT PRODUCT}"),  # ‘⋋’
    MacroTextSpec("rightthreetimes", "\N{RIGHT SEMIDIRECT PRODUCT}"),  # ‘⋌’
    MacroTextSpec("backsimeq", "\N{REVERSED TILDE EQUALS}"),  # ‘⋍’
    MacroTextSpec("curlyvee", "\N{CURLY LOGICAL OR}"),  # ‘⋎’
    MacroTextSpec("curlywedge", "\N{CURLY LOGICAL AND}"),  # ‘⋏’
    MacroTextSpec("Subset", "\N{DOUBLE SUBSET}"),  # ‘⋐’
    MacroTextSpec("Supset", "\N{DOUBLE SUPERSET}"),  # ‘⋑’
    MacroTextSpec("Cap", "\N{DOUBLE INTERSECTION}"),  # ‘⋒’
    MacroTextSpec("Cup", "\N{DOUBLE UNION}"),  # ‘⋓’
    MacroTextSpec("pitchfork", "\N{PITCHFORK}"),  # ‘⋔’
    MacroTextSpec("lessdot", "\N{LESS-THAN WITH DOT}"),  # ‘⋖’
    MacroTextSpec("gtrdot", "\N{GREATER-THAN WITH DOT}"),  # ‘⋗’
    MacroTextSpec("verymuchless", "\N{VERY MUCH LESS-THAN}"),  # ‘⋘’
    MacroTextSpec("verymuchgreater", "\N{VERY MUCH GREATER-THAN}"),  # ‘⋙’
    MacroTextSpec("lesseqgtr", "\N{LESS-THAN EQUAL TO OR GREATER-THAN}"),  # ‘⋚’
    MacroTextSpec("gtreqless", "\N{GREATER-THAN EQUAL TO OR LESS-THAN}"),  # ‘⋛’
    MacroTextSpec("curlyeqprec", "\N{EQUAL TO OR PRECEDES}"),  # ‘⋞’
    MacroTextSpec("curlyeqsucc", "\N{EQUAL TO OR SUCCEEDS}"),  # ‘⋟’
    MacroTextSpec("lnsim", "\N{LESS-THAN BUT NOT EQUIVALENT TO}"),  # ‘⋦’
    MacroTextSpec("gnsim", "\N{GREATER-THAN BUT NOT EQUIVALENT TO}"),  # ‘⋧’
    MacroTextSpec("precedesnotsimilar", "\N{PRECEDES BUT NOT EQUIVALENT TO}"),  # ‘⋨’
    MacroTextSpec("succnsim", "\N{SUCCEEDS BUT NOT EQUIVALENT TO}"),  # ‘⋩’
    MacroTextSpec("ntriangleleft", "\N{NOT NORMAL SUBGROUP OF}"),  # ‘⋪’
    MacroTextSpec("ntriangleright", "\N{DOES NOT CONTAIN AS NORMAL SUBGROUP}"),  # ‘⋫’
    MacroTextSpec("ntrianglelefteq", "\N{NOT NORMAL SUBGROUP OF OR EQUAL TO}"),  # ‘⋬’
    MacroTextSpec(
        "ntrianglerighteq", "\N{DOES NOT CONTAIN AS NORMAL SUBGROUP OR EQUAL}"
    ),  # ‘⋭’
    MacroTextSpec("vdots", "\N{VERTICAL ELLIPSIS}"),  # ‘⋮’
    MacroTextSpec("upslopeellipsis", "\N{UP RIGHT DIAGONAL ELLIPSIS}"),  # ‘⋰’
    MacroTextSpec("downslopeellipsis", "\N{DOWN RIGHT DIAGONAL ELLIPSIS}"),  # ‘⋱’
    MacroTextSpec("barwedge", "\N{PROJECTIVE}"),  # ‘⌅’
    MacroTextSpec("varperspcorrespond", "\N{PERSPECTIVE}"),  # ‘⌆’
    MacroTextSpec("lceil", "\N{LEFT CEILING}"),  # ‘⌈’
    MacroTextSpec("rceil", "\N{RIGHT CEILING}"),  # ‘⌉’
    MacroTextSpec("lfloor", "\N{LEFT FLOOR}"),  # ‘⌊’
    MacroTextSpec("rfloor", "\N{RIGHT FLOOR}"),  # ‘⌋’
    MacroTextSpec("recorder", "\N{TELEPHONE RECORDER}"),  # ‘⌕’
    MacroTextSpec("ulcorner", "\N{TOP LEFT CORNER}"),  # ‘⌜’
    MacroTextSpec("urcorner", "\N{TOP RIGHT CORNER}"),  # ‘⌝’
    MacroTextSpec("llcorner", "\N{BOTTOM LEFT CORNER}"),  # ‘⌞’
    MacroTextSpec("lrcorner", "\N{BOTTOM RIGHT CORNER}"),  # ‘⌟’
    MacroTextSpec("frown", "\N{FROWN}"),  # ‘⌢’
    MacroTextSpec("smile", "\N{SMILE}"),  # ‘⌣’
    MacroTextSpec(
        "lmoustache", "\N{UPPER LEFT OR LOWER RIGHT CURLY BRACKET SECTION}"
    ),  # ‘⎰’
    MacroTextSpec(
        "rmoustache", "\N{UPPER RIGHT OR LOWER LEFT CURLY BRACKET SECTION}"
    ),  # ‘⎱’
    MacroTextSpec("textvisiblespace", "\N{OPEN BOX}"),  # ‘␣’
    MacroTextSpec("circledS", "\N{CIRCLED LATIN CAPITAL LETTER S}"),  # ‘Ⓢ’
    MacroTextSpec(
        "diagup", "\N{BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT}"
    ),  # ‘╱’
    MacroTextSpec("square", "\N{WHITE SQUARE}"),  # ‘□’
    MacroTextSpec("blacksquare", "\N{BLACK SMALL SQUARE}"),  # ‘▪’
    MacroTextSpec("bigtriangleup", "\N{WHITE UP-POINTING TRIANGLE}"),  # ‘△’
    MacroTextSpec("blacktriangle", "\N{BLACK UP-POINTING SMALL TRIANGLE}"),  # ‘▴’
    MacroTextSpec("vartriangle", "\N{WHITE UP-POINTING SMALL TRIANGLE}"),  # ‘▵’
    MacroTextSpec(
        "blacktriangleright", "\N{BLACK RIGHT-POINTING SMALL TRIANGLE}"
    ),  # ‘▸’
    MacroTextSpec("triangleright", "\N{WHITE RIGHT-POINTING SMALL TRIANGLE}"),  # ‘▹’
    MacroTextSpec("bigtriangledown", "\N{WHITE DOWN-POINTING TRIANGLE}"),  # ‘▽’
    MacroTextSpec("blacktriangledown", "\N{BLACK DOWN-POINTING SMALL TRIANGLE}"),  # ‘▾’
    MacroTextSpec("triangledown", "\N{WHITE DOWN-POINTING SMALL TRIANGLE}"),  # ‘▿’
    MacroTextSpec("blacktriangleleft", "\N{BLACK LEFT-POINTING SMALL TRIANGLE}"),  # ‘◂’
    MacroTextSpec("triangleleft", "\N{WHITE LEFT-POINTING SMALL TRIANGLE}"),  # ‘◃’
    MacroTextSpec("lozenge", "\N{LOZENGE}"),  # ‘◊’
    MacroTextSpec("bigcirc", "\N{WHITE CIRCLE}"),  # ‘○’
    MacroTextSpec("bigcirc", "\N{LARGE CIRCLE}"),  # ‘◯’
    MacroTextSpec("rightmoon", "\N{LAST QUARTER MOON}"),  # ‘☾’
    MacroTextSpec("mercury", "\N{MERCURY}"),  # ‘☿’
    MacroTextSpec("venus", "\N{FEMALE SIGN}"),  # ‘♀’
    MacroTextSpec("male", "\N{MALE SIGN}"),  # ‘♂’
    MacroTextSpec("jupiter", "\N{JUPITER}"),  # ‘♃’
    MacroTextSpec("saturn", "\N{SATURN}"),  # ‘♄’
    MacroTextSpec("uranus", "\N{URANUS}"),  # ‘♅’
    MacroTextSpec("neptune", "\N{NEPTUNE}"),  # ‘♆’
    MacroTextSpec("pluto", "\N{PLUTO}"),  # ‘♇’
    MacroTextSpec("aries", "\N{ARIES}"),  # ‘♈’
    MacroTextSpec("taurus", "\N{TAURUS}"),  # ‘♉’
    MacroTextSpec("gemini", "\N{GEMINI}"),  # ‘♊’
    MacroTextSpec("cancer", "\N{CANCER}"),  # ‘♋’
    MacroTextSpec("leo", "\N{LEO}"),  # ‘♌’
    MacroTextSpec("virgo", "\N{VIRGO}"),  # ‘♍’
    MacroTextSpec("libra", "\N{LIBRA}"),  # ‘♎’
    MacroTextSpec("scorpio", "\N{SCORPIUS}"),  # ‘♏’
    MacroTextSpec("sagittarius", "\N{SAGITTARIUS}"),  # ‘♐’
    MacroTextSpec("capricornus", "\N{CAPRICORN}"),  # ‘♑’
    MacroTextSpec("aquarius", "\N{AQUARIUS}"),  # ‘♒’
    MacroTextSpec("pisces", "\N{PISCES}"),  # ‘♓’
    MacroTextSpec("diamond", "\N{WHITE DIAMOND SUIT}"),  # ‘♢’
    MacroTextSpec("quarternote", "\N{QUARTER NOTE}"),  # ‘♩’
    MacroTextSpec("eighthnote", "\N{EIGHTH NOTE}"),  # ‘♪’
    MacroTextSpec("flat", "\N{MUSIC FLAT SIGN}"),  # ‘♭’
    MacroTextSpec("natural", "\N{MUSIC NATURAL SIGN}"),  # ‘♮’
    MacroTextSpec("sharp", "\N{MUSIC SHARP SIGN}"),  # ‘♯’
    MacroTextSpec("longleftrightarrow", "\N{LONG LEFT RIGHT ARROW}"),  # ‘⟷’
    MacroTextSpec("Longleftarrow", "\N{LONG LEFTWARDS DOUBLE ARROW}"),  # ‘⟸’
    MacroTextSpec("Longrightarrow", "\N{LONG RIGHTWARDS DOUBLE ARROW}"),  # ‘⟹’
    MacroTextSpec("Longleftrightarrow", "\N{LONG LEFT RIGHT DOUBLE ARROW}"),  # ‘⟺’
    MacroTextSpec("longmapsto", "\N{LONG RIGHTWARDS ARROW FROM BAR}"),  # ‘⟼’
    MacroTextSpec("UpArrowBar", "\N{UPWARDS ARROW TO BAR}"),  # ‘⤒’
    MacroTextSpec("DownArrowBar", "\N{DOWNWARDS ARROW TO BAR}"),  # ‘⤓’
    MacroTextSpec("LeftRightVector", "\N{LEFT BARB UP RIGHT BARB UP HARPOON}"),  # ‘⥎’
    MacroTextSpec(
        "RightUpDownVector", "\N{UP BARB RIGHT DOWN BARB RIGHT HARPOON}"
    ),  # ‘⥏’
    MacroTextSpec(
        "DownLeftRightVector", "\N{LEFT BARB DOWN RIGHT BARB DOWN HARPOON}"
    ),  # ‘⥐’
    MacroTextSpec("LeftUpDownVector", "\N{UP BARB LEFT DOWN BARB LEFT HARPOON}"),  # ‘⥑’
    MacroTextSpec("LeftVectorBar", "\N{LEFTWARDS HARPOON WITH BARB UP TO BAR}"),  # ‘⥒’
    MacroTextSpec(
        "RightVectorBar", "\N{RIGHTWARDS HARPOON WITH BARB UP TO BAR}"
    ),  # ‘⥓’
    MacroTextSpec(
        "RightUpVectorBar", "\N{UPWARDS HARPOON WITH BARB RIGHT TO BAR}"
    ),  # ‘⥔’
    MacroTextSpec(
        "RightDownVectorBar", "\N{DOWNWARDS HARPOON WITH BARB RIGHT TO BAR}"
    ),  # ‘⥕’
    MacroTextSpec(
        "DownLeftVectorBar", "\N{LEFTWARDS HARPOON WITH BARB DOWN TO BAR}"
    ),  # ‘⥖’
    MacroTextSpec(
        "DownRightVectorBar", "\N{RIGHTWARDS HARPOON WITH BARB DOWN TO BAR}"
    ),  # ‘⥗’
    MacroTextSpec(
        "LeftUpVectorBar", "\N{UPWARDS HARPOON WITH BARB LEFT TO BAR}"
    ),  # ‘⥘’
    MacroTextSpec(
        "LeftDownVectorBar", "\N{DOWNWARDS HARPOON WITH BARB LEFT TO BAR}"
    ),  # ‘⥙’
    MacroTextSpec(
        "LeftTeeVector", "\N{LEFTWARDS HARPOON WITH BARB UP FROM BAR}"
    ),  # ‘⥚’
    MacroTextSpec(
        "RightTeeVector", "\N{RIGHTWARDS HARPOON WITH BARB UP FROM BAR}"
    ),  # ‘⥛’
    MacroTextSpec(
        "RightUpTeeVector", "\N{UPWARDS HARPOON WITH BARB RIGHT FROM BAR}"
    ),  # ‘⥜’
    MacroTextSpec(
        "RightDownTeeVector", "\N{DOWNWARDS HARPOON WITH BARB RIGHT FROM BAR}"
    ),  # ‘⥝’
    MacroTextSpec(
        "DownLeftTeeVector", "\N{LEFTWARDS HARPOON WITH BARB DOWN FROM BAR}"
    ),  # ‘⥞’
    MacroTextSpec(
        "DownRightTeeVector", "\N{RIGHTWARDS HARPOON WITH BARB DOWN FROM BAR}"
    ),  # ‘⥟’
    MacroTextSpec(
        "LeftUpTeeVector", "\N{UPWARDS HARPOON WITH BARB LEFT FROM BAR}"
    ),  # ‘⥠’
    MacroTextSpec(
        "LeftDownTeeVector", "\N{DOWNWARDS HARPOON WITH BARB LEFT FROM BAR}"
    ),  # ‘⥡’
    MacroTextSpec(
        "UpEquilibrium",
        "\N{UPWARDS HARPOON WITH BARB LEFT BESIDE DOWNWARDS HARPOON WITH BARB RIGHT}",
    ),  # ‘⥮’
    MacroTextSpec(
        "ReverseUpEquilibrium",
        "\N{DOWNWARDS HARPOON WITH BARB LEFT BESIDE UPWARDS HARPOON WITH BARB RIGHT}",
    ),  # ‘⥯’
    MacroTextSpec("RoundImplies", "\N{RIGHT DOUBLE ARROW WITH ROUNDED HEAD}"),  # ‘⥰’
    MacroTextSpec("Angle", "\N{RIGHT ANGLE VARIANT WITH SQUARE}"),  # ‘⦜’
    MacroTextSpec("LeftTriangleBar", "\N{LEFT TRIANGLE BESIDE VERTICAL BAR}"),  # ‘⧏’
    MacroTextSpec("RightTriangleBar", "\N{VERTICAL BAR BESIDE RIGHT TRIANGLE}"),  # ‘⧐’
    MacroTextSpec("blacklozenge", "\N{BLACK LOZENGE}"),  # ‘⧫’
    MacroTextSpec("RuleDelayed", "\N{RULE-DELAYED}"),  # ‘⧴’
    MacroTextSpec("clockoint", "\N{INTEGRAL AVERAGE WITH SLASH}"),  # ‘⨏’
    MacroTextSpec("sqrint", "\N{QUATERNION INTEGRAL OPERATOR}"),  # ‘⨖’
    MacroTextSpec("amalg", "\N{AMALGAMATION OR COPRODUCT}"),  # ‘⨿’
    MacroTextSpec("perspcorrespond", "\N{LOGICAL AND WITH DOUBLE OVERBAR}"),  # ‘⩞’
    MacroTextSpec("Equal", "\N{TWO CONSECUTIVE EQUALS SIGNS}"),  # ‘⩵’
    MacroTextSpec("lessapprox", "\N{LESS-THAN OR APPROXIMATE}"),  # ‘⪅’
    MacroTextSpec("gtrapprox", "\N{GREATER-THAN OR APPROXIMATE}"),  # ‘⪆’
    MacroTextSpec("lneq", "\N{LESS-THAN AND SINGLE-LINE NOT EQUAL TO}"),  # ‘⪇’
    MacroTextSpec("gneq", "\N{GREATER-THAN AND SINGLE-LINE NOT EQUAL TO}"),  # ‘⪈’
    MacroTextSpec("lnapprox", "\N{LESS-THAN AND NOT APPROXIMATE}"),  # ‘⪉’
    MacroTextSpec("gnapprox", "\N{GREATER-THAN AND NOT APPROXIMATE}"),  # ‘⪊’
    MacroTextSpec(
        "lesseqqgtr", "\N{LESS-THAN ABOVE DOUBLE-LINE EQUAL ABOVE GREATER-THAN}"
    ),  # ‘⪋’
    MacroTextSpec(
        "gtreqqless", "\N{GREATER-THAN ABOVE DOUBLE-LINE EQUAL ABOVE LESS-THAN}"
    ),  # ‘⪌’
    MacroTextSpec("eqslantless", "\N{SLANTED EQUAL TO OR LESS-THAN}"),  # ‘⪕’
    MacroTextSpec("eqslantgtr", "\N{SLANTED EQUAL TO OR GREATER-THAN}"),  # ‘⪖’
    MacroTextSpec("NestedLessLess", "\N{DOUBLE NESTED LESS-THAN}"),  # ‘⪡’
    MacroTextSpec("NestedGreaterGreater", "\N{DOUBLE NESTED GREATER-THAN}"),  # ‘⪢’
    MacroTextSpec("precneqq", "\N{PRECEDES ABOVE NOT EQUAL TO}"),  # ‘⪵’
    MacroTextSpec("succneqq", "\N{SUCCEEDS ABOVE NOT EQUAL TO}"),  # ‘⪶’
    MacroTextSpec("precapprox", "\N{PRECEDES ABOVE ALMOST EQUAL TO}"),  # ‘⪷’
    MacroTextSpec("succapprox", "\N{SUCCEEDS ABOVE ALMOST EQUAL TO}"),  # ‘⪸’
    MacroTextSpec("precnapprox", "\N{PRECEDES ABOVE NOT ALMOST EQUAL TO}"),  # ‘⪹’
    MacroTextSpec("succnapprox", "\N{SUCCEEDS ABOVE NOT ALMOST EQUAL TO}"),  # ‘⪺’
    MacroTextSpec("subseteqq", "\N{SUBSET OF ABOVE EQUALS SIGN}"),  # ‘⫅’
    MacroTextSpec("supseteqq", "\N{SUPERSET OF ABOVE EQUALS SIGN}"),  # ‘⫆’
    MacroTextSpec("subsetneqq", "\N{SUBSET OF ABOVE NOT EQUAL TO}"),  # ‘⫋’
    MacroTextSpec("supsetneqq", "\N{SUPERSET OF ABOVE NOT EQUAL TO}"),  # ‘⫌’
    MacroTextSpec("openbracketleft", "\N{LEFT WHITE SQUARE BRACKET}"),  # ‘〚’
    MacroTextSpec("openbracketright", "\N{RIGHT WHITE SQUARE BRACKET}"),  # ‘〛’
]

# ==============================================================================


specs = [
    #
    # CATEGORY: latex-base
    #
    ("latex-base", _latex_specs_base),
    #
    # CATEGORY: latex-approximations
    #
    ("latex-approximations", _latex_specs_approximations),
    #
    # CATEGORY: latex-placeholders
    #
    ("latex-placeholders", _latex_specs_placeholders),
    #
    # CATEGORY: nonascii-specials
    #
    (
        "nonascii-specials",
        {
            "macros": [],
            "environments": [],
            "specials": [
                SpecialsTextSpec("~", "\N{NO-BREAK SPACE}"),
                SpecialsTextSpec("``", "\N{LEFT DOUBLE QUOTATION MARK}"),
                SpecialsTextSpec("''", "\N{RIGHT DOUBLE QUOTATION MARK}"),
                SpecialsTextSpec("--", "\N{EN DASH}"),
                SpecialsTextSpec("---", "\N{EM DASH}"),
                SpecialsTextSpec("!`", "\N{INVERTED EXCLAMATION MARK}"),
                SpecialsTextSpec("?`", "\N{INVERTED QUESTION MARK}"),
            ],
        },
    ),
    #
    # CATEGORY: advanced-symbols
    #
    (
        "advanced-symbols",
        {
            "macros": advanced_symbols_macros,
            "environments": [],
            "specials": [],
        },
    ),
    #
    # CATEGORY: latex-ethuebung
    #
    # expect these to be removed in a future version.  These definitions should
    # be manually included in the applications where they are relevant.
    (
        "latex-ethuebung",
        {
            "macros": [
                MacroTextSpec("exercise", simplify_repl=_format_uebung),
                MacroTextSpec("uebung", simplify_repl=_format_uebung),
                MacroTextSpec("hint", "Hint: %s"),
                MacroTextSpec("hints", "Hints: %s"),
                MacroTextSpec("hinweis", "Hinweis: %s"),
                MacroTextSpec("hinweise", "Hinweise: %s"),
            ],
            "environments": [],
            "specials": [],
        },
    ),
    #
    # CATEGORY: nonstandard-qit
    #
    # expect these to be removed in a future version.  These definitions should
    # be manually included in the applications where they are relevant.
    (
        "nonstandard-qit",
        {
            "environments": [],
            "specials": [],
            "macros": [
                # we use these conventions as Identity operator (\mathbbm{1})
                MacroTextSpec("id", "\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}"),
                MacroTextSpec("Ident", "\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}"),
            ],
        },
    ),
]


def _greekletters(letterlist):
    for l in letterlist:
        ucharname = l.upper()
        if ucharname == "LAMBDA":
            ucharname = "LAMDA"
        smallname = "GREEK SMALL LETTER " + ucharname
        if ucharname == "EPSILON":
            smallname = "GREEK LUNATE EPSILON SYMBOL"
        if ucharname == "PHI":
            smallname = "GREEK PHI SYMBOL"
        _latex_specs_base["macros"].append(
            MacroTextSpec(l, unicodedata.lookup(smallname))
        )
        _latex_specs_base["macros"].append(
            MacroTextSpec(
                l[0].upper() + l[1:],
                unicodedata.lookup("GREEK CAPITAL LETTER " + ucharname),
            )
        )
        # up-greek version (from packages such as upgreek or newtxmath)
        _latex_specs_base["macros"].append(
            MacroTextSpec("up" + l, unicodedata.lookup(smallname))
        )
        _latex_specs_base["macros"].append(
            MacroTextSpec(
                "Up" + l, unicodedata.lookup("GREEK CAPITAL LETTER " + ucharname)
            )
        )


_greekletters(
    (
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
        "iota",
        "kappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "omicron",
        "pi",
        "rho",
        "sigma",
        "tau",
        "upsilon",
        "phi",
        "chi",
        "psi",
        "omega",
    )
)
_latex_specs_base["macros"] += [
    MacroTextSpec("varepsilon", "\N{GREEK SMALL LETTER EPSILON}"),
    MacroTextSpec("vartheta", "\N{GREEK THETA SYMBOL}"),
    MacroTextSpec("varpi", "\N{GREEK PI SYMBOL}"),
    MacroTextSpec("varrho", "\N{GREEK RHO SYMBOL}"),
    MacroTextSpec("varsigma", "\N{GREEK SMALL LETTER FINAL SIGMA}"),
    MacroTextSpec("varphi", "\N{GREEK SMALL LETTER PHI}"),
    # up-greek version
    MacroTextSpec("upvarepsilon", "\N{GREEK SMALL LETTER EPSILON}"),
    MacroTextSpec("upvartheta", "\N{GREEK THETA SYMBOL}"),
    MacroTextSpec("upvarpi", "\N{GREEK PI SYMBOL}"),
    MacroTextSpec("upvarrho", "\N{GREEK RHO SYMBOL}"),
    MacroTextSpec("upvarsigma", "\N{GREEK SMALL LETTER FINAL SIGMA}"),
    MacroTextSpec("upvarphi", "\N{GREEK SMALL LETTER PHI}"),
]


unicode_accents_list = (
    # see http://en.wikibooks.org/wiki/LaTeX/Special_Characters for a list
    ("'", "\N{COMBINING ACUTE ACCENT}"),
    ("`", "\N{COMBINING GRAVE ACCENT}"),
    ('"', "\N{COMBINING DIAERESIS}"),
    ("c", "\N{COMBINING CEDILLA}"),
    ("^", "\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("~", "\N{COMBINING TILDE}"),
    ("H", "\N{COMBINING DOUBLE ACUTE ACCENT}"),
    ("k", "\N{COMBINING OGONEK}"),
    ("=", "\N{COMBINING MACRON}"),
    ("b", "\N{COMBINING MACRON BELOW}"),
    (".", "\N{COMBINING DOT ABOVE}"),
    ("d", "\N{COMBINING DOT BELOW}"),
    ("r", "\N{COMBINING RING ABOVE}"),
    ("u", "\N{COMBINING BREVE}"),
    ("v", "\N{COMBINING CARON}"),
    ("vec", "\N{COMBINING RIGHT ARROW ABOVE}"),
    ("dot", "\N{COMBINING DOT ABOVE}"),
    ("hat", "\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("check", "\N{COMBINING CARON}"),
    ("breve", "\N{COMBINING BREVE}"),
    ("acute", "\N{COMBINING ACUTE ACCENT}"),
    ("grave", "\N{COMBINING GRAVE ACCENT}"),
    ("tilde", "\N{COMBINING TILDE}"),
    ("bar", "\N{COMBINING OVERLINE}"),
    ("ddot", "\N{COMBINING DIAERESIS}"),
    ("not", "\N{COMBINING LONG SOLIDUS OVERLAY}"),
)


def make_accented_char(node, combining, l2tobj):
    if node.nodeargs and len(node.nodeargs):
        nodearg = node.nodeargs[0]
        c = l2tobj.nodelist_to_text([nodearg]).strip()
    else:
        c = " "

    def getaccented(ch, combining):
        ch = unicode(ch)
        combining = unicode(combining)
        if ch == "\N{LATIN SMALL LETTER DOTLESS I}":
            ch = "i"
        if ch == "\N{LATIN SMALL LETTER DOTLESS J}":
            ch = "j"
        # print u"Accenting %s with %s"%(ch, combining) # this causes UnicdeDecodeError!!!
        return unicodedata.normalize("NFC", unicode(ch) + combining)

    return "".join([getaccented(ch, combining) for ch in c])


for u in unicode_accents_list:
    (mname, mcombining) = u
    _latex_specs_base["macros"].append(
        MacroTextSpec(
            mname, lambda x, l2tobj, c=mcombining: make_accented_char(x, c, l2tobj)
        )
    )

# specs structure now complete
