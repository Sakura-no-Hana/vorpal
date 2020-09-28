from io import open
import time
from modulefinder import ModuleFinder

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

parser = Lark.open("vorpal.lark", parser="lalr", **kwargs)


def _read(fn, *args):
    kwargs = {"encoding": "iso-8859-1"}
    with open(fn, *args, **kwargs) as f:
        return f.read()


def parse(path: str):
    return parser.parse(_read(path) + "\n")


if __name__ == "__main__":
    finder = ModuleFinder()
    finder.run_script("test.py")

    print("Loaded modules:")
    for name, mod in finder.modules.items():
        print("%s: " % name, end="")
        print(list(mod.globalnames.keys()))
