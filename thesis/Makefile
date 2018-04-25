# Install python-pygments

.PHONY: thesis.pdf presentation.pdf all clean

all: thesis.pdf presentation.pdf

# -pdf tells latexmk to generate PDF directly (instead of DVI).
# -pdflatex="" tells latexmk to call a specific backend with specific options.
# -use-make tells latexmk to call make for generating missing files.
# -shell-escape is used for Pygments code highlighting

# -interaction=nonstopmode keeps the pdflatex backend from stopping at a
# missing file reference and interactively asking you for an alternative.

thesis.pdf: thesis.tex
	latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode -shell-escape" -use-make thesis.tex

# we need xelatex for the custom HPI font NeoSans
presentation.pdf: presentation.tex
	latexmk -pdf -xelatex -latexoption="-shell-escape" -use-make presentation.tex

clean:
	latexmk -CA
