from antlr4 import *
from grammar.BaLangLexer import BaLangLexer
from grammar.BaLangParser import BaLangParser
from grammar.IRgen import *

f = open("test_example/test.grammar", "r")
txt = f.read()
lexer = BaLangLexer(InputStream(txt))
stream = CommonTokenStream(lexer)
parser = BaLangParser(stream)
tree = parser.program()
gen = IRgen()
generatedIR = gen.root(tree)

print(str(generatedIR))