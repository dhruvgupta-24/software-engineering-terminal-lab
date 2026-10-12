#!/usr/bin/env python3
"""Give a hint for one experiment of the CourseDesk lab, without the answer.

    python3 ../../lab/hint.py 3        first hint for Experiment 3
    python3 ../../lab/hint.py 3 2      second, more specific hint
    python3 ../../lab/hint.py final    hints for the final task

Try the first hint before asking for the second.
"""
import sys
import textwrap

HINTS = {
    "1": [
        "Searches in less are case-sensitive and run forward from the screen you "
        "are on. Press g before each new search so it starts at the top.",
        "The headings are in capitals (NOTE FORMAT, ROTA, LOG FORMAT). When a "
        "search lands on a section marked RETIRED or ARCHIVED, press n until you "
        "reach the one marked CURRENT.",
    ],
    "2": [
        "Only lines 2 and 3 of work/handover.txt change in this experiment. Line 3 "
        "needs the incident lead from the CURRENT rota you found in Experiment 1.",
        "Ctrl+K deletes the whole line under the cursor, so you can retype it. "
        "Save with Ctrl+O then Enter, exit with Ctrl+X, then reopen to confirm. "
        "work/findings.txt needs at least two lines.",
    ],
    "3": [
        "Count fields from 1, using the field list in runbook Section 3. Always "
        "quote the delimiter: -d \"|\".",
        "List several fields with commas, for example -f 1,2,3. Do not sort the "
        "result: row order is what tells you which 503 came first. Save with > "
        "into a file in work/.",
    ],
    "4": [
        "Plain sort compares characters, not numbers. Which option compares the "
        "number at the start of each line?",
        "Cut fields 4 and 5 so each line starts with the response time, then add "
        "-n for numbers and -r for highest first. Read the first line of the "
        "saved file.",
    ],
    "5": [
        "uniq only merges identical lines that are directly next to each other.",
        "Put sort in front of uniq (or uniq -c) so identical lines become "
        "neighbours. For the status counts, start from work/statuses.txt.",
    ],
    "6": [
        "Press Ctrl+R and type |503. When your Experiment 3 grep appears, press "
        "Right Arrow, not Enter, then End to reach the end of the line.",
        "Delete | less and build the rest from tools you know: keep the server "
        "field with cut, put identical servers together with sort, count them "
        "with uniq -c, rank with sort -n -r, and save with > into work/.",
    ],
    "7": [
        "Lines marked < are in the first file (live); lines marked > are in the "
        "second (approved). Your working copy must end up matching the > side.",
        "c means change a line, d delete it, a add it. Edit work/web-02.conf in "
        "nano, then run diff work/web-02.conf evidence/web-02-approved.conf "
        "until it prints nothing.",
    ],
    "final": [
        "Read runbook Section 12 for who to include, and Section 11 for why a 504 "
        "is not a failed enrolment. Section 14 gives the exact note format.",
        "Filter requests.log with grep -F twice (status, then endpoint), cut the "
        "student field, then sort before uniq. For the note, fill in Section 14 "
        "line by line from work/findings.txt.",
    ],
}


def main(argv):
    if len(argv) not in (2, 3) or argv[1] not in HINTS:
        print("Usage: python3 ../../lab/hint.py EXPERIMENT [LEVEL]")
        print(f"EXPERIMENT is one of: {', '.join(HINTS)}. LEVEL is 1 or 2.")
        return 2
    level = argv[2] if len(argv) == 3 else "1"
    if level not in ("1", "2"):
        print("LEVEL must be 1 or 2.")
        return 2
    name = "the final task" if argv[1] == "final" else f"Experiment {argv[1]}"
    print(f"Hint {level} for {name}:")
    print(textwrap.fill(HINTS[argv[1]][int(level) - 1], width=78))
    if level == "1":
        print(f"Still stuck? python3 ../../lab/hint.py {argv[1]} 2")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
