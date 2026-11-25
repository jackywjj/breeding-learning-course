#show: doc => {
  let ink = rgb("#302527")
  let muted = rgb("#705858")
  let accent = rgb("#982f24")

  set document(title: [$title$], author: "$for(by-author)$$it.name.literal$$sep$, $endfor$")
  set text(font: ("Libertinus Serif", "$mainfont$"), size: $fontsize$, lang: "$lang$", fill: ink)
  set par(leading: 0.82em, spacing: 1.06em, justify: false)
  show link: set text(fill: accent)
  show heading: set text(font: ("$mainfont$",), fill: accent, weight: "bold")
  show heading.where(level: 1): set text(size: 19pt)
  show heading.where(level: 1): set block(above: 1.2em, below: 0.65em)
  show heading.where(level: 2): set text(size: 14pt)
  show heading.where(level: 3): set text(size: 12pt)
  show figure.caption: set text(size: 9pt, fill: muted)
  show raw.where(block: true): set text(size: 9pt)

  page(fill: rgb("#fff9ef"), numbering: none, margin: (x: 22mm, y: 24mm))[
    #v(0.55fr)
    #line(length: 44pt, stroke: 3pt + accent)
    #v(13pt)
    #text(font: ("$mainfont$",), size: 36pt, weight: "bold", fill: accent)[$title$]
    #v(5pt)
    #text(size: 14pt, fill: muted)[$subtitle$]
    #v(24pt)
    #image("_extensions/course/cover-art.png", width: 100%,
      alt: "代码、系谱学习笔记与种猪的砖红插画 / Brick-red illustration of code, a pedigree notebook, and a pig")
    #v(17pt)
    #text(font: ("$mainfont$",), size: 12pt, weight: "bold")[$for(by-author)$$it.name.literal$$sep$, $endfor$]
    #v(1fr)
    #line(length: 100%, stroke: 0.55pt + rgb("#d9b0a6"))
  ]
  $if(toc)$
  block(above: 0pt, below: 16pt, outline(title: [$toc-title$], depth: $toc-depth$))
  $endif$
  doc
}
