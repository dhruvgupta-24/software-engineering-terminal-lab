# Walkthrough recording outline

Camera on, face visible, voice clear. Replace each `[mm:ss]` with the real timestamp after recording, and paste the list into the Loom description.

Loom URL: _to be added_

| Time | Section | Show on screen | Explain |
|---|---|---|---|
| [mm:ss] | Setup | Repository page, README, Codespace creation (trim waiting), `Setup complete`, `bash lab/start.sh`, `cd`, `pwd`, `ls evidence work` | What the devcontainer installs and configures; why `evidence/` is read-only and `work/` is editable; how `start.sh` makes a fresh attempt without deleting old ones |
| [mm:ss] | Scenario and book | Lab book page 1 | The incident, the learner's job, the three files in the handover package, `findings.txt` as the running notebook |
| [mm:ss] | Experiment 1: less | `less evidence/runbook.txt`: Space, b, G, g, `/NOTE FORMAT`, n, N, `/ROTA`, `/LOG FORMAT`, q | Why less instead of cat; why the first search match (RETIRED) is not the answer |
| [mm:ss] | Experiment 2: nano | Edit lines 2 and 3 of `work/handover.txt`, Ctrl+O, Enter, Ctrl+X, cat, reopen (no save prompt), create `work/findings.txt` | Reading nano's `^` shortcuts; what the missing save prompt proves |
| [mm:ss] | Experiment 3: cut | Unquoted `cut -d |` error, field 3 to `statuses.txt`, fields 1,2,3, `grep -F "|503"`, `-f 5,4` observation | Why the delimiter is quoted; why row order lets the first match be the earliest 503 |
| [mm:ss] | Experiment 4: sort | Text vs `-n` in less (g and G), `sort -n -r` saved, `sort scratch > scratch` empties the file, `Permission denied` on evidence | Text vs numeric comparison; why the shell empties the destination first |
| [mm:ss] | Experiment 5: uniq | 14 lines to 10 with uniq, 5 with sort, `uniq -c` with and without sort, status counts | Adjacent-only comparison; order of commands changes the answer |
| [mm:ss] | Experiment 6: history | `history 10`, `history | grep -F "uniq"`, Ctrl+R, Ctrl+R again, Ctrl+G, Ctrl+R `|503`, Right Arrow, edit, Enter | Difference between Right Arrow and Enter; reusing real earlier work |
| [mm:ss] | Experiment 7: diff | Identical pair (no output), live vs approved, marker meanings, swapped order, save to file, repair in nano, verify (no output) | Input order; when output is expected and when silence is the goal |
| [mm:ss] | Final task | Read Sections 11 and 12, build `students-to-contact.txt`, complete `handover.txt`, final `cat` of the package | How each earlier finding fills a line of the note |
| [mm:ss] | Validation | Full checker run; the deliberate `uniq` mistake, FAIL message, Ctrl+R to the correct command, PASS; final 14 of 14; mention the sign-off table | What the checker can and cannot prove; why it never changes files |
