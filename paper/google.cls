% Google Research / Google Cloud AI Research Paper Class (adapted from google.cls in Harness^2 / OO-Harness)
% Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{google}

\RequirePackage{xifthen}
\newboolean{nonumbering}
\newboolean{address}
\newboolean{copyright}
\newboolean{confidential}
\DeclareOption{nonumbering}{\setboolean{nonumbering}{true}}
\DeclareOption{address}{\setboolean{address}{true}}
\DeclareOption{copyright}{\setboolean{copyright}{true}}
\DeclareOption{confidential}{\setboolean{confidential}{true}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}}
\ProcessOptions
\LoadClass{extarticle}

\AtEndOfClass{\RequirePackage[tracking=smallcaps]{microtype}}
\RequirePackage[utf8]{inputenc}
\RequirePackage[english]{babel}
\RequirePackage{amsthm, amsmath, amsfonts, amssymb}
\RequirePackage{cmap}
\RequirePackage[T1]{fontenc}
\RequirePackage{url}
\RequirePackage[colorlinks=true, allcolors=blue]{hyperref}
\RequirePackage{pifont}
\RequirePackage[dvipsnames]{xcolor}
\RequirePackage{textcomp}
\RequirePackage[overload]{textcase}
\RequirePackage{graphicx}
\RequirePackage{colortbl}
\RequirePackage{booktabs}
\RequirePackage{changepage}
\RequirePackage{enumitem}
\RequirePackage{tabularx}
\RequirePackage{datetime}
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
\setlist[itemize]{noitemsep}
\setlist[enumerate]{noitemsep}
\RequirePackage[explicit]{titlesec}
\RequirePackage{bibentry}
\RequirePackage{mdframed}
\RequirePackage{caption}
\RequirePackage{needspace}
\RequirePackage{soul}
\RequirePackage{kvoptions}

\IfFileExists{XCharter.sty}{%
  \RequirePackage{XCharter}
  \RequirePackage[xcharter,bigdelims,vvarbb]{newtxmath}
}{%
  \RequirePackage{charter}
  \RequirePackage{lmodern}
}

\RequirePackage[left=2.2cm,right=2.2cm,top=2.8cm,bottom=2.8cm,headheight=36pt,headsep=18pt,a4paper]{geometry}
\setlength{\columnsep}{15pt}
\setlength{\parskip}{0.5\baselineskip}
\setlength{\parindent}{0pt}

\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\headerfont}{\normalfont\sffamily\fontsize{8}{10}\selectfont}
\newcommand{\titlefont}{\color{black}\normalfont\bfseries\fontsize{19}{22}\selectfont}
\newcommand{\datesfont}{\normalfont\sffamily\itshape\fontsize{8}{10}\selectfont}
\newcommand\urlheaderfont{\color{blue}\fontsize{8}{10}\selectfont}
\newcommand{\absfont}{\bfseries\linespread{1.18}\fontsize{10}{12}\selectfont}
\newcommand{\keywordstitlefont}{\bfseries\linespread{1.2}\fontsize{8}{10}\selectfont}
\newcommand{\keywordsfont}{\itshape\linespread{1.2}\fontsize{11}{12}\selectfont}
\newcommand{\copyrightfont}{\normalfont\fontsize{7}{9}\selectfont}
\newcommand{\footerfont}{\color{black}\normalfont\fontsize{8}{10}\selectfont}
\newcommand{\subjectfont}{\color{white}\bfseries\fontsize{10}{12}\selectfont}
\newcommand{\headingfont}{\color{black}\bfseries\fontsize{13}{14}\selectfont}

