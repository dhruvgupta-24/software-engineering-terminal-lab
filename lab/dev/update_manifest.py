#!/usr/bin/env python3
"""Rewrite lab/evidence.sha256 after an evidence file is intentionally changed."""
import hashlib
from pathlib import Path

lab = Path(__file__).resolve().parent.parent
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}"
         for p in sorted((lab / "evidence").iterdir()) if p.is_file()]
(lab / "evidence.sha256").write_text("\n".join(lines) + "\n", newline="\n")
print("\n".join(lines))
