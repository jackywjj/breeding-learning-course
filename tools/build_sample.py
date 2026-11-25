#!/usr/bin/env python3
"""Render local samples or the complete PDF using Quarto and Typst."""

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CHAPTERS = ("01-0", "03-0", "07-0", "07-2")
PAGE_NUMBER = re.compile(r"^(\d{2}-\d+)-")
CHAPTER_LINK = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\s]+\.md)(#[^)\s]*)?\)")
IMAGE_LINK = re.compile(r"!\[[^\]\n]*\]\((images/[^)\s]+)\)")
SAMPLE_NOTE = (
    "本地样章包含前言、第 01、03、07 章和混合模型方程详读。  \n"
    "This local preview contains the preface, Chapters 01, 03, and 07, "
    "and the detailed reading on mixed model equations.\n\n"
)


def chapter_route(source: str) -> str:
    if source == "README.md":
        return "index.qmd"
    if source == "00-目录.md":
        return "contents.qmd"
    match = PAGE_NUMBER.match(source)
    if not match or Path(source).name != source:
        raise ValueError(f"Unrecognized chapter path in SUMMARY.md: {source}")
    return f"chapter-{match[1]}.qmd"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quarto", default="quarto", help="path to the Quarto executable")
    parser.add_argument("--font", default="Hiragino Sans GB", help="installed CJK font for PDF")
    parser.add_argument("--full-pdf", action="store_true", help="render the complete PDF in SUMMARY.md order")
    args = parser.parse_args()
    quarto = shutil.which(args.quarto)
    if quarto is None:
        parser.error("Quarto is required. Provide its path with --quarto.")

    summary = (ROOT / "SUMMARY.md").read_text(encoding="utf-8")
    pages = [unquote(path) for path in re.findall(r"^\s*\* \[[^\]]+\]\(([^)]+\.md)\)", summary, re.MULTILINE)]
    if args.full_pdf:
        selected = {page: chapter_route(page) for page in pages}
        if len(pages) != len(set(selected.values())) or next(iter(selected), None) != "README.md":
            parser.error("SUMMARY.md must start with README.md and contain unique chapter paths.")
    else:
        selected = {"README.md": "index.qmd"}
        for chapter in SAMPLE_CHAPTERS:
            matches = [name for name in pages if name.startswith(f"{chapter}-")]
            if len(matches) != 1:
                parser.error(f"Expected one SUMMARY.md entry for {chapter}; got {matches}")
            selected[matches[0]] = chapter_route(matches[0])

    output_parent = ROOT / "_sample"
    output_parent.mkdir(exist_ok=True)
    project = Path(mkdtemp(prefix="preview-", dir=output_parent))
    (project / "images").mkdir()

    def rewrite_chapter_link(match: re.Match) -> str:
        label, target, anchor = match.groups()
        target = unquote(target)
        if target in selected:
            return f"[{label}]({selected[target]}{anchor or ''})"
        return label if target in pages else match[0]

    for source, output in selected.items():
        manuscript = (ROOT / source).read_text(encoding="utf-8")
        for match in IMAGE_LINK.findall(manuscript):
            image = Path(unquote(match))
            shutil.copyfile(ROOT / image, project / image)
        manuscript = CHAPTER_LINK.sub(rewrite_chapter_link, manuscript)
        manuscript = re.sub(r"^```mermaid[ \t]*$", "```{mermaid}", manuscript, flags=re.MULTILINE)
        if source == "README.md":
            note = "" if args.full_pdf else SAMPLE_NOTE
            manuscript = re.sub(r"^# [^\n]+\n\n## 前言 / Preface\n\n", "# 前言 / Preface\n\n" + note, manuscript, count=1)
        manuscript = re.sub(r"^# ([^\n]+)", rf"# \1 {{#{Path(output).stem}}}", manuscript, count=1)
        (project / output).write_text(manuscript, encoding="utf-8")

    chapters = "\n".join(f"    - {page}" for page in selected.values())
    font = args.font.replace("'", "''")
    subtitle = "Learning Animal Breeding the Way I Build Software"
    output_name = "breeding-learning-course"
    toc_title = "全书目录 / Contents"
    if not args.full_pdf:
        subtitle += " · 样章 / Sample"
        output_name += "-sample"
        toc_title = "样章目录 / Sample contents"
    config = f"""project:
  type: book

book:
  title: "我用做软件的方式学育种"
  subtitle: "{subtitle}"
  author: "玩 AI 的杰克"
  output-file: {output_name}
  chapters:
{chapters}

lang: zh
number-sections: false
execute:
  enabled: false
filters:
  - quarto
  - offline-sample.lua

format:
  html:
    toc: true
    html-math-method: mathml
    css: sample.css
  course-typst:
    toc: true
    toc-depth: 1
    toc-title: "{toc_title}"
    papersize: a4
    margin:
      x: 22mm
      top: 20mm
      bottom: 22mm
    page-numbering: '1'
    mainfont: '{font}'
    fontsize: 11pt
  epub:
    toc: true
    toc-depth: 2
"""
    for asset in ("offline-sample.lua", "sample.css"):
        shutil.copyfile(ROOT / "tools" / asset, project / asset)
    shutil.copytree(ROOT / "tools" / "_extensions" / "course", project / "_extensions" / "course")
    (project / "_quarto.yml").write_text(config, encoding="utf-8")
    print(f"Building in {project}", flush=True)
    subprocess.run([quarto, "render", "--to", "course-typst" if args.full_pdf else "all"], cwd=project, check=True)
    print(f"Preview files: {project / '_book'}")


if __name__ == "__main__":
    main()
