#!/usr/bin/env python3
"""Build articles.json from the Markdown files in articles/.

Each article is articles/<slug>.md. Optional front matter at the top of the file:

    ---
    title: My article title
    date: 2026-11-15
    summary: One or two sentences shown in the list.
    author: Your Name
    published: true
    ---

Anything missing is filled in:
  title    -> the first "# Heading" in the file, otherwise the slug
  date     -> today's date (UTC) the first time the file is seen, kept afterwards
  summary  -> the first paragraph, shortened to 160 characters
  author   -> empty (the website shows the company name)
  published-> true

Only the Python standard library is used.
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")
OUT = os.path.join(ROOT, "articles.json")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8-sig", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_front_matter(text):
    """Return (dict, body). Front matter is optional."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    rest = text[end + 4:]
    if rest and not rest.startswith("\n"):
        return {}, text
    meta = {}
    for line in block.split("\n"):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        val = m.group(2).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        meta[m.group(1).lower()] = val
    return meta, rest.lstrip("\n")


def first_heading(body):
    m = re.search(r"^\s*#\s+(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def first_paragraph(body):
    in_code = False
    para = []
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not s:
            if para:
                break
            continue
        if s.startswith(("#", ">", "|", "-", "*", "!", "<")) or re.match(r"^\d+\.\s", s):
            if para:
                break
            continue
        para.append(s)
    text = " ".join(para)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_]{1,3}", "", text)
    if len(text) > 160:
        text = text[:157].rsplit(" ", 1)[0].rstrip(",;:.") + "..."
    return text


def truthy(value, default=True):
    if value is None or value == "":
        return default
    return str(value).strip().lower() not in ("false", "no", "0", "off")


def load_previous():
    try:
        with open(OUT, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return {a["slug"]: a for a in data if isinstance(a, dict) and "slug" in a}
    except (OSError, ValueError):
        return {}


def main():
    previous = load_previous()
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    items = []
    problems = 0
    if not os.path.isdir(ARTICLES):
        print("No articles/ folder found.", file=sys.stderr)
        return 1
    for name in sorted(os.listdir(ARTICLES)):
        if not name.endswith(".md"):
            continue
        slug = name[:-3]
        if not SLUG.match(slug):
            print(f"SKIPPED {name}: the file name must use lowercase letters, digits and hyphens only "
                  f"(for example my-article.md).", file=sys.stderr)
            problems += 1
            continue
        meta, body = split_front_matter(read_text(os.path.join(ARTICLES, name)))
        date = meta.get("date", "")
        if not DATE.match(date):
            if date:
                print(f"WARNING {name}: date '{date}' is not YYYY-MM-DD; using a default.", file=sys.stderr)
                problems += 1
            date = previous.get(slug, {}).get("date") or today
        item = {
            "slug": slug,
            "title": meta.get("title") or first_heading(body) or slug.replace("-", " "),
            "date": date,
            "summary": meta.get("summary") or first_paragraph(body),
            "author": meta.get("author", ""),
            "published": truthy(meta.get("published")),
        }
        items.append(item)
    items = [a for a in items if a["published"]]
    items.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    out = json.dumps(items, indent=2, ensure_ascii=False) + "\n"
    old = ""
    try:
        with open(OUT, "r", encoding="utf-8") as fh:
            old = fh.read()
    except OSError:
        pass
    if out != old:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(out)
        print(f"articles.json updated: {len(items)} published article(s).")
    else:
        print(f"articles.json already up to date: {len(items)} published article(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
