
.PHONY: doc clean clean_pdf clean_all user_guide

.DEFAULT_GOAL := doc

doc: user_guide clean

# executed twice for TOC
user_guide:
	pdflatex Davai_User_Guide.tex
	pdflatex Davai_User_Guide.tex
	mv Davai_User_Guide.pdf ../pdf/.

clean_all: clean clean_pdf

clean:
	find . -name "*.aux" -print0 | xargs -0r rm
	find . -name "*.log" -print0 | xargs -0r rm
	find . -name "*.toc" -print0 | xargs -0r rm
	find . -name "*.out" -print0 | xargs -0r rm
	find . -name "*.synctex.gz" -print0 | xargs -0r rm

clean_pdf:
	find . -name "*.pdf" -print0 | xargs -0r rm
