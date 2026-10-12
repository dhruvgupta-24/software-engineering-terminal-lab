# Reviewer notes: CourseDesk incident handover lab

These notes sit outside the student book's page limit. They give the reference solution, expected results, how each required behaviour is covered, and how the lab was checked.

## Scenario in one paragraph

coursedesk, a fictional college's course registration portal, returned 503 errors overnight. Deploy D-118 had changed `web-02`'s configuration: `db.pool_size` dropped from 40 to 4, `debug.sql_trace = on` was added and `cache.course_list_ttl = 300` was removed. The learner is the day-shift junior developer. They read the runbook, analyse the request log and pager alerts, compare the live and approved configuration, and deliver a corrected handover package: a 10-line handover note, a reconciled `web-02.conf` and the list of students whose enrolment failed.

All evidence is original and written for this lab. `requests.log` and `alerts.log` are produced by `lab/dev/generate_logs.py` with a fixed seed. The runbook, configuration files and draft handover were written by hand.

## How each experiment feeds the final result

| Experiment | Tool | Fact or file produced | Used later in |
|---|---|---|---|
| 1 | less | Current format is rev 4; incident lead Tomas Reyes; log field numbers | 2 (handover lines), 3 to 7 (field numbers), final (format) |
| 2 | nano | `handover.txt` lines 1 to 3; new `findings.txt` | final (note completed in the same file) |
| 3 | cut | `statuses.txt`; `time-server-status.txt`; first 503 at 01:14:07 | 5D (counts), 6 (recalled command), final |
| 4 | sort | `latency-ranked.txt`; slowest request 10093 ms on /api/enrol | final |
| 5 | uniq | alert summary; `status-counts.txt`; 37 responses with status 503 | final |
| 6 | history | `errors-by-server.txt`; faulty server web-02 (31 of 37) | final |
| 7 | diff | `config-changes.diff`; repaired `web-02.conf`; cause | final (`Config: reconciled` is only true after this) |
| Final | all | `students-to-contact.txt` (9 IDs); complete `handover.txt` | handover package |

## Reference solution

`reviewer/solution.sh` produces every graded file non-interactively (nano edits are replaced by `printf` and `cp`). The commands a student types are:

```bash
# Experiment 3
cut -d "|" -f 3 evidence/requests.log > work/statuses.txt
cut -d "|" -f 1,2,3 evidence/requests.log > work/time-server-status.txt
grep -F "|503" work/time-server-status.txt | less          # first line: 01:14:07|web-02|503

# Experiment 4
cut -d "|" -f 4,5 evidence/requests.log | sort -n -r > work/latency-ranked.txt

# Experiment 5
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq > work/alert-types.txt
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq -c > work/alert-counts.txt
sort work/statuses.txt | uniq -c > work/status-counts.txt

# Experiment 6 (recalled with Ctrl+R "|503", Right Arrow, then edited)
grep -F "|503" work/time-server-status.txt | cut -d "|" -f 2 | sort | uniq -c | sort -n -r > work/errors-by-server.txt

# Experiment 7
diff evidence/web-02-live.conf evidence/web-02-approved.conf > work/config-changes.diff
nano work/web-02.conf        # 4 -> 40, delete debug.sql_trace, add cache.course_list_ttl = 300
diff work/web-02.conf evidence/web-02-approved.conf          # no output

# Final task
grep -F "|503|" evidence/requests.log | grep -F "|/api/enrol|" | cut -d "|" -f 6 | sort | uniq > work/students-to-contact.txt
nano work/handover.txt
```

### Expected files

`work/handover.txt`

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

`work/students-to-contact.txt`: `S24026 S24206 S24299 S24446 S24505 S24514 S24738 S24931 S24940` (one per line).

`work/errors-by-server.txt`:

```text
     31 web-02
      4 web-03
      2 web-01
```

`work/status-counts.txt`: 200 = 103, 304 = 11, 404 = 4, 503 = 37, 504 = 5 (160 requests).

`work/alert-types.txt` (5 lines) and `work/alert-counts.txt`:

```text
      4 DBPoolExhausted|web-02
      1 DiskSpaceLow|web-03
      6 HighErrorRate|web-02
      1 HighErrorRate|web-03
      2 HighLatency|web-01
```

`work/config-changes.diff`:

```text
7c7
< db.pool_size = 4
---
> db.pool_size = 40
9d8
< debug.sql_trace = on
10a10
> cache.course_list_ttl = 300
```

`work/latency-ranked.txt` starts `10093|/api/enrol`, `10047|/login`, `10031|/api/enrol`. `work/web-02.conf` is byte-identical to `evidence/web-02-approved.conf`. `work/findings.txt` is the learner's notebook; the checker only requires at least two lines.

