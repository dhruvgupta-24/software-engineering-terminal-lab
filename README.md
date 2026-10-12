# CourseDesk incident handover: a terminal tools lab

Lab 2 for Introduction to Software Engineering. Learners practise seven terminal tools (`less`, `nano`, `cut`, `sort`, `uniq`, `history`, `diff`) while taking over an incident from a night on-call engineer.

**Scenario.** coursedesk, the course registration portal of a fictional college, returned errors overnight. The night engineer left an incomplete handover note in an old format. The learner reads the runbook, analyses the request log and pager alerts, compares the live and approved configuration of the faulty server, and delivers a corrected handover package: a 10-line handover note, a reconciled configuration file and the list of students whose enrolment failed.

**Launch:** [Open in GitHub Codespaces](https://codespaces.new/dhruvgupta-24/software-engineering-terminal-lab)

| Path | Contents |
|---|---|
| `book/lab-book.pdf` | Student lab book (7 pages) |
| `book/lab-book.md` | Editable source of the book; `book/build_pdf.py` and `book/style.css` build the PDF |
| `lab/evidence/` | Original evidence: runbook, request log, alert log, live and approved configuration, draft handover |
| `lab/start.sh` | Creates a new attempt folder |
| `lab/check.py` | Read-only checker |
| `reviewer/REVIEWER_NOTES.md` | Reference solution, expected results, tool coverage, design notes |
| `reviewer/solution.sh` | Produces the reference results in an attempt (for reviewers and tests) |
| `reviewer/RECORDING_OUTLINE.md` | Walkthrough outline with timestamps |
| `tests/run-tests.sh` | Automated tests for setup and the checker |

## Prerequisites

- A GitHub account with Codespaces access.
- Lab 1 knowledge: `cd`, `pwd`, `ls`, `cat`, `cp`, `rm`, `grep`, pipes (`|`) and output redirection (`>`).

Everything else is provided by the Codespace: Bash, `nano`, `less`, GNU coreutils, `diff` and Python 3 (for the checker).

## Set up in a Codespace

1. Open the launch link above, or on the repository page choose **Code → Codespaces → Create codespace on main**.
2. Wait for the container to build. `.devcontainer/devcontainer.json` runs `lab/setup/postcreate.sh`, which installs any missing tools and adds a few shell settings to `~/.bashrc`. The terminal prints `Setup complete` when it has finished.
3. If a terminal was already open before setup finished, open a new one (**Terminal → New Terminal**) so the settings apply.
4. At the repository root, create an attempt and move into it:

```bash
bash lab/start.sh
cd attempts/attempt-01
```

Expected output of `start.sh`:

```text
Created attempt-01

  evidence/   original files (read-only)
  work/       your working copies and results

Move into your lab root with:

  cd /workspaces/software-engineering-terminal-lab/attempts/attempt-01
```

The attempt folder is the learner's **lab root**. All commands in the book are run from there.

What the setup configures:

| Setting | Why |
|---|---|
| `terminal.integrated.sendKeybindingsToShell: true` | Sends Ctrl+R, Ctrl+G, Ctrl+O, Ctrl+X and Ctrl+K to the terminal instead of VS Code |
| `history -a` in `PROMPT_COMMAND`, `histappend`, larger `HISTSIZE` | Every command is saved immediately, so earlier commands can be found with Ctrl+R even in a new terminal |
| `LC_COLLATE=C` | `sort` uses the same character order for every learner |

## Starting a fresh attempt

From the repository root:

```bash
bash lab/start.sh
```

Each run creates the next folder (`attempt-02`, `attempt-03`, ...) with fresh copies of the evidence and working files. Existing attempts are never modified or deleted, so earlier work stays available for review. Attempts are listed in `.gitignore` and stay in the Codespace.

Inside an attempt:

- `evidence/` holds read-only copies of the original files. Attempting to overwrite one fails with `Permission denied`.
- `work/` holds the working copies `handover.txt` and `web-02.conf`, and every file the learner creates.

## Validation

From the lab root:

```bash
python3 ../../lab/check.py          # all checks
python3 ../../lab/check.py 5        # one experiment: 2, 3, 4, 5, 6, 7 or final
```

The checker:

- confirms that the original evidence is unchanged (SHA-256, listed in `lab/evidence.sha256`);
- checks content, line order and structure of every required file in `work/`;
- prints `PASS` or `FAIL` with a specific reason for each of 14 checks and exits with status 0 only when all pass;
- never creates, changes or deletes files.

It cannot observe interactive use of `history`, `nano` or `less`. Those are demonstrated live using the sign-off table in the lab book.

Expected output on a fresh attempt: `1 of 14 checks passed` (only the evidence check). Expected output for a complete attempt: `14 of 14 checks passed`. Example of a failing check:

```text
FAIL  Exp 5     work/alert-types.txt still has repeated lines. uniq removes only adjacent repeats; sort first, then uniq.
```

`diff` output is expected in two places (Experiment 7B and `work/config-changes.diff`), where the differences are the answer. In Experiment 7A and after repairing `work/web-02.conf`, the expected result is no output, which means the files are identical.

## Tests for maintainers

```bash
bash tests/run-tests.sh
```

Runs on a temporary copy of the repository and checks attempt creation, read-only evidence, attempt preservation, that the checker leaves files unchanged, that the reference solution passes, and that 23 common mistakes each produce the correct FAIL message.

Rebuild the book after editing `book/lab-book.md`:

```bash
pip install markdown
python3 book/build_pdf.py     # needs Chrome, Chromium or Edge; set CHROME=/path if not found
```
