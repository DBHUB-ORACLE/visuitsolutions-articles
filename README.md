# visuitsolutions-articles

Articles for the Resources section of https://visuitsolutions.com.
The website reads this repository directly. Add a Markdown file and push: the article list updates itself.

The repository must be **public**.

## Structure

```
articles/
  <slug>.md              one Markdown file per article
  images/                optional pictures used in articles
articles.json            generated automatically - do not edit by hand
scripts/build_index.py   builds articles.json from the Markdown files
.github/workflows/build-index.yml   runs the script on every push
```

## Publish a new article

1. Create `articles/<slug>.md` (GitHub: Add file > Create new file).
   The slug is the file name: lowercase letters, digits, and hyphens only, for example `ora-00600-at-startup.md`.
2. Write the article (see the template below) and commit to `main`.
3. Wait about one minute. A GitHub Action rebuilds `articles.json` and commits it as "Update articles.json".
4. The article appears on https://visuitsolutions.com/resources/ about five minutes later (GitHub caches raw files briefly).

You never edit `articles.json`.

## Article template

```markdown
---
title: ORA-00600 at startup: first steps
date: 2026-11-15
summary: One or two sentences shown in the article list and in search results.
author: Your Name
---

Opening paragraph that explains the problem.

## First check

Steps, commands, and what the output means.
```

Everything in the block between the `---` lines is optional. If you leave something out:

| Field | If missing |
|---|---|
| title | the first `# Heading` in the file, otherwise the file name |
| date | the day you first pushed the file |
| summary | the first paragraph, shortened to 160 characters |
| author | the website shows "Visu IT Solutions Oracle team" |
| published | the article is published; write `published: false` to hide a draft |

## Writing rules

- One error code or one real situation per article.
- Write from real experience; include the commands you actually ran.
- English only.
- Use headings (`##`), short paragraphs, and code blocks for SQL and RMAN.
- Never include customer names, hostnames, IP addresses, or real data.
- End with what the reader should do next.

## Images

Put images in `articles/images/` and link them relatively: `![ASM disk list](images/asm-disks.png)`.

## If an article does not appear

1. Open the **Actions** tab of this repository. The latest "Build articles.json" run must be green. A red run shows the reason.
2. Check the file name: lowercase, hyphens, ends with `.md`. The Action log lists any skipped file.
3. Open `articles.json` in the repository and check your article is listed.
4. Open https://raw.githubusercontent.com/DBHUB-ORACLE/visuitsolutions-articles/main/articles.json . If it is old, wait a few minutes.
5. Hard refresh the website page (Ctrl+F5).

## One-time setup

- Settings > Actions > General > Workflow permissions: choose **Read and write permissions** if the Action cannot push (only needed on some accounts).
- If the repository's default branch is not `main`, rename it to `main`.
