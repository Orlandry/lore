"""mkdocs hook: render ADR frontmatter as a table on the site.

ADR source files carry status/date/deciders/etc. in YAML frontmatter, which
mkdocs consumes and never renders. For pages under developing/decisions/ whose
filename is an ADR (NNNNN-slug.md), this injects a small metadata table just
under the H1, built from the frontmatter (the single source of truth). A
markdown link in `status` (e.g. "superseded by [ADR-00006](...)") renders
normally because injection happens before markdown conversion.

The ADR number itself lives in the H1 ("# ADR-NNNNN: ...") and the filename, so
the nav and page title carry it without any help from this hook.
"""

import posixpath
import re

ADR_FILENAME = re.compile(r"\d{5}-")
META_FIELDS = ("status", "date", "deciders", "consulted", "informed")


def on_page_markdown(markdown, *, page, **kwargs):
    """Inject a frontmatter metadata table under the H1 of each ADR page."""
    src = page.file.src_uri
    if "developing/decisions/" not in src:
        return markdown
    if not ADR_FILENAME.match(posixpath.basename(src)):  # README.md, adr-template.md
        return markdown

    rows = []
    for key in META_FIELDS:
        value = page.meta.get(key)
        if value in (None, ""):
            continue
        rows.append(f"| **{key.capitalize()}** | {str(value).strip()} |")
    if not rows:
        return markdown

    out = []
    inserted = False
    for line in markdown.split("\n"):
        out.append(line)
        if not inserted and line.startswith("# "):
            out += ["", "| Field | Value |", "|---|---|", *rows]
            inserted = True
    return "\n".join(out)
