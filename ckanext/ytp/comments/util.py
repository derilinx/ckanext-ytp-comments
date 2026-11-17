import re

import nh3

ALLOWED_TAGS = {
    "a", "em", "strong", "cite", "code", "ul", "ol", "li", "p", "blockquote"
}

ALLOWED_ATTRIBUTES = {"a": {"href"}}

LINK_REL = "nofollow noopener noreferrer"

# Quotes and angle brackets (raw or escaped, as the text has already been
# sanitized) are excluded so a match can never break out of the href attribute
URL_RE = re.compile(
    r"""https?://(?:(?!&(?:lt|gt|quot|#0*39|#x0*27);)[^\s<>"'])+""",
    re.IGNORECASE,
)
TRAILING_PUNCTUATION = ".,;:!?)"

# Splits sanitized HTML into tags and text, capturing the tags
TAG_RE = re.compile(r"(<[^>]*>)")


def _sanitize(html):
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel=LINK_REL,
    )


def _link(match):
    url = match.group(0)
    trailing = ""
    while url and url[-1] in TRAILING_PUNCTUATION:
        trailing = url[-1] + trailing
        url = url[:-1]
    if not url:
        return match.group(0)
    return '<a href="{0}">{0}</a>{1}'.format(url, trailing)


def _autolink(html):
    """Turns bare URLs in the text of sanitized HTML into links, leaving
    tags and the contents of existing links untouched."""
    parts = TAG_RE.split(html)
    in_link = 0
    for i, part in enumerate(parts):
        if i % 2:
            # A tag
            tag = part.lower()
            if tag.startswith("<a ") or tag == "<a>":
                in_link += 1
            elif tag == "</a>":
                in_link = max(in_link - 1, 0)
        elif not in_link:
            parts[i] = URL_RE.sub(_link, part)
    return "".join(parts)


def clean_input(comment):
    content = _autolink(_sanitize(comment))
    # Sanitize again so the generated links get the same treatment as the
    # ones provided by the user
    return _sanitize(content).replace('\n', '&nbsp;')
