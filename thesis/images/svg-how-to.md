1. Draw diagram in draw.io

  a) No text wrap
  b) No text formatting

2. Export as SVG

3. Import SVG directly in LaTeX via Inkscape-pdf_tex-Export
```tex
\usepackage{import}
\graphicspath{{images/}}
\newcommand{\executeiffilenewer}[3]{%
  \ifnum\pdfstrcmp{\pdffilemoddate{#1}}%
  {\pdffilemoddate{#2}}>0%
  {\immediate\write18{#3}}\fi%
} 
\newcommand{\includesvg}[1]{%
  \executeiffilenewer{#1.svg}{#1.pdf}%
  {inkscape -z -D --file=#1.svg %
    --export-pdf=#1.pdf --export-dpi=72 --export-latex}%
  \input{#1.pdf_tex}%
}
```

Load

```tex
\begin{figure}[ht]
  \centering
  \def\svgwidth{0.9\textwidth}
  \textsf{
    \includesvg{images/architecture}
  } % omit .svg
  \caption{Verteilte Architektur}	
  \label{fig:architecture}
\end{figure}
