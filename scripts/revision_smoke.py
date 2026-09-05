"""Smoke: agree -> deliver -> pay -> revise -> pay REFUSED -> reconsider -> pay."""
import shutil
import subprocess
import sys
from pathlib import Path

DB = Path.home() / ".mnemos" / "revision_smoke.db"
if DB.exists():
    DB.unlink()

PY = r"C:\Users\vergio\Dev\mnemos\.venv\Scripts\python.exe"


def run(*args, expect=0):
    result = subprocess.run(
        [PY, "-c", "import sys; from core.cli import main; sys.exit(main())",
         "--db", str(DB), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    out = (result.stdout + result.stderr).strip()
    print(f"$ mnemos {' '.join(args)}")
    print(out)
    if expect is not None and result.returncode != expect:
        print(f"!! expected exit {expect}, got {result.returncode}")
        sys.exit(1)
    return out


run("remember", "contractor rate is 40", "--category", "preference")
run("remember", "fencing delivery, 200", "--category", "preference")
run("agree", "fencing", "--amount", "200")
run("advance", "fencing", "--to", "delegated")
run("advance", "fencing", "--to", "delivered")
run("link", "preference", "contractor_rate_is_40", "agreement", "fencing")
run("blast", "preference", "contractor_rate_is_40")
out = run("revise", "preference", "contractor_rate_is_40", "60", "--reason", "corrected")
assert "suspect: agreement:fencing" in out
run("suspect")
out = run("pay", "fencing", "200", expect=1)
assert "suspect" in out
run("reconsider", "agreement", "fencing", "--invalid", "--reason", "price void")
out = run("pay", "fencing", "200", expect=1)
assert "suspect" in out
run("reconsider", "agreement", "fencing", "--valid", "--reason", "fixed price")
run("suspect")
run("pay", "fencing", "200", expect=0)
run("blast", "preference", "contractor_rate_is_40")
print("SMOKE OK")
