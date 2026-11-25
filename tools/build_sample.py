#!/usr/bin/env python3
"""Render local HTML, PDF, and EPUB samples using Quarto and Typst."""

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CHAPTERS = ("01-0", "03-0", "07-0", "07-2")
CHAPTER_LINK = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\s]+\.md)(#[^)\s]*)?\)")
IMAGE_LINK = re.compile(r"!\[[^\]\n]*\]\((images/[^)\s]+)\)")
SAMPLE_NOTE = (
    "本地样章包含前言、第 01、03、07 章和混合模型方程详读。  \n"
    "This local preview contains the preface, Chapters 01, 03, and 07, "
    "and the detailed reading on mixed model equations.\n\n"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quarto", default="quarto", help="path to the Quarto executable")
    parser.add_argument("--font", default="Hiragino Sans GB", help="installed CJK font for PDF")
    args = parser.parse_args()
    quarto = shutil.which(args.quarto)
    if quarto is None:
        parser.error("Quarto is required. Provide its path with --quarto.")

    summary = (ROOT / "SUMMARY.md").read_text(encoding="utf-8")
    pages = set(re.findall(r"^\s*\* \[[^\]]+\]\(([^)]+\.md)\)", summary, re.MULTILINE))
    sample = {"README.md": "index.qmd"}
    for chapter in SAMPLE_CHAPTERS:
        matches = [name for name in pages if name.startswith(f"{chapter}-")]
        if len(matches) != 1:
            parser.error(f"Expected one SUMMARY.md entry for {chapter}; got {matches}")
        sample[matches[0]] = f"chapter-{chapter}.qmd"

    output_parent = ROOT / "_sample"
    output_parent.mkdir(exist_ok=True)
    project = Path(mkdtemp(prefix="preview-", dir=output_parent))
    (project / "images").mkdir()

    def rewrite_chapter_link(match: re.Match) -> str:
        label, target, anchor = match.groups()
        target = unquote(target)
        if target in sample:
            return f"[{label}]({sample[target]}{anchor or ''})"
        return label if target in pages else match[0]

    for source, output in sample.items():
        manuscript = (ROOT / source).read_text(encoding="utf-8")
        for match in IMAGE_LINK.findall(manuscript):
            image = Path(unquote(match))
            shutil.copyfile(ROOT / image, project / image)
        manuscript = CHAPTER_LINK.sub(rewrite_chapter_link, manuscript)
        manuscript = re.sub(r"^```mermaid[ \t]*$", "```{mermaid}", manuscript, flags=re.MULTILINE)
        if source == "README.md":
            manuscript = re.sub(r"^# [^\n]+\n\n## 前言 / Preface\n\n", "# 前言 / Preface\n\n" + SAMPLE_NOTE, manuscript, count=1)
        manuscript = re.sub(r"^# ([^\n]+)", rf"# \1 {{#{Path(output).stem}}}", manuscript, count=1)
        (project / output).write_text(manuscript, encoding="utf-8")

    chapters = "\n".join(f"    - {page}" for page in sample.values())
    font = args.font.replace("'", "''")
    config = f"""project:
  type: book

book:
  title: "我用做软件的方式学育种"
  subtitle: "Learning Animal Breeding the Way I Build Software · 样章 / Sample"
  author: "玩 AI 的杰克"
  output-file: breeding-learning-course-sample
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
    subprocess.run([quarto, "render", "--to", "all"], cwd=project, check=True)
    print(f"Preview files: {project / '_book'}")


if __name__ == "__main__":
    main()
