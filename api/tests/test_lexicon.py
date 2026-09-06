"""The lexicon is data, not code.

These tests guard the boundary: the JSON has to stay loadable and well-shaped,
and a malformed file has to fail loudly rather than silently degrade every
passage in the app to "no lexical data".
"""
import json
import pytest
from berean import lexicon


def test_data_file_is_the_source_of_truth():
    raw = json.loads(lexicon.DATA.read_text(encoding="utf-8"))
    assert raw == lexicon.ENTRIES
    assert lexicon.COVERAGE == len(raw) > 0


def test_every_entry_is_well_formed():
    for label, entry in lexicon.ENTRIES.items():
        assert entry["context"].strip(), f"{label} has an empty context"
        for lemma in entry.get("lemmas", []):
            assert lexicon._REQUIRED_LEMMA_KEYS <= lemma.keys()
            assert lemma["strongs"][0] in "GH", f"{label}: odd Strong's {lemma['strongs']}"


def test_commentary_is_always_attributed():
    """Public-domain quotations still need a source line, or the app is
    presenting someone else's interpretation as its own."""
    for label, entry in lexicon.ENTRIES.items():
        c = entry.get("commentary")
        if c:
            assert c.get("source"), f"{label} quotes commentary with no source"


def test_keys_are_parseable_references():
    from berean.refs import parse
    for label in lexicon.ENTRIES:
        assert parse(label) is not None, f"{label} is not a valid reference"
        assert parse(label).label == label, f"{label} is not in canonical form"


@pytest.mark.parametrize("bad,expect", [
    ('{"Romans 8:28": {}}', "context"),
    ('{"Romans 8:28": {"context": "x", "lemmas": [{"word": "w"}]}}', "missing"),
    ('not json at all', "not valid JSON"),
])
def test_malformed_data_fails_loudly(tmp_path, bad, expect):
    p = tmp_path / "lexicon.json"
    p.write_text(bad, encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        lexicon._load(p)
    assert expect in str(e.value)


def test_missing_file_fails_loudly(tmp_path):
    with pytest.raises(SystemExit, match="missing"):
        lexicon._load(tmp_path / "nope.json")
