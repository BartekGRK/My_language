all:
	java -Xmx500M -cp "/usr/local/lib/antlr-4.9.2-complete.jar:$CLASSPATH" org.antlr.v4.Tool -listener -visitor -Dlanguage=Python3 grammar/BaLang.g4

test:
	python3 main.py > kod.ll
	clang kod.ll
	./a.out