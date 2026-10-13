# CourseDesk incident handover: a terminal tools lab

[![Test lab](https://github.com/dhruvgupta-24/software-engineering-terminal-lab/actions/workflows/test.yml/badge.svg)](https://github.com/dhruvgupta-24/software-engineering-terminal-lab/actions/workflows/test.yml)

Lab 2 for Introduction to Software Engineering. Learners practise seven terminal tools (`less`, `nano`, `cut`, `sort`, `uniq`, `history`, `diff`) by taking over an incident from a night on-call engineer.

coursedesk, the course registration portal of a fictional college, returned errors overnight. The night engineer left an incomplete handover note in a retired format. The learner reads the runbook, analyses the request log and pager alerts, compares the faulty server's live and approved configuration, and delivers a handover package: a 10-line handover note, a reconciled configuration file and the list of students whose enrolment failed.

**[Open in GitHub Codespaces](https://codespaces.new/dhruvgupta-24/software-engineering-terminal-lab?quickstart=1)** (resumes your existing Codespace if you have one)

## Start here

| You are | Open |
|---|---|
| A student | [`book/lab-book.pdf`](book/lab-book.pdf), then follow "Set up" below |
| A reviewer | [`reviewer/REVIEWER_NOTES.md`](reviewer/REVIEWER_NOTES.md): solution, expected results, requirement coverage, test evidence |
| Editing the lab | `book/lab-book.md` (book source), `lab/` (evidence, setup, checker), `tests/` |

| Path | Contents |
|---|---|
| `book/` | Student lab book: PDF (9 pages), Markdown source, `build_pdf.py` and `style.css` |
| `lab/evidence/` | Original evidence: runbook, request log, alert log, live and approved configuration, draft handover |
| `lab/start.sh` | Creates a new attempt folder |
| `lab/check.py` | Read-only checker |
| `lab/hint.py` | Two-level hints per experiment, without answers |
| `lab/setup/postcreate.sh` | Codespace setup, run automatically |
| `lab/dev/` | Data generator and evidence hash updater, for maintainers |
| `reviewer/` | Reviewer notes and the reference solution script |
| `tests/` | Setup and checker tests; book command and output tests; interactive key tests |
| `.devcontainer/` | Codespace definition: image, settings, SSH server, setup command |
| `.github/workflows/test.yml` | On every push: runs all three test suites, and builds the dev container as Codespaces does |

## Prerequisites

A GitHub account with Codespaces access, and Lab 1 knowledge: `cd`, `pwd`, `ls`, `cat`, `cp`, `rm`, `grep`, pipes (`|`) and output redirection (`>`). The Codespace provides Bash, `nano`, `less`, GNU coreutils, `diff` and Python 3.

## Set up

1. Open the Codespaces link above (or **Code → Codespaces → Create codespace on main**) and wait for setup. `postcreate.sh` installs any missing tools, adds the shell settings below, runs the setup and checker test suite as a self-test (about 2 seconds) and prints `Lab self-test: 37 passed, 0 failed.` then `Setup complete`. If anything fails it stops with the failing checks listed. Then open a new terminal (``Ctrl+Shift+` `` or **☰ → Terminal → New Terminal**).
2. At the repository root, run `bash lab/start.sh`, then run the exact `cd` command it prints (the folder number differs for each attempt). On a first attempt it prints:

```text
Created attempt-01

  evidence/   original files (read-only)
  work/       your working copies and results

Move into your lab root with:

  cd /workspaces/software-engineering-terminal-lab/attempts/attempt-01
```

The attempt folder is the **lab root**; every command in the book runs from there. `evidence/` holds write-protected copies of the originals (overwriting one fails with `Permission denied`). `work/` holds the working copies `handover.txt` and `web-02.conf` and every file the learner creates.

**Fresh attempt.** Run `bash lab/start.sh` again from the repository root. It creates the next folder (`attempt-02`, ...) and prints the `cd` command for it. Existing attempts are never modified or deleted. Attempts are git-ignored and stay in the Codespace.

What the Codespace configures:

| Setting | Why |
|---|---|
| `terminal.integrated.sendKeybindingsToShell` | Ctrl+R, Ctrl+G, Ctrl+O, Ctrl+X and Ctrl+K reach the terminal instead of VS Code |
| Copilot and inline AI suggestions disabled | Students type and reason through each command themselves |
| `history -a` in `PROMPT_COMMAND`, `histappend` | Each command is saved immediately, so Ctrl+R finds it even in a new terminal |
| `LC_COLLATE=C` | `sort` gives every learner the same order |
| Welcome message (`lab/setup/welcome.sh`) | A new terminal at the repository root shows the next command: `bash lab/start.sh`, or the `cd` for the latest attempt. It only prints; it never creates or changes files. Turn it off with `export COURSEDESK_NO_WELCOME=1` in `~/.bashrc`, or delete the `# coursedesk-lab welcome` lines there. |

## Validation

From the lab root:

```bash
python3 ../../lab/check.py          # all 14 checks
python3 ../../lab/check.py 5        # one experiment: 2 to 7, or final
python3 ../../lab/hint.py 5         # a hint for Experiment 5; add 2 for a stronger one
```

The checker confirms the evidence is unchanged (SHA-256 in `lab/evidence.sha256`), checks the content, line order and structure of each required file in `work/`, and prints `PASS` or `FAIL` with a specific reason. It exits 0 only when every check passes and never creates, changes or deletes files. A fresh attempt scores `1 of 14` (the evidence check); a complete one `14 of 14`. Below the score it shows a progress bar and one `PASS` or `FAIL` per experiment, in colour in a terminal (`NO_COLOR=1` turns colour off; piped output never has colour). Example:

```text
FAIL  Exp 5     work/alert-types.txt still has repeated lines. uniq removes only adjacent repeats; sort first, then uniq.
```

The checker cannot observe interactive use of `history`, `nano` or `less`; the lab book has an instructor sign-off table for those.

`diff` output is expected in Experiment 7B and in `work/config-changes.diff`, where the differences are the answer. In 7A and after the repair in 7C, the expected result is no output: the files are identical.

## Tests

```bash
bash tests/run-tests.sh                 # 45 tests: setup, attempts, checker, hints, progress, welcome, 23 mistakes
bash tests/book-claims.sh               # 43 tests: the book's commands and every output it quotes
python3 tests/interactive-smoke.py      # 19 tests: the book's keys in bash, nano and less, colour, welcome (Linux)
```

All three run on a temporary copy and never touch real attempts. Rebuild the PDF after editing the book with `pip install markdown && python3 book/build_pdf.py` (needs Chrome, Chromium or Edge; set `CHROME=/path` if it is not found).
