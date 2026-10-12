#!/usr/bin/env python3
"""Check the interactive key sequences taught in the lab book (Linux only).

Runs Bash, nano and less in a pseudo-terminal and sends the same keys a
student types: history search with Ctrl+R, Right Arrow and Ctrl+G; saving
and exiting nano; paging and searching in less. Each step waits for the
text it expects on screen, so a slow machine does not cause false failures.
It works on a temporary copy of the repository with a temporary HOME, using
the shell settings from lab/setup/postcreate.sh. From the repository root:

    python3 tests/interactive-smoke.py

This tests the terminal programs, not the browser or VS Code keyboard layer.
"""
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT = "LAB-PROMPT> "
# A finished command leaves the prompt at the start of a new line. Readline
# also redraws "PROMPT command" when a search match is accepted, before the
# command runs, so waiting for PROMPT alone could return too early.
DONE = "\n" + PROMPT
CTRL = {c: chr(ord(c) & 0x1F) for c in "egkorx"}
RIGHT, DOWN, END = "\x1b[C", "\x1b[B", "\x1b[F"
failures = 0


def clean(text):
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[=>]|[\x08\r]", "", text)


def result(name, ok):
    global failures
    failures += not ok
    print(("ok    " if ok else "FAIL  ") + name, flush=True)


class Terminal:
    def __init__(self, cwd, env):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(cwd)
            os.execvpe("bash", ["bash", "-i"], env)
        self.keys("", PROMPT)
        self.run("stty cols 160 rows 30")

    def keys(self, keys, until=None, timeout=10):
        """Send keys; return screen text, waiting until `until` appears."""
        if keys:
            os.write(self.fd, keys.encode())
        out = ""
        end = time.time() + (timeout if until else 0.5)
        while time.time() < end:
            ready, _, _ = select.select([self.fd], [], [], 0.05)
            if ready:
                try:
                    out += os.read(self.fd, 65536).decode(errors="replace")
                except OSError:
                    break
                if until and until in clean(out):
                    return clean(out)
        if until:
            print(f"      (waited {timeout}s without seeing {until!r})", flush=True)
        return clean(out)

    def run(self, command):
        """Type a command, press Enter and wait for the next prompt."""
        return self.keys(command + "\r", DONE)

    def close(self):
        os.write(self.fd, b"exit\r")
        os.waitpid(self.pid, 0)


