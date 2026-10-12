# Reviewer notes: CourseDesk incident handover lab

**Scenario.** Deploy D-118 cut `db.pool_size` on `web-02` from 40 to 4, so `web-02` refused requests with 503 during the overnight registration window. The learner investigates the runbook, request log, alerts and configuration, and delivers a corrected 10-line handover note, a reconciled `web-02.conf` and the list of students whose enrolment failed. All evidence is original (`lab/dev/generate_logs.py`, fixed seed; runbook and configs written by hand).

## Tools mapped to experiments

| Exp | Tool | What the learner does | Result used later |
|---|---|---|---|
| 1 | `less` | Space, b, G, g; `/` search; n, N to step from a RETIRED to the CURRENT section; q | Note format, incident lead, log field numbers |
| 2 | `nano` | Edit `work/handover.txt`, create `work/findings.txt`; Ctrl+O, Enter, Ctrl+X; reopen | Note lines 1 to 3; findings file |
| 3 | `cut` | One field, several fields, quoted `-d "|"`; row order gives the first 503 | `First 503:` |
| 4 | `sort` | Text vs `-n`, `-r`, saved; `sort f > f` empties the file | `Slowest request:` |
| 5 | `uniq` | Adjacent-only repeats, `sort` first, `-c`; order changes the result | `503 responses:` |
| 6 | `history` | `history 10`, `history | grep`, Ctrl+R twice, Ctrl+G, Right Arrow to edit the Exp 3 command | `Faulty server:` |
| 7 | `diff` | Identical and changed files, markers, input order, saved diff, repair and verify | `Cause:`, `Config:` |
| Final | all | Requirements only: student list, complete note, verify | Handover package |

## Reference solution and expected results

`reviewer/solution.sh` produces every graded file. Key commands:

```bash
cut -d "|" -f 1,2,3 evidence/requests.log > work/time-server-status.txt
cut -d "|" -f 4,5 evidence/requests.log | sort -n -r > work/latency-ranked.txt
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq -c > work/alert-counts.txt
grep -F "|503" work/time-server-status.txt | cut -d "|" -f 2 | sort | uniq -c | sort -n -r > work/errors-by-server.txt
diff evidence/web-02-live.conf evidence/web-02-approved.conf > work/config-changes.diff
grep -F "|503|" evidence/requests.log | grep -F "|/api/enrol|" | cut -d "|" -f 6 | sort | uniq > work/students-to-contact.txt
```

Final `work/handover.txt`:

```text
Incident: INC-2417
Service: coursedesk
Escalation: Tomas Reyes
Faulty server: web-02
First 503: 01:14:07
503 responses: 37
Slowest request: 10093 ms on /api/enrol
Cause: db.pool_size changed from 40 to 4
Config: reconciled
Students to contact: 9
```

Other results: 503s by server 31 / 4 / 2 (web-02, web-03, web-01); statuses 200: 108, 304: 11, 404: 4, 503: 37, 504: 5; config diff `7c7`, `9d8`, `10a10`; `web-02.conf` identical to the approved file; 9 students (S24026, S24206, S24299, S24446, S24505, S24514, S24738, S24931, S24940). Traps: S24916 (503 only on `/api/timetable`) and S24656 (only 504s, retried) are excluded. Optional "Going further" answers: `/api/enrol` had the most 503s (18); S24299, S24505 and S24931 each received three.

## Validation and test evidence

`python3 ../../lab/check.py [2-7|final]` runs 14 checks (evidence hashes and 12 result files), prints a specific reason for each FAIL (for example `uniq removes only adjacent repeats; sort first, then uniq`), never writes files, and leaves interactive skills to the book's sign-off table.

