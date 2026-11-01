"""Server uji transport. Payload = paket 1 detik (250 sampel int, ADC 12 bit) dari MIT-BIH.
Tiap pasien dikirim 1 paket/detik dengan fase berbeda (perangkat tidak serempak)."""
import asyncio, json, os, time, pathlib
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response, StreamingResponse
PATIENTS = 200
z = np.load(pathlib.Path(__file__).resolve().parents[2] / "data/processed/mitdb_250hz.npz")
ids = [100, 103, 105, 111, 113, 117, 121, 123, 200, 202]
# mV -> hitungan ADC 12 bit sekitar 2048, 1 mV = 400 hitungan (asumsi, perlu dicocokkan dengan kalibrasi AD8232 nyata)
SIG = [np.clip(2048 + z[f"x_{r}"] * 400, 0, 4095).astype(int) for r in ids]
app = FastAPI(); latest = {}; subs = {}; seq = {}

def payload(pid):
    s = SIG[pid % len(SIG)]; k = seq[pid]; off = (k * 250 + pid * 997) % (len(s) - 250)
    return '{"pid":%d,"seq":%d,"t":%.6f,"s":%s}' % (pid, k, time.time(), json.dumps(s[off:off + 250].tolist(), separators=(",", ":")))

async def producer():
    for p in range(PATIENTS): seq[p] = 0
    k = 0; t0 = time.perf_counter(); step = 1.0 / PATIENTS
    while True:
        pid = k % PATIENTS; seq[pid] += 1; pkt = payload(pid); latest[pid] = pkt
        for q in list(subs.get(pid, ())): q.put_nowait(pkt)
        k += 1; await asyncio.sleep(max(0, t0 + k * step - time.perf_counter()))

@app.on_event("startup")
async def st(): asyncio.create_task(producer())

@app.get("/latest/{pid}")
async def lt(pid: int): return Response(latest.get(pid, "{}"), media_type="application/json")

@app.websocket("/ws/{pid}")
async def ws(w: WebSocket, pid: int):
    await w.accept(); q = asyncio.Queue(); subs.setdefault(pid, set()).add(q)
    try:
        while True: await w.send_text(await q.get())
    except Exception: pass
    finally: subs[pid].discard(q)

@app.get("/sse/{pid}")
async def sse(pid: int):
    q = asyncio.Queue(); subs.setdefault(pid, set()).add(q)
    async def gen():
        try:
            while True: yield "data: " + (await q.get()) + "\n\n"
        finally: subs[pid].discard(q)
    return StreamingResponse(gen(), media_type="text/event-stream")
