"""Unduh MIT-BIH Arrhythmia Database v1.0.0 ke data/raw/ (tidak di-commit)."""
import pathlib, wfdb
raw = pathlib.Path(__file__).resolve().parent / "raw"
raw.mkdir(exist_ok=True)
if len(list(raw.glob("*.dat"))) < 48:
    wfdb.dl_database("mitdb", str(raw))
print(len(list(raw.glob("*.dat"))), "rekaman di", raw)
