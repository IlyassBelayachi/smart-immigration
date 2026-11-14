from smart_immigration.knowledge.ingest import build_chunks, parse_page, split_text

HTML = """<html><head><meta name="dcterms.modified" content="2026-09-02"></head><body><main>
<nav>menu</nav><h1>Title</h1><p>Intro sentence.</p><h2>Section A</h2><p>First. Second.</p><li>Third item.</li>
<h2>Section B</h2><p>Other text.</p></main></body></html>"""


def test_parse_page_and_chunks():
    modified, sections = parse_page(HTML)
    assert modified == "2026-09-02"
    assert [s for s, _ in sections] == ["Title", "Section A", "Section B"]
    src = {"source_id": "x", "url": "https://www.canada.ca/x", "title": "T"}
    chunks = build_chunks(src, HTML, "CA", "study_permit", "en")
    assert chunks[0]["page_modified"] == "2026-09-02"
    assert all(c["content_hash"] and c["url"] for c in chunks)


def test_split_text_respects_limit():
    text = " ".join(f"Sentence number {i}." for i in range(100))
    assert all(len(c) <= 900 for c in split_text(text))
