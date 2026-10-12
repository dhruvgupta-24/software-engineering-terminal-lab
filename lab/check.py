#!/usr/bin/env python3
"""Check the results of the CourseDesk incident handover lab.

Run from your lab root (the attempt folder created by lab/start.sh):

    python3 ../../lab/check.py          check everything
    python3 ../../lab/check.py 3        check one experiment (2 to 7)
    python3 ../../lab/check.py final    check the final task only

The checker only reads files. It never creates, changes or deletes anything.
It cannot see how you used history, nano or less; show those skills to your
instructor.
"""
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
PARTS = ["2", "3", "4", "5", "6", "7", "final"]

INCIDENT_ID = "INC-2417"
INCIDENT_LEAD = "Tomas Reyes"
ARCHIVED_LEAD = "Ravi Menon"
CAUSE = "db.pool_size changed from 40 to 4"

# Output of: diff evidence/web-02-live.conf evidence/web-02-approved.conf
CONFIG_DIFF = """7c7
< db.pool_size = 4
---
> db.pool_size = 40
9d8
< debug.sql_trace = on
10a10
> cache.course_list_ttl = 300
"""
# The same comparison with the two files in the opposite order.
CONFIG_DIFF_REVERSED = """7c7
< db.pool_size = 40
---
> db.pool_size = 4
8a9
> debug.sql_trace = on
10d10
< cache.course_list_ttl = 300
"""


# ---------------------------------------------------------------- helpers

