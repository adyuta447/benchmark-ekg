"""Pemuatan MIT-BIH: pilih kanal MLII berdasarkan nama, resample 360 -> 250 Hz, band-pass, peta kelas AAMI."""
import pathlib, numpy as np, wfdb
from scipy.signal import butter, filtfilt, resample_poly

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
FS_SRC, FS = 360, 250
EXCLUDE = [102, 104, 107, 217]  # alat pacu jantung
DS1 = [101, 106, 108, 109, 112, 114, 115, 116, 118, 119, 122, 124, 201, 203, 205, 207, 208, 209, 215, 220, 223, 230]
DS2 = [100, 103, 105, 111, 113, 117, 121, 123, 200, 202, 210, 212, 213, 214, 219, 221, 222, 228, 231, 232, 233, 234]
CLASSES = ["N", "S", "V", "F", "Q"]
AAMI = {**dict.fromkeys("NLRej", "N"), **dict.fromkeys("AaJS", "S"), **dict.fromkeys("VE", "V"),
        "F": "F", **dict.fromkeys("/fQ", "Q")}

def bandpass(x, lo=0.5, hi=40.0, fs=FS, order=4):
    b, a = butter(order, [lo / (fs / 2), hi / (fs / 2)], btype="band")
    return filtfilt(b, a, x)

def load(rid, filt=True):
    """Kembalikan dict: sinyal 250 Hz (mV), posisi R (indeks 250 Hz), label AAMI per detak."""
    rec = wfdb.rdrecord(str(RAW / str(rid)))
    ch = rec.sig_name.index("MLII")  # urutan kanal beda antar rekaman
    ann = wfdb.rdann(str(RAW / str(rid)), "atr")
    x = resample_poly(rec.p_signal[:, ch], FS, FS_SRC)  # 25/36
    keep = [i for i, s in enumerate(ann.symbol) if s in AAMI]
    pos = np.round(ann.sample[keep] * FS / FS_SRC).astype(int)
    lab = np.array([AAMI[ann.symbol[i]] for i in keep])
    ok = pos < len(x)
    return {"id": rid, "x": bandpass(x) if filt else x, "r": pos[ok], "y": lab[ok], "sig_name": rec.sig_name,
            "raw_symbols": [ann.symbol[i] for i in keep]}
