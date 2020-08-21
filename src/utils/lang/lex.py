from io import open
import time

from lark import Lark
from lark.indenter import Indenter


class PythonIndenter(Indenter):
    NL_type = "_NEWLINE"
    OPEN_PAREN_types = ["LPAR", "LSQB", "LBRACE"]
    CLOSE_PAREN_types = ["RPAR", "RSQB", "RBRACE"]
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


kwargs = dict(rel_to=__file__, postlex=PythonIndenter(), start="start")

chosen_parser = Lark.open("vorpal.lark", parser="lalr", **kwargs)


def _read(fn, *args):
    kwargs = {"encoding": "iso-8859-1"}
    with open(fn, *args, **kwargs) as f:
        return f.read()


def test_python_lib(path: str):
    start = time.time()
    print(chosen_parser.parse(_read(path) + "\n").pretty())
    end = time.time()
    print("test_python_lib (%d files), time: %s secs" % (len(files), end - start))