def read_lines(path):
    """Return the lines of a text file, or None if it does not exist."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n") if text else []


def parse_counts(lines):
    """Parse uniq -c output into a list of (count, text) pairs.

    Returns (pairs, None) or (None, message).
    """
    pairs = []
    for number, line in enumerate(lines, 1):
        match = re.match(r"^\s*(\d+) (.+)$", line)
        if not match:
            return None, (f"line {number} ({line!r}) does not look like uniq -c "
                          "output: a count, a space, then the text.")
        pairs.append((int(match.group(1)), match.group(2)))
    return pairs, None


def is_number(text):
    return text.isdigit()


class Evidence:
    """Facts derived from the original evidence files."""

    def __init__(self, folder):
        rows = [line.split("|") for line in read_lines(folder / "requests.log")]
        alerts = [line.split("|") for line in read_lines(folder / "alerts.log")]
        self.rows = rows
        self.statuses = [r[2] for r in rows]
        self.time_server_status = ["|".join(r[:3]) for r in rows]
        self.latency_pairs = ["|".join(r[3:5]) for r in rows]
        self.alert_pairs = ["|".join(a[1:3]) for a in alerts]
        errors = [r for r in rows if r[2] == "503"]
        self.errors_503 = len(errors)
        self.errors_by_server = Counter(r[1] for r in errors)
        self.first_503 = errors[0][0]
        slowest = max(rows, key=lambda r: int(r[3]))
        self.slowest = f"{slowest[3]} ms on {slowest[4]}"
        self.students = sorted({r[5] for r in errors if r[4] == "/api/enrol"})
        self.approved_conf = read_lines(folder / "web-02-approved.conf")


# ---------------------------------------------------------------- checks

class Checker:
    def __init__(self, attempt):
        self.attempt = attempt
        self.work = attempt / "work"
        self.results = []          # (part, passed, message)
        self.ev = Evidence(LAB_DIR / "evidence")

    def record(self, part, passed, message):
        self.results.append((part, passed, message))

    def lines(self, part, name):
        """Read a work file, recording a failure if it is missing or empty."""
        lines = read_lines(self.work / name)
        if lines is None:
            self.record(part, False, f"work/{name} is missing (not created yet, or "
                        "saved under another name).")
            return None
        if not any(line.strip() for line in lines):
            self.record(part, False, f"work/{name} is empty. If you used the same "
                        "file as input and as the destination of >, the shell "
                        "emptied it before the command ran. Run the command again "
                        "with a different destination.")
            return None
        return lines

    # Evidence -----------------------------------------------------------

    def check_evidence(self):
        manifest = {}
        for line in read_lines(LAB_DIR / "evidence.sha256"):
            digest, name = line.split(maxsplit=1)
            manifest[name.lstrip("*")] = digest
        problems = []
        for folder, label in [(LAB_DIR / "evidence", "lab/evidence"),
                              (self.attempt / "evidence", "evidence")]:
            for name, digest in sorted(manifest.items()):
                path = folder / name
                if not path.is_file():
                    problems.append(f"{label}/{name} is missing")
                elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    problems.append(f"{label}/{name} has been changed")
        if problems:
            self.record("evidence", False, "; ".join(problems) + ". Original "
                        "evidence must not be edited. Start a new attempt with "
                        "bash lab/start.sh from the repository root and copy "
                        "your work files across, or ask your instructor.")
        else:
            self.record("evidence", True, "Original evidence files are unchanged.")

    # Experiment 2: nano --------------------------------------------------

    def check_handover_lines(self, part, lines, expected):
        """Compare handover lines with (label, value, hint) triples."""
        for number, (label, value, hint) in enumerate(expected, 1):
            if number > len(lines):
                self.record(part, False, f"work/handover.txt has no line {number}. "
                            f"Expected a line starting '{label}:'.")
                return False
            line = lines[number - 1].rstrip()
            if not line.startswith(label + ":"):
                self.record(part, False, f"work/handover.txt line {number} should "
                            f"start with '{label}:' (found {line!r}). Follow the "
                            "rev 4 format in the runbook.")
                return False
            got = line[len(label) + 1:].strip()
            if got != value:
                self.record(part, False, f"work/handover.txt line {number} "
                            f"('{label}:') has the wrong value. {hint(got)}")
                return False
        return True

    def handover_spec(self, students_in_file):
        ev = self.ev

        def escalation(got):
            if got == ARCHIVED_LEAD:
                return (f"{ARCHIVED_LEAD} is on the archived 2025 rota. Use the "
                        "incident lead from the CURRENT rota (runbook Section 15).")
            return "Use the incident lead from the CURRENT rota (runbook Section 15)."

        def cause(got):
            if got == "db.pool_size changed from 4 to 40":
                return ("The approved value comes first: 'changed from <approved "
                        "value> to <live value>'.")
            return ("Use the format '<setting> changed from <approved value> to "
                    "<live value>' with the setting your comparison found "
                    "(Experiment 7). debug.sql_trace and cache.course_list_ttl "
                    "were added or removed, not changed.")

        def students(got):
            if students_in_file is not None and got != str(students_in_file):
                return (f"It should match the {students_in_file} IDs in "
                        "work/students-to-contact.txt.")
            return "It should equal the number of IDs in work/students-to-contact.txt."

        return [
            ("Incident", INCIDENT_ID, lambda g: "Keep the incident ID from the draft."),
            ("Service", "coursedesk", lambda g: "The service name is coursedesk."),
            ("Escalation", INCIDENT_LEAD, escalation),
            ("Faulty server", max(ev.errors_by_server, key=ev.errors_by_server.get),
             lambda g: "Use the server with the most 503 responses (Experiment 6)."),
            ("First 503", ev.first_503,
             lambda g: "Use the time of the earliest 503 response, HH:MM:SS "
                       "(Experiment 3)."),
            ("503 responses", str(ev.errors_503),
             lambda g: "Count every 503 line in requests.log, on all servers "
                       "(Experiment 5)."),
            ("Slowest request", ev.slowest,
             lambda g: "Use '<ms> ms on <endpoint>' from the first line of "
                       "work/latency-ranked.txt (Experiment 4)."),
            ("Cause", CAUSE, cause),
            ("Config", "reconciled",
             lambda g: "Write exactly 'Config: reconciled'."),
            ("Students to contact", str(len(ev.students)), students),
        ]

    def part_2(self):
        lines = self.lines("2", "handover.txt")
        if lines is not None:
            spec = self.handover_spec(None)[:3]
            if self.check_handover_lines("2", lines, spec):
                self.record("2", True, "work/handover.txt lines 1 to 3 follow rev 4.")
        lines = self.lines("2", "findings.txt")
        if lines is not None:
            filled = [line for line in lines if line.strip()]
            if len(filled) < 2:
                self.record("2", False, "work/findings.txt needs at least two "
                            "lines: the handover format revision and the incident "
                            "lead you found in the runbook.")
            else:
                self.record("2", True, "work/findings.txt was created with notes.")

    # Experiment 3: cut ---------------------------------------------------

    def compare_extract(self, part, name, lines, expected, fields):
        if lines == expected:
            self.record(part, True, f"work/{name} has field(s) {fields} in the "
                        "original row order.")
        elif sorted(lines) == sorted(expected):
            self.record(part, False, f"work/{name} has the right lines in a "
                        "different order. cut keeps the original row order; "
                        "do not sort this output.")
        elif len(lines) != len(expected):
            self.record(part, False, f"work/{name} has {len(lines)} lines; "
                        f"requests.log has {len(expected)}. Extract from every "
                        "row of evidence/requests.log.")
        else:
            self.record(part, False, f"work/{name} does not contain field(s) "
                        f"{fields}. First line found: {lines[0]!r}, expected "
                        f"{expected[0]!r}. Check -d \"|\" and the -f list.")

    def part_3(self):
        lines = self.lines("3", "statuses.txt")
        if lines is not None:
            self.compare_extract("3", "statuses.txt", lines, self.ev.statuses, "3")
        lines = self.lines("3", "time-server-status.txt")
        if lines is not None:
            self.compare_extract("3", "time-server-status.txt", lines,
                                 self.ev.time_server_status, "1,2,3")

    # Experiment 4: sort --------------------------------------------------

    def part_4(self):
        name = "latency-ranked.txt"
        lines = self.lines("4", name)
        if lines is None:
            return
        expected = self.ev.latency_pairs
        if len(lines) and "|" not in lines[0]:
            self.record("4", False, f"work/{name} should keep two fields, the "
                        "response time and the endpoint, like '512|/login'. "
                        "Use cut -f 4,5.")
            return
        if sorted(lines) != sorted(expected):
            self.record("4", False, f"work/{name} does not contain fields 4 and 5 "
                        "of every row in evidence/requests.log.")
            return
        values = [int(line.split("|")[0]) for line in lines]
        if values == sorted(values, reverse=True):
            self.record("4", True, f"work/{name} is in descending numeric order.")
        elif values == sorted(values):
            self.record("4", False, f"work/{name} is in ascending order. Add -r "
                        "to reverse it so the slowest request is first.")
        elif lines == sorted(lines, reverse=True):
            self.record("4", False, f"work/{name} is in reverse text order, so "
                        "9xx appears above 10093. Add -n to compare numbers.")
        else:
            self.record("4", False, f"work/{name} is not in descending numeric "
                        "order. Use sort -n -r.")

    # Experiment 5: uniq --------------------------------------------------

    def check_counts(self, part, name, expected_counter, what):
        lines = self.lines(part, name)
        if lines is None:
            return
        pairs, error = parse_counts(lines)
        if error:
            self.record(part, False, f"work/{name}: {error}")
            return
        keys = [text for _, text in pairs]
        repeated = [k for k, n in Counter(keys).items() if n > 1]
        if repeated:
            self.record(part, False, f"work/{name} lists {repeated[0]!r} more than "
                        "once. uniq -c only groups adjacent lines; sort before "
                        "uniq -c.")
            return
        got = {text: count for count, text in pairs}
        if got != dict(expected_counter):
            total = sum(got.values())
            expected_total = sum(expected_counter.values())
            hint = (f"The counts add up to {total}, but there are {expected_total} "
                    f"{what}." if total != expected_total else
                    "Check that you selected the right field(s).")
            self.record(part, False, f"work/{name} has the wrong counts. {hint}")
            return
        self.record(part, True, f"work/{name} counts every {what[:-1]} group once.")
        return pairs

    def part_5(self):
        name = "alert-types.txt"
        lines = self.lines("5", name)
        if lines is not None:
            expected = sorted(set(self.ev.alert_pairs))
            if lines == expected:
                self.record("5", True, f"work/{name} lists each alert and server "
                            "once, in sorted order.")
            elif len(lines) != len(set(lines)):
                self.record("5", False, f"work/{name} still has repeated lines. "
                            "uniq removes only adjacent repeats; sort first, then "
                            "uniq.")
            elif sorted(lines) == expected:
                self.record("5", False, f"work/{name} has the right lines but not "
                            "in sorted order.")
            else:
                self.record("5", False, f"work/{name} should hold fields 2 and 3 of "
                            "evidence/alerts.log (alert name and server), each "
                            "pair once.")
        self.check_counts("5", "alert-counts.txt", Counter(self.ev.alert_pairs),
                          "alerts")
        self.check_counts("5", "status-counts.txt", Counter(self.ev.statuses),
                          "requests")

    # Experiment 6: history -----------------------------------------------

    def part_6(self):
        pairs = self.check_counts("6", "errors-by-server.txt",
                                  self.ev.errors_by_server, "503 responses")
        if pairs is None:
            return
        counts = [count for count, _ in pairs]
        if counts != sorted(counts, reverse=True):
            # Replace the pass recorded by check_counts with a failure.
            self.results.pop()
            self.record("6", False, "work/errors-by-server.txt has the right counts "
                        "but the highest count is not first. Add sort -n -r "
                        "after uniq -c.")

    # Experiment 7: diff --------------------------------------------------

    def part_7(self):
        path = self.work / "config-changes.diff"
        if not path.is_file():
            self.record("7", False, "work/config-changes.diff is missing.")
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            if text == CONFIG_DIFF:
                self.record("7", True, "work/config-changes.diff compares the live "
                            "file (first) with the approved file (second).")
            elif text == CONFIG_DIFF_REVERSED:
                self.record("7", False, "work/config-changes.diff has the inputs in "
                            "the wrong order: < lines should come from the live "
                            "file. Put evidence/web-02-live.conf first.")
            elif not text.strip():
                self.record("7", False, "work/config-changes.diff is empty. diff "
                            "prints nothing for identical files: compare "
                            "evidence/web-02-live.conf with "
                            "evidence/web-02-approved.conf, not two identical files.")
            else:
                self.record("7", False, "work/config-changes.diff is not the "
                            "saved output of diff evidence/web-02-live.conf "
                            "evidence/web-02-approved.conf.")
        lines = self.lines("7", "web-02.conf")
        if lines is None:
            return
        approved = self.ev.approved_conf
        if [line.rstrip() for line in lines] == approved:
            self.record("7", True, "work/web-02.conf matches the approved "
                        "configuration.")
            return
        live = read_lines(LAB_DIR / "evidence" / "web-02-live.conf")
        if lines == live:
            message = "has not been changed yet."
        else:
            differing = [str(i + 1) for i in range(max(len(lines), len(approved)))
                         if i >= len(lines) or i >= len(approved)
                         or lines[i].rstrip() != approved[i]]
            message = (f"still differs from the approved file (first difference at "
                       f"line {differing[0]}).")
        self.record("7", False, f"work/web-02.conf {message} Run diff "
                    "work/web-02.conf evidence/web-02-approved.conf to see what "
                    "remains, then repair it in nano.")

    # Final task ----------------------------------------------------------

    def part_final(self):
        name = "students-to-contact.txt"
        lines = self.lines("final", name)
        students_in_file = None
        if lines is not None:
            students_in_file = len([line for line in lines if line.strip()])
            expected = self.ev.students
            enrol_503 = set(expected)
            if lines == expected:
                self.record("final", True, f"work/{name} lists each affected "
                            "student once, sorted.")
            elif len(lines) != len(set(lines)):
                self.record("final", False, f"work/{name} lists a student more than "
                            "once. Students retried; remove repeats with sort "
                            "then uniq.")
            elif set(lines) - enrol_503:
                extra = sorted(set(lines) - enrol_503)[0]
                self.record("final", False, f"work/{name} includes {extra}, who had "
                            "no 503 response on /api/enrol. Read runbook Section 12 "
                            "again.")
            elif enrol_503 - set(lines):
                self.record("final", False, f"work/{name} is missing "
                            f"{len(enrol_503 - set(lines))} student(s) with a 503 "
                            "response on /api/enrol.")
            else:
                self.record("final", False, f"work/{name} has the right IDs but they "
                            "are not in sorted order.")
        lines = self.lines("final", "handover.txt")
        if lines is None:
            return
        spec = self.handover_spec(students_in_file)
        if not self.check_handover_lines("final", lines, spec):
            return
        if len([line for line in lines if line.strip()]) != len(spec):
            self.record("final", False, f"work/handover.txt should have exactly "
                        f"{len(spec)} lines. Remove the old rev 3 lines.")
            return
        conf = read_lines(self.work / "web-02.conf") or []
        if [line.rstrip() for line in conf] != self.ev.approved_conf:
            self.record("final", False, "work/handover.txt says 'Config: "
                        "reconciled', but work/web-02.conf still differs from "
                        "the approved file.")
            return
        self.record("final", True, "work/handover.txt is complete in rev 4 format.")


# ---------------------------------------------------------------- main

def find_attempt():
    for folder in [Path.cwd(), *Path.cwd().parents]:
        if (folder / ".attempt").is_file():
            return folder
    return None


def main(argv):
    wanted = argv[1:] or PARTS
    unknown = [part for part in wanted if part not in PARTS]
    if unknown:
        print(f"Unknown part: {unknown[0]}. Use one of: {', '.join(PARTS)}.")
        return 2
    attempt = find_attempt()
    if attempt is None:
        print("Run this checker from inside your lab attempt: run the cd command")
        print("printed by bash lab/start.sh (for example cd attempts/attempt-01),")
        print("then: python3 ../../lab/check.py")
        return 2

    checker = Checker(attempt)
    checker.check_evidence()
    for part in PARTS:
        if part in wanted:
            getattr(checker, f"part_{part}")()

    print(f"Checking {attempt}")
    print()
    for part, passed, message in checker.results:
        label = "Evidence" if part == "evidence" else (
            "Final" if part == "final" else f"Exp {part}")
        print(f"{'PASS' if passed else 'FAIL'}  {label:<8}  {message}")
    passed = sum(1 for _, ok, _ in checker.results if ok)
    total = len(checker.results)
    print()
    print(f"{passed} of {total} checks passed.")
    if passed < total:
        print("Fix one FAIL at a time, then run the checker again.")
        first = next((part for part, ok, _ in checker.results
                      if not ok and part != "evidence"), None)
        if first:
            name = "the final task" if first == "final" else f"Experiment {first}"
            print(f"Stuck on {name}? For a hint: python3 ../../lab/hint.py {first}")
    if wanted == PARTS:
        print()
        print("Not checked here: searching history with Ctrl+R, saving in nano and")
        print("moving or searching in less. Show these to your instructor.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
