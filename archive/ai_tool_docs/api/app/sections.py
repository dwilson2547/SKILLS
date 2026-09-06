import re


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or "section"


def parse_sections(doc_slug: str, content: str) -> list[dict]:
    """Split markdown content into sections by heading."""
    pattern = re.compile(r"^(#{1,6})\s+(.+?)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    if not matches:
        return [
            {
                "heading": "",
                "level": 0,
                "content": content.strip(),
                "position": 0,
            }
        ]

    sections = []

    for i, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()

        sections.append(
            {
                "heading": heading,
                "level": level,
                "content": section_content,
                "position": i,
            }
        )

    return sections
