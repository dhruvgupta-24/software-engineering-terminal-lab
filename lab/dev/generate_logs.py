#!/usr/bin/env python3
"""Regenerate lab/evidence/requests.log and lab/evidence/alerts.log.

The output is deterministic (fixed seed). Run from the repository root:

    python3 lab/dev/generate_logs.py

After regenerating, update the expected values in lab/check.py and the
reviewer notes. The script prints the facts the checker depends on.
"""
import random
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parent.parent / "evidence"
SERVERS = ["web-01", "web-02", "web-03"]
STATUS_VALUES = {200, 304, 404, 503, 504}

rng = random.Random(2417)


def secs(hms):
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 3600 + m * 60 + s


def hms(t):
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


def latency(low, high):
    # A latency must never look like a status code, otherwise a search
    # such as grep -F "|503|" would match the ms field as well.
    while True:
        ms = rng.randint(low, high)
        if ms not in STATUS_VALUES:
            return ms


STUDENTS = [f"S{n}" for n in rng.sample(range(24000, 24999), 40)]
ENROL_FAILED = STUDENTS[:9]        # get at least one 503 on /api/enrol
TIMETABLE_ONLY = STUDENTS[9]       # 503 on /api/timetable only
TIMEOUT_ONLY = STUDENTS[10]        # 504 on /api/enrol only
OTHERS = STUDENTS[11:]

rows = []


def add(t, server, status, ms, endpoint, student):
    rows.append((t, server, status, ms, endpoint, student))


# Background traffic, 01:00:00 to 03:29:59.
endpoints = (["/api/courses"] * 5 + ["/api/enrol"] * 3 + ["/api/timetable"] * 3
             + ["/login"] * 2 + ["/health"] * 2 + ["/favicon.ico"])
incident = (secs("01:14:07"), secs("02:21:00"))
t = secs("01:00:00")
while t < secs("03:30:00"):
    server = rng.choice(SERVERS)
    endpoint = rng.choice(endpoints)
    slow = server == "web-02" and incident[0] <= t <= incident[1]
    ms = latency(1150, 4800) if slow else latency(12, 960)
    if endpoint == "/favicon.ico":
        status, student = 404, "-"
    elif endpoint == "/health":
        status, student, ms = 200, "-", latency(3, 40)
    elif endpoint == "/api/courses":
        status = rng.choice([200, 200, 304])
        student = rng.choice(OTHERS + ["-"])
    else:
        status, student = 200, rng.choice(OTHERS)
    if t >= incident[0] - 1 and t <= incident[0]:
        t += 2
        continue
    add(t, server, status, ms, endpoint, student)
    t += rng.randint(40, 120)

# 503 responses on web-02 while the connection pool was exhausted.
enrol_503 = ENROL_FAILED + ENROL_FAILED[:5] + ENROL_FAILED[2:6]  # 18, with retries
rng.shuffle(enrol_503)
web02_503 = [("/api/enrol", s) for s in enrol_503]
web02_503 += [("/api/timetable", TIMETABLE_ONLY)] * 2
web02_503 += [("/api/timetable", rng.choice(OTHERS)) for _ in range(5)]
web02_503 += [("/login", rng.choice(OTHERS)) for _ in range(6)]
first = web02_503.pop(web02_503.index(("/api/enrol", enrol_503[0])))
add(incident[0], "web-02", 503, 2004, *first)
rng.shuffle(web02_503)
times = sorted(rng.sample(range(incident[0] + 30, secs("02:18:00")), len(web02_503)))
for when, (endpoint, student) in zip(times, web02_503):
    add(when, "web-02", 503, latency(2001, 2019), endpoint, student)

# A few 503s elsewhere while the load balancer shifted traffic.
for when, server in [("01:51:12", "web-03"), ("01:52:40", "web-03"),
                     ("01:58:03", "web-01"), ("02:02:19", "web-03"),
                     ("02:06:55", "web-01"), ("02:09:31", "web-03")]:
    add(secs(when), server, 503, latency(2001, 2019), "/api/timetable",
        rng.choice(OTHERS))

# Gateway timeouts (504) on web-02, all just over the 10000 ms limit.
for when, ms, endpoint, student in [
        ("01:22:48", 10031, "/api/enrol", TIMEOUT_ONLY),
        ("01:37:15", 10012, "/api/timetable", rng.choice(OTHERS)),
        ("01:44:02", 10093, "/api/enrol", ENROL_FAILED[3]),
        ("01:59:40", 10047, "/login", rng.choice(OTHERS)),
        ("02:11:26", 10020, "/api/enrol", TIMEOUT_ONLY)]:
    add(secs(when), "web-02", 504, ms, endpoint, student)

rows.sort(key=lambda r: r[0])
lines = [f"{hms(r[0])}|{r[1]}|{r[2]}|{r[3]}|{r[4]}|{r[5]}" for r in rows]
assert len({r[0] for r in rows}) == len(rows), "duplicate timestamps"
(EVIDENCE / "requests.log").write_text("\n".join(lines) + "\n", newline="\n")

alerts = """01:14:30|HighErrorRate|web-02
01:15:30|HighErrorRate|web-02
01:16:30|HighErrorRate|web-02
01:17:10|DBPoolExhausted|web-02
01:18:10|DBPoolExhausted|web-02
01:21:40|HighLatency|web-01
01:24:30|HighErrorRate|web-02
01:25:30|HighErrorRate|web-02
01:31:05|HighLatency|web-01
01:33:10|DBPoolExhausted|web-02
01:40:00|DiskSpaceLow|web-03
01:52:30|HighErrorRate|web-03
01:53:30|HighErrorRate|web-02
02:05:10|DBPoolExhausted|web-02
"""
(EVIDENCE / "alerts.log").write_text(alerts, newline="\n")

# Facts used by the checker and the reviewer notes.
c503 = [r for r in rows if r[2] == 503]
print("rows:", len(rows))
print("503 total:", len(c503))
for s in SERVERS:
    print(f"  503 {s}:", sum(r[1] == s for r in c503))
print("first 503:", hms(c503[0][0]), c503[0][1])
slow = max(rows, key=lambda r: r[3])
print("slowest:", slow[3], slow[4])
print("statuses:", {s: sum(r[2] == s for r in rows) for s in sorted(STATUS_VALUES)})
contact = sorted({r[5] for r in c503 if r[4] == "/api/enrol"})
print("students to contact:", len(contact), contact)
