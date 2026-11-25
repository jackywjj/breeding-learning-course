#!/usr/bin/env python3
"""Build the complete static reading site from the release manuscript."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from tempfile import mkdtemp
from urllib.parse import unquote

from build_sample import CHAPTER_LINK, IMAGE_LINK, ROOT


SUMMARY_ENTRY = re.compile(r"^( *)\* \[([^\]]+)\]\(([^)]+\.md)\)\s*$")
PAGE_NUMBER = re.compile(r"^(\d{2}-\d+)-")
HOME_ART = "images/course-cover.png"
SIDEBAR = re.compile(r'(<nav\b[^>]*\bid="quarto-sidebar"[^>]*>)(.*?)(</nav>)', re.DOTALL)
SIDEBAR_LABEL = re.compile(r'(<span class="menu-text"[^>]*>)([^<>]*)(</span>)')


def read_navigation(summary):
    sidebar = []
    group = sidebar
    pages = {}
    chapter = None
    for line in summary.splitlines():
        if line.startswith("## "):
            group = []
            sidebar.append({"section": line[3:], "contents": group})
            chapter = None
            continue
        match = SUMMARY_ENTRY.fullmatch(line)
        if not match:
            continue
        indent, label, source = match.groups()
        source = unquote(source)
        if source in {"README.md", "00-目录.md"}:
            target = "index.qmd" if source == "README.md" else "contents.qmd"
        else:
            match_number = PAGE_NUMBER.match(source)
            if not match_number or PurePosixPath(source).name != source:
                raise ValueError(f"Unrecognized chapter path in SUMMARY.md: {source}")
            target = f"chapter-{match_number[1]}.qmd"
        if source in pages or target in pages.values():
            raise ValueError(f"Duplicate chapter in SUMMARY.md: {source}")
        pages[source] = target
        item = {"text": label, "href": target}
        if indent:
            if chapter is None:
                raise ValueError(f"Reading without a parent chapter: {source}")
            if "contents" not in chapter:
                chapter["section"] = chapter.pop("href")
                chapter["contents"] = []
            chapter["contents"].append(item)
        else:
            group.append(item)
            chapter = item
    if not {"README.md", "00-目录.md"} <= pages.keys():
        raise ValueError("SUMMARY.md must list the preface and contents.")
    return pages, sidebar


def format_sidebar(match):
    def bilingual_label(label_match):
        opening, label, closing = label_match.groups()
        primary, separator, secondary = label.strip().partition(" / ")
        if not separator:
            return label_match[0]
        return (
            f'{opening}<span class="course-nav-zh" lang="zh">{primary}</span> '
            f'<span class="course-nav-en" lang="en">{secondary}</span>{closing}'
        )

    opening, contents, closing = match.groups()
    return opening + SIDEBAR_LABEL.sub(bilingual_label, contents) + closing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quarto", default="quarto", help="path to the Quarto executable")
    parser.add_argument("--output", type=Path, help="new or empty directory for the rendered static files")
    args = parser.parse_args()
    quarto = shutil.which(args.quarto)
    if not quarto:
        parser.error("Quarto is required. Provide its path with --quarto.")
    if args.output and (
        args.output.is_symlink()
        or (args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())))
    ):
        parser.error("The output directory must be new or empty.")

    pages, sidebar = read_navigation((ROOT / "SUMMARY.md").read_text(encoding="utf-8"))
    workspace = ROOT / "_site-build"
    workspace.mkdir(exist_ok=True)
    project = Path(mkdtemp(prefix="render-", dir=workspace))
    (project / "images").mkdir()

    def rewrite_link(match):
        label, target, anchor = match.groups()
        target = unquote(target)
        if target in pages:
            return f"[{label}]({pages[target]}{anchor or ''})"
        if "://" in target:
            return match[0]
        raise ValueError(f"Chapter link is missing from SUMMARY.md: {target}")

    images = set()
    for source, target in pages.items():
        title_line, _, body = (ROOT / source).read_text(encoding="utf-8").partition("\n")
        if not title_line.startswith("# "):
            raise ValueError(f"Expected a heading at the start of {source}")
        images.update(unquote(asset) for asset in IMAGE_LINK.findall(body))
        body = CHAPTER_LINK.sub(rewrite_link, body)
        body = re.sub(r"^```mermaid[ \t]*$", "```{mermaid}", body, flags=re.MULTILINE)
        if target == "index.qmd":
            start = next(page for page in pages.values() if page == "chapter-01-0.qmd")
            body = f"""
::: {{.book-intro}}
![]({HOME_ART}){{fig-alt="电脑代码、手绘系谱和种猪的砖红插画"}}

::: {{.book-entry}}
[开始阅读 / Start reading]({start}){{.btn .btn-primary}}
[全书目录 / Contents](contents.qmd){{.btn .btn-outline-primary}}
:::
:::
""" + body
        title = json.dumps(title_line[2:], ensure_ascii=False)
        (project / target).write_text(f"---\ntitle: {title}\n---\n{body}", encoding="utf-8")

    for asset in sorted(images):
        path = PurePosixPath(asset)
        if len(path.parts) != 2 or path.parts[1] in {"..", "."}:
            raise ValueError(f"Invalid illustration path: {asset}")
        shutil.copyfile(ROOT / path, project / path)
    shutil.copyfile(ROOT / "tools/_extensions/course/cover-art.png", project / HOME_ART)
    for asset in ("sample.css", "site.scss"):
        shutil.copyfile(ROOT / "tools" / asset, project / asset)

    config = {
        "project": {"type": "website", "render": list(pages.values())},
        "website": {
            "title": "我用做软件的方式学育种",
            "search": True,
            "page-navigation": True,
            "navbar": {"right": [{"href": "contents.qmd", "text": "全书目录"}]},
            "sidebar": {"style": "docked", "collapse-level": 2, "contents": sidebar},
        },
        "lang": "zh",
        "execute": {"enabled": False},
        "format": {
            "html": {
                "theme": ["cosmo", "site.scss"],
                "css": "sample.css",
                "toc": True,
                "toc-title": "本页目录",
                "html-math-method": "mathml",
                "grid": {"sidebar-width": "320px", "margin-width": "210px"},
            },
        },
    }
    (project / "_quarto.yml").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run([quarto, "render", "--to", "html"], cwd=project, check=True)
    site = project / "_site"
    for source, route in pages.items():
        page = site / Path(route).with_suffix(".html")
        markup, count = SIDEBAR.subn(format_sidebar, page.read_text(encoding="utf-8"), count=1)
        if not count:
            raise ValueError(f"Missing sidebar in rendered page for {source}")
        page.write_text(markup, encoding="utf-8")
    (site / ".nojekyll").touch()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        if args.output.is_symlink() or any(args.output.iterdir()):
            parser.error("The output directory must be new or empty.")
        site = Path(shutil.copytree(site, args.output.resolve(), dirs_exist_ok=True))
    print(f"Static site: {site}")


if __name__ == "__main__":
    main()
