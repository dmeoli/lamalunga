STY     = $(wildcard *.sty)
TEXMF   = $(shell kpsewhich -var-value TEXMFHOME)
DEST    = $(TEXMF)/tex/latex/lamalunga
LATEXMK = TEXINPUTS=$(CURDIR)//: latexmk -lualatex -interaction=nonstopmode

.PHONY: all demo gallery install uninstall clean

all: demo

demo:
	cd demo && $(LATEXMK) lamalunga-demo.tex lamalunga-demo-dark.tex

gallery:
	python3 doc/gallery/build.py

install:
	mkdir -p $(DEST)
	cp $(STY) $(DEST)
	-mktexlsr $(TEXMF) 2>/dev/null

uninstall:
	rm -rf $(DEST)

clean:
	cd demo && latexmk -c lamalunga-demo.tex lamalunga-demo-dark.tex
	rm -f demo/*.nav demo/*.snm demo/*.vrb