| Test (Codespace image, non-root user, Docker) | Result |
|---|---|
| `bash tests/run-tests.sh`: setup, attempts, read-only evidence, checker read-only, solution 14/14, hints, 23 deliberate mistakes | 37 passed |
| `python3 tests/interactive-smoke.py`: the book's keys in bash, nano and less, waiting for real screen output; also at a quarter CPU | 15 passed |
| `bash tests/book-claims.sh`: every command in the book run in order; every quoted output, message and count checked | 43 passed |
| `postcreate.sh` twice (also runs the self-test) | Settings added once; self-test passes |
| Book followed end to end by a separate AI agent given only the book (no solution files) | 14/14; its 15 findings were fixed |

**Fresh GitHub Codespace** (2-core, created from `main` on 2026-10-12, tested over `gh codespace ssh`): the container built from `.devcontainer/` (Debian 12, user `vscode`); setup printed `Lab self-test: 34 passed, 0 failed.` and `Setup complete`; all three suites passed (34, 36 and 15 checks); `start.sh` created `attempt-01` (checker 1/14 fresh, 14/14 after the reference solution); a second run created `attempt-02` and left `attempt-01` byte-identical; evidence was read-only; a second setup run added no duplicate settings; `git status` stayed clean. Not testable over SSH: whether the browser passes Ctrl+R, Ctrl+G and Ctrl+O to the terminal, which needs a person at the keyboard.

**GitHub Actions** ([runs](https://github.com/dhruvgupta-24/software-engineering-terminal-lab/actions)): every push runs the three suites in the Codespace image and builds the dev container with the official devcontainer CLI, including the setup self-test. All runs passed.


## Three improvements over the reference lab

1. **One connected investigation.** The reference practises on unrelated files (names, scores, a timetable) and repeats similar tasks in a challenge. Here every experiment answers one question about the incident and fills one line of the handover note, so the final task depends on earlier results.
2. **Mistakes demonstrated and diagnosed.** Learners run the failing versions (unquoted delimiter, `sort f > f`, `uniq -c` without `sort`, swapped `diff` inputs); each experiment has a "Watch for" box; the checker names the mistake and fix and points to a two-level hint (`lab/hint.py`) that never gives the answer. The reference checker prints only `CHECK <file>`.
3. **History used for real work, with the keys configured.** The learner recalls and extends their own Experiment 3 pipeline to find the faulty server, rather than searching two commands typed only to make a trail. The Codespace sends Ctrl+R, Ctrl+G, Ctrl+O and Ctrl+K to the shell and saves history after every command; the reference configures neither.

## Time, assumptions and blockers

- Expected learner time: about 100 minutes (90 to 110), as planned in the lab book: setup 5, Experiments 1 to 7 at 10 to 12 each, final task 15, validation 10. The author, who already knew the answers and the tools, completed the lab in 34 minutes; a beginner reading each explanation, writing predictions and recovering from mistakes needs roughly three times as long. Not yet timed with a student.
- Actual time spent: 34 minutes to complete the lab end to end (started 11:30 PM, finished 12:04 AM the following day).
- Assumptions: Lab 1 commands are known; Bash in the Codespace image as the non-root `vscode` user; `LC_COLLATE=C` (the data also sorts the same under `en_US.UTF-8`); one shared dataset; solution and checker visible, as in the reference.
- Blockers: Nothing stopped the lab. During development, the Codespace build failed once because the base image ships a Yarn package source with an expired signing key, so `apt-get update` failed and GitHub fell back to a recovery container. `.devcontainer/Dockerfile` now removes that source, and CI builds the dev container on every push. During my own run, my first reverse search in Experiment 6 ran the recalled `sort | uniq -c` command again instead of placing it on the prompt for editing, and left a stray `uniq -c`; I also ran the Experiment 3 `grep -F "|503"` command on its own before adding the per-server pipeline. I recalled the command again, completed the pipeline, and the attempt finished with 14 of 14 checks passing.

## AI use

I took assistance from Claude Code throughout the assignment for implementation, drafting, debugging and review. I chose the scenario, defined the requirements and writing standards, guided the implementation, reviewed each result against the assignment brief and the reference lab, and requested changes until the outcome met them.

I then completed the lab myself as a student in my own Codespace, running the commands, troubleshooting my mistakes (see Blockers) and finishing with 14 of 14 checks passing.