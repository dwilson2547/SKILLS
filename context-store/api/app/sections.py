import re


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or "section"


def parse_sections(doc_slug: str, content: str) -> list[dict]:
    pattern = re.compile(r"^(#{1,6})\s+(.+?)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    if not matches:
        return [
            {
                "slug": f"{doc_slug}#content",
                "heading": "",
                "heading_slug": "content",
                "level": 0,
                "content": content.strip(),
                "position": 0,
            }
        ]

    # Track heading_slug usage within this document to avoid duplicates
    seen: dict[str, int] = {}
    sections = []

    for i, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        h_slug = slugify(heading)

        # Deduplicate heading slugs within a document
        if h_slug in seen:
            seen[h_slug] += 1
            h_slug = f"{h_slug}-{seen[h_slug]}"
        else:
            seen[h_slug] = 0

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()

        sections.append(
            {
                "slug": f"{doc_slug}#{h_slug}",
                "heading": heading,
                "heading_slug": h_slug,
                "level": level,
                "content": section_content,
                "position": i,
            }
        )

    return sections
