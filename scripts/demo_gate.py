#!/usr/bin/env python3
"""A terminal demonstration of the citation gate.

Nothing here is staged. Every verdict on screen is a real lookup against the
real corpus, and the reasons are derived — "Romans 8 ends at verse 39" is
counted at runtime, not typed into a string.

    make demo              # paced for recording
    make demo FAST=1       # no delays, for checking it still works
"""
from __future__ import annotations
import os, sys, time, shutil, textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from berean import store                                    # noqa: E402
from berean.refs import parse, find_inline                  # noqa: E402
from berean.answer import _strip_invalid                    # noqa: E402

FAST = os.getenv("FAST") == "1"
W = min(shutil.get_terminal_size((92, 30)).columns, 92)

# palette
DIM, OFF = "\033[38;5;245m", "\033[0m"
GOLD, GOLDB = "\033[38;5;214m", "\033[1;38;5;214m"
GREEN, RED = "\033[38;5;78m", "\033[38;5;203m"
WHITE, BOLD = "\033[38;5;253m", "\033[1m"


def w(s="", d=0.0):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()
    if not FAST:
        time.sleep(d)


def type_out(s, d=0.012, indent=""):
    sys.stdout.write(indent)
    for ch in s:
        sys.stdout.write(ch)
        sys.stdout.flush()
        if not FAST:
            time.sleep(d)
    sys.stdout.write("\n")


def rule(ch="─"):
    w(f"{DIM}{ch * W}{OFF}")


def pause(t):
    if not FAST:
        time.sleep(t)


# ── the claim ────────────────────────────────────────────────────────────
CLAIM = ("Paul tells us to be anxious for nothing [Philippians 4:6-7], a theme "
         "echoed in [Romans 8:99] and prefigured in [Hezekiah 3:1].")


def why_invalid(con, ref) -> str:
    """Derive the reason, so the failure message cannot drift from the data."""
    last_ch, last_v = con.execute(
        "SELECT MAX(chapter), MAX(verse) FROM verses WHERE translation='BSB' AND book=? "
        "AND chapter=(SELECT MAX(chapter) FROM verses WHERE translation='BSB' AND book=?)",
        (ref.book, ref.book)).fetchone()
    end = con.execute(
        "SELECT MAX(verse) FROM verses WHERE translation='BSB' AND book=? AND chapter=?",
        (ref.book, ref.chapter)).fetchone()[0]
    if end is None:
        return f"{ref.book} has {last_ch} chapters, not {ref.chapter}"
    return f"{ref.book} {ref.chapter} ends at verse {end}"


def main():
    os.system("clear")
    con = store.connect()
    total = con.execute("SELECT COUNT(*) FROM verses WHERE translation='BSB'").fetchone()[0]

    w()
    w(f"  {GOLDB}isaiah-54-17{OFF}  {DIM}·{OFF}  {WHITE}the citation gate{OFF}", .6)
    w(f"  {DIM}{total:,} verses · every reference checked before you see it{OFF}", 1.1)
    w()
    rule()
    w()

    w(f"  {DIM}The model wrote this:{OFF}", .5)
    w()
    NB = "\x00"
    shown = CLAIM
    for t in ("[Philippians 4:6-7]", "[Romans 8:99]", "[Hezekiah 3:1]"):
        shown = shown.replace(t, t.replace(" ", NB))
    for line in textwrap.wrap(shown, W - 6):
        type_out(f"{WHITE}{line.replace(NB, ' ')}{OFF}", .014, "  ")
    w("", 1.0)

    refs = find_inline(CLAIM)
    bracketed = ["Philippians 4:6-7", "Romans 8:99", "Hezekiah 3:1"]

    w(f"  {DIM}Three references. Checking each one…{OFF}", 1.0)
    w()

    good, bad = 0, 0
    for label in bracketed:
        ref = parse(label)
        sys.stdout.write(f"    {DIM}checking{OFF} {label} ")
        sys.stdout.flush()
        pause(.75)
        sys.stdout.write("\r\033[K")

        if ref is None:
            bad += 1
            w(f"    {RED}✗{OFF}  {BOLD}{label:<22}{OFF}{DIM}no book by that name — never became a reference{OFF}", .55)
            continue

        rows = store.get_verses(con, ref, "BSB")
        if rows:
            good += 1
            text = rows[0]["text"]
            text = text[:W - 34] + "…" if len(text) > W - 33 else text
            w(f"    {GREEN}✓{OFF}  {BOLD}{label:<22}{OFF}{WHITE}{text}{OFF}", .55)
        else:
            bad += 1
            w(f"    {RED}✗{OFF}  {BOLD}{label:<22}{OFF}{DIM}{why_invalid(con, ref)}{OFF}", .55)

    w("", 1.0)
    rule()
    w()
    w(f"  {DIM}What the reader actually receives:{OFF}", .6)
    w()
    # This is the app's own function, not a re-implementation for the demo.
    rendered = _strip_invalid(CLAIM, [r for r in refs if not store.exists(con, r, "BSB")])

    # A reference must never be split across a line break: wrapping would put
    # half of it on each line and neither half would colourise, so a stripped
    # reference could still look bracketed and live. Glue each one with a
    # sentinel, wrap, then restore.
    protect = ["[Philippians 4:6-7]", "Romans 8:99", "Hezekiah 3:1"]
    glued = rendered
    for t in protect:
        glued = glued.replace(t, t.replace(" ", NB))

    def colourise(line: str) -> str:
        line = line.replace("[Philippians" + NB + "4:6-7]",
                            f"{GOLD}[Philippians 4:6-7]{OFF}{WHITE}")
        for dead in ("Romans" + NB + "8:99", "Hezekiah" + NB + "3:1"):
            line = line.replace(dead, f"{DIM}{dead.replace(NB, ' ')}{OFF}{WHITE}")
        return line.replace(NB, " ")

    for line in textwrap.wrap(glued, W - 6):
        w(f"  {WHITE}{colourise(line)}{OFF}", .12)
    pause(1.1)
    w()
    w(f"  {GREEN}{good} verified{OFF}   {RED}{bad} stripped{OFF}   "
      f"{DIM}— unlinked, so nothing looks checkable that isn't{OFF}", 1.4)
    w()
    rule()
    w()
    w(f"  {DIM}Most apps put this in the prompt:{OFF}", .7)
    w(f"    {DIM}\"Only cite the passages provided. Do not invent references.\"{OFF}", 1.3)
    w()
    w(f"  {WHITE}A prompt is a request.{OFF}  {GOLDB}This is a lookup.{OFF}", 1.6)
    w()
    con.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(OFF)