### Answers to the questions in the book

| Where | Expected answer |
|---|---|
| 1B | Two headings contain `NOTE FORMAT`. Rev 4 is current. The first match (Section 9) is marked RETIRED. |
| 1C | Incident lead Tomas Reyes (Ravi Menon is on the archived rota). Fields: status 3, response time 4, endpoint 5, student ID 6. |
| 2A | nano does not ask to save after an unchanged reopen, because the buffer matches the file on disk: the earlier save worked. |
| 3A | Unquoted `|` splits the line into two commands: `cut -d` fails with "option requires an argument" and `-f` is "command not found". |
| 3B | Fields 4 and 5 are printed in file order (time before endpoint) whatever order `-f` lists them in. |
| 4A | No. Text order starts `10012`, `10020`, ..., and `10093` is the 5th line. With `-n` it is the last line. |
| 4C | `cat` shows nothing: the shell empties the destination before `sort` reads it. |
| 5A | 14 lines in, 10 out. `HighErrorRate|web-02`, `DBPoolExhausted|web-02` and `HighLatency|web-01` still repeat. |
| 5C | Without `sort`, `uniq -c` shows `HighErrorRate|web-02` as groups of 3, 2 and 1 instead of 6. |
| 7B | `db.pool_size` changed from 40 (approved) to 4 (live); `debug.sql_trace = on` was added by the deploy; `cache.course_list_ttl = 300` is missing from live. Swapping the inputs swaps `<` and `>` and turns `a` into `d` (and `d` into `a`). |
| Final | Order: grep (503, then /api/enrol), cut field 6, sort, uniq. `sort` must come first because `uniq` only removes adjacent repeats and students retried at different times (18 matching rows, 15 lines after `uniq` alone, 9 after `sort | uniq`). |

Traps built into the data: S24916 had 503s only on `/api/timetable`; S24656 had only 504s on `/api/enrol` (Section 11 says these were retried). The slowest request (10093 ms) is a 504, which is why the handover line asks for the slowest request, not the slowest 503.

## Required behaviour coverage

| Requirement | Where it is taught and used |
|---|---|
| `history 10`, filter earlier commands | 6A: `history 10`, `history | grep -F "uniq"` |
| Ctrl+R, repeat search, Right Arrow, Ctrl+G | 6B (Ctrl+R, Ctrl+R again, Ctrl+G), 6C (Ctrl+R, Right Arrow, edit, Enter) on commands typed in Experiments 3 and 5; validation section uses Ctrl+R again |
| nano: edit existing, create new, Ctrl+O + Enter, Ctrl+X, reopen | 2A (existing, reopen and observe no save prompt), 2B (new file), 7C and final (further edits) |
| less: Space, b, g, G, /, n, N, q | 1A (Space, b, G, g), 1B (/, n, N), 1C (independent searches), 3A, 4A, 4B (paging pipeline output), final |
| sort: text vs `-n`, `-r`, save | 4A (text vs numeric), 4B (`-n -r` saved), 5C and 6C (`sort -n -r` on counts) |
| uniq: adjacent, sort first, `-c` | 5A (adjacent only), 5B (sort then uniq), 5C (`-c`, order comparison), 5D, 6C, final |
| cut: one and several fields, `-d`, `-f`, quoting, row order | 3A (one field, unquoted error demo), 3B (several fields, row order used to find the first 503, field order observation), 4, 5, final |
| diff: identical, changed, input order, markers, save, repair, verify | 7A, 7B (marker table, swap prediction), save to file, 7C (repair and verify with empty output) |
| Pipes, `>`, quoting | Throughout; quoting of `"|"` explained in 3A |
| Processing order changes the result | 5C (`uniq -c` with and without `sort`); final question on why `sort` precedes `uniq` |
| Input and destination of `>` must differ | 4C demonstration on a scratch copy; evidence is write-protected |
| Deliberate wrong result, failed check, fix, pass | Validation section of the book (uniq without sort on `alert-types.txt`) |
| When diff output is expected | 7 intro, 7B save step, and the validation section |

## Validation design

`lab/check.py` (Python 3 standard library only) reads the attempt and prints one PASS or FAIL line per check with a reason, a score out of 14, and exits 0 only when everything passes. `python3 ../../lab/check.py N` checks one experiment.

