import pytest

from ckanext.ytp.comments.util import clean_input

REL = 'rel="nofollow noopener noreferrer"'


def test_plain_text():
    assert clean_input("Some text") == "Some text"


def test_newlines():
    assert clean_input("Line one\nLine two") == "Line one&nbsp;Line two"


def test_allowed_tags_kept():
    html = "<p>para</p><em>e</em><strong>s</strong><ul><li>i</li></ul>"
    assert clean_input(html) == html


@pytest.mark.parametrize("html,expected", [
    ("<script>alert(1)</script>Hi", "Hi"),
    ("<b>bold</b> <h1>T</h1>", "bold T"),
    ("<img src=x onerror=alert(1)>Hi", "Hi"),
    ("<iframe src=//evil></iframe>Hi", "Hi"),
    ('<p onclick="x" style="color:red" class="c">p</p>', "<p>p</p>"),
])
def test_unsafe_content_removed(html, expected):
    assert clean_input(html) == expected


def test_existing_links_get_rel():
    assert clean_input('<a href="http://x.ie" onclick="e()">l</a>') == \
        '<a href="http://x.ie" {}>l</a>'.format(REL)


def test_javascript_links_removed():
    assert clean_input('<a href="javascript:alert(1)">j</a>') == \
        '<a {}>j</a>'.format(REL)


def test_autolink():
    assert clean_input("See http://data.gov.ie/dataset?a=1&b=2, thanks.") == (
        'See <a href="http://data.gov.ie/dataset?a=1&amp;b=2" {0}>'
        'http://data.gov.ie/dataset?a=1&amp;b=2</a>, thanks.'.format(REL)
    )


def test_autolink_trailing_punctuation():
    assert clean_input("(https://x.ie/path)") == \
        '(<a href="https://x.ie/path" {}>https://x.ie/path</a>)'.format(REL)


def test_autolink_skips_existing_links():
    result = clean_input(
        '<a href="http://x.ie">http://x.ie</a> and http://y.ie')
    assert result == (
        '<a href="http://x.ie" {0}>http://x.ie</a> and '
        '<a href="http://y.ie" {0}>http://y.ie</a>'.format(REL)
    )


@pytest.mark.parametrize("text", [
    'http://x.ie/"onmouseover="alert(1)',
    "http://x.ie/'onmouseover='alert(1)",
    "&lt;a href=http://x.ie&gt;",
    "http://x.ie/<script>alert(1)</script>",
])
def test_autolink_cannot_break_attributes(text):
    result = clean_input(text)
    assert "onmouseover=" not in result.split(">")[0]
    assert "<script" not in result
    assert 'href="http://x.ie/"' in result or 'href="http://x.ie"' in result