def main():
    tmp = tempfile.mkdtemp()
    try:
        repo = os.path.join(tmp, "repo")
        home = os.path.join(tmp, "home")
        os.makedirs(home)
        for folder in ["lab", "tests", "reviewer"]:
            shutil.copytree(os.path.join(REPO, folder), os.path.join(repo, folder))
        # /etc/bash.bashrc sets PS1, so set the marker prompt in ~/.bashrc,
        # which postcreate.sh then extends exactly as in a Codespace.
        with open(os.path.join(home, ".bashrc"), "w") as bashrc:
            bashrc.write(f"PS1='{PROMPT}'\n")
        env = dict(os.environ, HOME=home, TERM="xterm",
                   HISTFILE=os.path.join(home, ".bash_history"))
        subprocess.run(["bash", "lab/setup/postcreate.sh"], cwd=repo, env=env,
                       check=True, capture_output=True)
        subprocess.run(["bash", "lab/start.sh"], cwd=repo, env=env, check=True,
                       capture_output=True)
        attempt = os.path.join(repo, "attempts", "attempt-01")
        work = lambda name: os.path.join(attempt, "work", name)
        read = lambda name: open(work(name)).read() if os.path.exists(work(name)) else ""

        t = Terminal(attempt, env)
        t.run('cut -d "|" -f 1,2,3 evidence/requests.log > work/time-server-status.txt')

        # less: every key from Experiment 1, on piped output as in 3B
        t.keys('grep -F "|503" work/time-server-status.txt | less\r', "01:14:07")
        for key in [" ", "b", "G", "g"]:
            t.keys(key)
        t.keys("/web-01\r", "web-01")
        t.keys("n")
        t.keys("N")
        out = t.keys("q", PROMPT)
        result("less: Space b G g / n N q returns to the prompt", PROMPT in out)

        t.keys("less evidence/runbook.txt\r", "COURSEDESK OPERATIONS RUNBOOK")
        out = t.keys("/Rota\r", "Pattern not found")
        result("less: case-sensitive search reports 'Pattern not found'",
               "Pattern not found" in out)
        t.keys("\r")
        t.keys("q", PROMPT)

        # history list and filter
        t.run("echo first-one")
        t.run("echo second-one")
        out = t.run("history 10")
        result("history 10 lists earlier commands", "echo first-one" in out and "grep -F" in out)
        result("history | grep -F filters the list",
               "echo first-one" in t.run('history | grep -F "first-one"'))

        # Ctrl+R, Ctrl+R again for an older match, Enter runs it
        t.keys(CTRL["r"], "reverse-i-search")
        t.keys("echo ", "second-one")
        t.keys(CTRL["r"], "first-one")
        out = t.keys("\r", DONE)
        result("Ctrl+R twice reaches the older match",
               "\nfirst-one\n" in out)

        # Ctrl+G cancels without running the match
        t.run("touch work/marker")
        t.run("rm work/marker")
        t.keys(CTRL["r"], "reverse-i-search")
        t.keys("touch work/mark", "touch work/marker")
        t.keys(CTRL["g"])
        t.keys("\r", DONE)
        result("Ctrl+G cancels: the matched command does not run",
               not os.path.exists(work("marker")))

        t.keys(CTRL["r"], "reverse-i-search")
        out = t.keys("zzqq", "failed reverse-i-search")
        result("Ctrl+R shows 'failed reverse-i-search' for unknown text",
               "failed reverse-i-search" in out)
        t.keys(CTRL["g"])
        t.keys("\r", PROMPT)

        # Validation: after the deliberate mistake, the book's search text
        # recalls the correct 5B command, not the newer wrong one
        t.run('cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq > work/alert-types.txt')
        t.run('cut -d "|" -f 2,3 evidence/alerts.log | uniq > work/alert-types.txt')
        t.keys(CTRL["r"], "reverse-i-search")
        t.keys("sort | uniq > work/alert", "alert-types.txt")
        t.keys("\r", DONE)
        lines = read("alert-types.txt").splitlines()
        result("Ctrl+R 'sort | uniq > work/alert' recalls the correct 5B command",
               len(lines) == 5 and lines == sorted(lines))

        # Experiment 6C: Ctrl+R |503, Right Arrow, End, edit, Enter
        t.keys(CTRL["r"], "reverse-i-search")
        t.keys("|503", "| less")
        t.keys(RIGHT)
        t.keys(END)
        t.keys("\x7f" * len("| less"))
        t.run('| cut -d "|" -f 2 | sort | uniq -c | sort -n -r > work/errors-by-server.txt')
        result("Right Arrow accepts a match for editing (6C pipeline saved)",
               read("errors-by-server.txt").split() == ["31", "web-02", "4", "web-03", "2", "web-01"])

        # nano: new file without a final Enter, Ctrl+O, Enter, Ctrl+X
        t.keys("nano work/findings.txt\r", "New File")
        t.keys("Handover format: rev 4\rIncident lead: Tomas Reyes")
        t.keys(CTRL["o"], "File Name to Write")
        t.keys("\r", "Wrote")
        t.keys(CTRL["x"], PROMPT)
        result("nano: new file saved with exactly two lines",
               read("findings.txt") == "Handover format: rev 4\nIncident lead: Tomas Reyes\n")

        # nano: edit an existing file, Ctrl+X asks to save
        t.keys("nano work/handover.txt\r", "Owner: Sam Okafor")
        t.keys(DOWN)
        t.keys(CTRL["k"])
        t.keys("Service: coursedesk\r")
        t.keys(CTRL["k"])
        t.keys("Escalation: Tomas Reyes\r")
        out = t.keys(CTRL["x"], "Save modified buffer")
        result("nano: Ctrl+X with changes asks 'Save modified buffer?'",
               "Save modified buffer" in out)
        t.keys("y", "File Name to Write")
        t.keys("\r", PROMPT)
        result("nano: existing file edited and saved",
               read("handover.txt").splitlines()[:3] ==
               ["Incident: INC-2417", "Service: coursedesk", "Escalation: Tomas Reyes"])

        t.keys("nano work/handover.txt\r", "Escalation: Tomas Reyes")
        out = t.keys(CTRL["x"], PROMPT)
        result("nano: reopen and Ctrl+X without changes exits with no prompt",
               "Save modified buffer" not in out and PROMPT in out)

        out = t.keys("nano evidence/web-02-approved.conf\r", "is unwritable")
        result("nano: an evidence file opens as unwritable", "is unwritable" in out)
        t.keys(CTRL["x"], PROMPT)
        t.close()

        # A new terminal can find the previous terminal's commands
        t = Terminal(attempt, env)
        t.keys(CTRL["r"], "reverse-i-search")
        out = t.keys("first-one", "echo first-one")
        result("a new terminal finds earlier commands with Ctrl+R", "echo first-one" in out)
        t.keys(CTRL["g"])
        t.close()
    finally:
        subprocess.run(["chmod", "-R", "u+w", tmp])
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print(f"{failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