- **Evidence integrity.** Every file in the attempt's `evidence/` and in `lab/evidence/` is compared with the SHA-256 values in `lab/evidence.sha256`. The attempt's evidence is also made read-only by `start.sh`.
- **Expected values are derived** from the original evidence at run time (counts, first 503, slowest request, student list), so the checker does not hard-code the answers it is testing, except the diff text, the incident ID, the incident lead and the cause line.
- **Specific feedback** for the mistakes students make most often: sorted `cut` output, wrong field, text sort instead of `-n`, missing `-r`, a file emptied by redirecting onto its own input, `uniq` without `sort`, unranked counts, 504s counted as 503s, reversed diff inputs, a saved diff of identical files, unrepaired or partly repaired configuration, duplicate or wrongly filtered student IDs, archived escalation contact, reversed cause values, old rev 3 lines left in the note, and `Config: reconciled` written before the configuration matches.
- **Read-only.** The checker never opens a file for writing. The test suite hashes the whole attempt before and after running the checker.
- **Interactive skills are not inferred from files.** The checker says so in its output. The book's sign-off table lists what the instructor watches for `history`, `nano` and `less`.

`tests/run-tests.sh` runs 34 tests on a temporary copy of the repository: attempt creation, read-only evidence, fresh attempt fails, reference solution passes 14 of 14, checker leaves files unchanged, a second attempt preserves the first, single-part mode, running from a subfolder, and 23 deliberate mistakes that must each produce their specific FAIL message.

## Three improvements over the reference lab

1. **One chain of evidence instead of separate practice and challenge sets.** In the reference, the guided experiments use unrelated practice files (names, scores, a timetable) and the challenge uses a second copy of similar data. Here every experiment works on the same incident and produces a fact or file the final handover needs; the final task cannot be completed without the earlier results, and the learner even finds the field numbers for `cut` in the runbook with `less` before using them.
2. **Mistakes are demonstrated and diagnosed, not only warned about.** The reference says "never use the same file as both input and destination" and "uniq before sort is not enough". This lab has the learner run the failing versions (the unquoted delimiter, `sort file > file`, `uniq -c` without `sort`, swapped `diff` inputs) and observe the result. The checker recognises these specific mistakes and names the fix. The reference booklet describes its checker output as CHECK lines that tell the student to inspect a result, without saying what is wrong.
3. **History is used for real work.** The reference practises Ctrl+R on two `grep` commands typed only to create a trail. Here the learner recalls their own pipeline from Experiment 3 and extends it into the per-server count that identifies the faulty server. The devcontainer also sets `terminal.integrated.sendKeybindingsToShell` so Ctrl+R, Ctrl+G, Ctrl+O and Ctrl+K reach the shell instead of VS Code, and saves history after every command so earlier commands are still searchable in a new terminal.

Smaller changes: every flag is explained in a table immediately before its first use; each experiment opens with its goal, start folder and output files; `diff` output includes all three markers (`a`, `c`, `d`); and the checker can be run per experiment.

## Timing

| Item | Value |
|---|---|
| Expected learner completion time | About 100 minutes (estimate: setup 5, Exp 1 to 7 about 10 each, final task 15, validation 10). Not yet timed with a learner. |
| Actual time spent building the lab | _To be completed by the author._ |

## Assumptions

- Learners know Lab 1: `cd`, `pwd`, `ls`, `cat`, `cp`, `rm`, `grep`, pipes and `>`.
- The lab runs in Bash in a GitHub Codespace built from `.devcontainer/devcontainer.json` (image `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm`, non-root user).
- `LC_COLLATE=C` is set in `~/.bashrc` so every learner gets the same `sort` order. The data was also chosen so text order is the same under `C` and `en_US.UTF-8`.
- The reference solution and checker are visible in the repository, as in the reference lab. The checker confirms results; the sign-off and recording show how the work was done.
- No per-student variation (the reference lab assigned individual IDs). One shared dataset keeps the lab simpler to teach and review.

## Blockers and items still to verify

- _To be completed by the author after testing in a fresh Codespace._
- Keyboard shortcuts in the browser version of Codespaces depend on the browser. If Ctrl+R or Ctrl+G is intercepted, open the Codespace in VS Code Desktop; the book also gives `history | grep` as a fallback.

## AI use

_To be completed by the author._

## Maintaining the lab

```bash
python3 lab/dev/generate_logs.py     # regenerate requests.log and alerts.log (prints the key facts)
python3 lab/dev/update_manifest.py   # after any intended evidence change
pip install markdown && python3 book/build_pdf.py   # rebuild the PDF (needs Chrome, Chromium or Edge)
bash tests/run-tests.sh              # must report 0 failed
```

If the evidence changes, update the expected values in this file, the diff text in `lab/check.py` and any numbers quoted in the book.
