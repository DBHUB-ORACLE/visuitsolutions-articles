# visuitsolutions-articles

Articles for the Resources section of https://visuitsolutions.com.
The website reads this repository directly, so a push here publishes the article. No website upload is needed.

The repository must be **public**.

## Structure

```
articles.json            list of articles shown on the website
articles/
  <slug>.md              one Markdown file per article
  images/                optional pictures used in articles
```

## Publish a new article

1. Choose a slug: lowercase letters, digits, and hyphens only, for example `ora-00600-at-startup`.
2. Create `articles/<slug>.md`. Start with a `# Title` line; the website takes the title from `articles.json` and hides this line.
3. Add an entry at the top of `articles.json`:

```json
{
  "slug": "ora-00600-at-startup",
  "title": "ORA-00600 at startup: first steps",
  "date": "2026-11-15",
  "summary": "One or two sentences shown in the article list and in search results.",
  "author": "",
  "published": true
}
```

4. Commit and push. The article appears at `https://visuitsolutions.com/resources/read/?a=<slug>` within about five minutes (GitHub caches raw files briefly).

## Fields in articles.json

| Field | Required | Notes |
|---|---|---|
| slug | yes | Must match the file name without `.md` |
| title | yes | Shown as the page title |
| date | yes | `YYYY-MM-DD`; the list is sorted newest first |
| summary | yes | 1 to 2 sentences, under 160 characters |
| author | no | Your name; empty shows "Visu IT Solutions Oracle team" |
| published | no | Set to `false` to hide an article without deleting it |

## Writing rules

- One error code or one real situation per article.
- Write from real experience; include the commands you actually ran.
- English only.
- Use headings (`##`), short paragraphs, code blocks for SQL and RMAN.
- Never include customer names, hostnames, IP addresses, or real data.
- End with what the reader should do next.

## Images

Put images in `articles/images/` and link them relatively: `![ASM disk list](images/asm-disks.png)`.

## Check before pushing

- `articles.json` is valid JSON (a missing comma hides every article). Paste it into any JSON validator if unsure.
- The slug in `articles.json` and the file name match exactly.
