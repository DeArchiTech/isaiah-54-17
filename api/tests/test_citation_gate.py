"""The citation gate.

This is the whole idea of the project, so it is the test to read first.

A language model asked about scripture will sometimes produce a reference that
looks perfectly well-formed and does not exist — Romans 8:99, or a chapter of
Philippians that was never written. Asking it not to do that in the system
prompt reduces the rate; it does not make the guarantee. A prompt is a request.

So the guarantee is made here instead: parse every reference the model wrote,
look each one up, and drop the ones that do not resolve before the response
leaves the server.
"""
from berean import store
from berean.refs import find_inline, parse


def test_a_real_reference_survives(con):
    good, bad = store.validate(con, find_inline("see [Romans 8:28]"), "BSB")
    assert [r.label for r in good] == ["Romans 8:28"]
    assert bad == []


def test_an_invented_verse_is_caught(con):
    """Romans has 8:28. It does not have 8:99."""
    good, bad = store.validate(con, find_inline("see [Romans 8:99]"), "BSB")
    assert good == []
    assert [r.label for r in bad] == ["Romans 8:99"]


def test_an_invented_book_never_becomes_a_reference():
    """Filtered earlier still — 'Hezekiah' is not a book, so it never parses."""
    assert parse("Hezekiah 3:1") is None
    assert find_inline("as [Hezekiah 3:1] says") == []


def test_a_real_book_at_an_impossible_chapter_is_caught(con):
    good, bad = store.validate(con, find_inline("[Genesis 999:1]"), "BSB")
    assert good == []
    assert [r.label for r in bad] == ["Genesis 999:1"]


def test_the_gate_is_per_translation(con):
    """A verse present in one text and absent from another must not pass on the
    strength of the other. The fixture has Philippians 4:6 in BSB only."""
    refs = find_inline("[Philippians 4:6]")
    assert [r.label for r in store.validate(con, refs, "BSB")[0]] == ["Philippians 4:6"]
    assert [r.label for r in store.validate(con, refs, "KJV")[1]] == ["Philippians 4:6"]


def test_mixed_output_keeps_the_good_and_drops_the_bad(con):
    text = "Paul writes [Philippians 4:6-7], and also [Philippians 9:1], and [Romans 8:28]."
    good, bad = store.validate(con, find_inline(text), "BSB")
    assert [r.label for r in good] == ["Philippians 4:6-7", "Romans 8:28"]
    assert [r.label for r in bad] == ["Philippians 9:1"]


def test_placeholder_key_counts_as_unconfigured(monkeypatch):
    """First run after `make setup` has a key variable that is set and useless.
    Reporting that as configured trades a clear message for a 401."""
    from berean import answer
    monkeypatch.setattr(answer.os.path, "isdir", lambda p: False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-REPLACE_ME")
    assert answer._has_model() is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-" + "aBc9dEf2" * 6)
    assert answer._has_model() is True
    # a real key may contain a short run of x's — that must not read as a placeholder
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-xxq" + "aBc9dEf2" * 6)
    assert answer._has_model() is True
