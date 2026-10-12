#!/usr/bin/env bash
# Reference solution for reviewers and automated tests.
#
# Produces every graded file in an attempt folder without interactive tools.
# Students make the nano edits by hand; here they are written with printf and
# cp so the result can be reproduced exactly.
#
# Usage: bash reviewer/solution.sh attempts/attempt-01
set -euo pipefail

cd "$1"

# Experiment 2: nano edits (lines 1 to 3 of the handover, new findings file)
printf '%s\n' "Incident: INC-2417" "Service: coursedesk" "Escalation: Tomas Reyes" \
    "Errors: about 20" "Server: web-03" \
    "Notes: errors started around 01:40, cause unknown, config not checked" \
    > work/handover.txt
printf '%s\n' "Handover format: rev 4" "Incident lead: Tomas Reyes" > work/findings.txt

# Experiment 3: cut
cut -d "|" -f 3 evidence/requests.log > work/statuses.txt
cut -d "|" -f 1,2,3 evidence/requests.log > work/time-server-status.txt

# Experiment 4: sort
cut -d "|" -f 4,5 evidence/requests.log | sort -n -r > work/latency-ranked.txt

# Experiment 5: uniq
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq > work/alert-types.txt
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq -c > work/alert-counts.txt
sort work/statuses.txt | uniq -c > work/status-counts.txt

# Experiment 6: the command recalled with Ctrl+R and extended
grep -F "|503" work/time-server-status.txt | cut -d "|" -f 2 | sort | uniq -c | sort -n -r \
    > work/errors-by-server.txt

# Experiment 7: diff (exit status 1 means differences were found, which is expected)
diff evidence/web-02-live.conf evidence/web-02-approved.conf > work/config-changes.diff || true
cp evidence/web-02-approved.conf work/web-02.conf
chmod 644 work/web-02.conf

# Final task
grep -F "|503|" evidence/requests.log | grep -F "|/api/enrol|" | cut -d "|" -f 6 | sort | uniq \
    > work/students-to-contact.txt
printf '%s\n' \
    "Incident: INC-2417" \
    "Service: coursedesk" \
    "Escalation: Tomas Reyes" \
    "Faulty server: web-02" \
    "First 503: 01:14:07" \
    "503 responses: 37" \
    "Slowest request: 10093 ms on /api/enrol" \
    "Cause: db.pool_size changed from 40 to 4" \
    "Config: reconciled" \
    "Students to contact: 9" \
    > work/handover.txt