\newcommand{\keywords}[1]{\def\@keywords{#1}}
\newcommand{\correspondingauthor}[1]{\gdef\google@corr{#1}}
\def\google@corr{}
\newtoks\paperurl
\newtoks\reportnumber

\newdateformat{monthyeardate}{\THEYEAR-\twodigit{\THEMONTH}-\twodigit{\THEDAY}}

\setcounter{secnumdepth}{3}
\ifthenelse{\boolean{nonumbering}}{\setcounter{secnumdepth}{0}}{}

\RequirePackage{authblk}
\setcounter{Maxaffil}{0}
\setlength{\affilsep}{0.2em}
\renewcommand\Authfont{\normalfont\bfseries\fontsize{9.5}{13}\selectfont}
\renewcommand\Affilfont{\normalfont\fontsize{8.5}{10.5}\selectfont}
\makeatletter
\renewcommand\AB@affilsepx{, \protect\Affilfont}
\makeatother
\renewcommand\Authands{ and }
\newcommand{\internalonly}{\hl{Confidential---Do not share or forward externally}}
\newcommand{\copyrightext}{\footerfont \textcopyright\, \the\year{} Google. All rights reserved}

\newcommand{\pafullname}{Google}
\def\@selectedlogo{1}
\newcommand{\uselogo}[1]{\gdef\@selectedlogo{1}}

\pagestyle{fancy}
\makeatletter
\fancypagestyle{firststyle}{
  \fancyhead[L]{
    \includegraphics[height=18pt]{assets/logo_Google_FullColor.png}
  }
  \fancyhead[R]{
    \ifdefined\paperurl
    \if\relax\the\paperurl\relax \else
      \href{\the\paperurl}{\urlheaderfont \itshape \the\paperurl}\\ \fi
    \else
    \fi
    {\footerfont\itshape\monthyeardate\today}
  }
  \fancyhead[C]{}
  \fancyfoot[L]{
    \ifx\google@corr\@empty\else
      \footerfont\itshape Corresponding author(s): \google@corr \\
    \fi
    \ifthenelse{\boolean{copyright}}{\copyrightext}{}
  }
  \fancyfoot[R]{}
  \fancyfoot[C]{}
}
\makeatother

\fancyhead[L,R]{}
\makeatletter
\fancyhead[C]{\footerfont Dual-Loop Specification-Driven Software Engineering}
\makeatother
\fancyfoot[C]{}
\fancyfoot[L]{}
\fancyfoot[R]{\footerfont \thepage}

\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{1pt}
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{gray}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{gray}{\DefaultFootRule}}

\renewenvironment{abstract}
{\par\noindent\\ \ignorespaces}
{\par\bigskip}

\addto{\captionsenglish}{\renewcommand{\refname}{References}}

\def\xabstract{abstract}
\long\def\abstract#1\end#2{\def\two{#2}\ifx\two\xabstract
  \long\gdef\theabstract{\ignorespaces#1}
  \def\go{\end{abstract}}\else
\typeout{PLEASE DO NOT USE ANY \string\begin\space \string\end COMMANDS WITHIN ABSTRACT}#1\end{#2}
\gdef\theabstract{BADLY FORMED ABSTRACT}\let\go\relax\fi
\go}

\makeatletter
\newcommand{\abscontent}{
  \noindent
  \parbox{\dimexpr\linewidth}{\absfont \theabstract}
  \@ifundefined{@keywords}{}{
    \vskip1em \noindent \keywordsfont Keywords: \@keywords}
}

\renewcommand{\maketitle}{\bgroup\setlength{\parindent}{0pt}
  \begin{adjustwidth}{0pt}{12pt}
    \begin{flushleft}
      {
        {\raggedright \titlefont \@title\par}%
        \ifnum\value{authors}>0
          \vskip10pt
          {\raggedright \@author\par}
          \vskip16pt%
        \else
          \vskip24pt%
        \fi
      }%
    \end{flushleft}
  \end{adjustwidth}
  \egroup
  {%
    {\abscontent}
  }%
  \vskip10pt
  \thispagestyle{firststyle}
}%
\makeatother

\titleformat{\section}
{\large\bfseries\headingfont}
{\thesection.}
{0.5em}
{#1}
[]
\titleformat{name=\section,numberless}
{\large\bfseries\headingfont}
{}
{0em}
{#1}
[]
\titleformat{\subsection}
{\bfseries}
{\thesubsection.}
{0.5em}
{#1}
[]
\titleformat{\subsubsection}
{\bfseries\itshape}
{\thesubsubsection.}
{0.5em}
{#1}
[]

\titlespacing*{\section}{0pc}{2.6ex plus3pt minus2pt}{4pt}
\titlespacing*{\subsection}{0pc}{2.2ex plus2pt minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{1.8ex plus2pt minus1pt}{2pt}

\captionsetup{labelfont={bf},
labelsep=colon,
figurename=Figure,
tablename=Table,
font=small,
skip=6pt,
singlelinecheck=off
}
