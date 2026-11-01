"""Klien uji transport (satu proses, banyak klien). Argumen: mode port pid_awal jumlah durasi_detik pemanasan_detik.
Keluaran: satu baris JSON berisi umur data (ms) dan byte yang diterima."""
import asyncio, aiohttp, time, json, sys, random
mode, port, p0, N, DUR = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]); WARM = float(sys.argv[6]); T0 = time.time() + 0.5  # T0: mulai hitung setelah koneksi dibuka
ok = lambda: time.time() - T0 > WARM
BASE = f"http://127.0.0.1:{port}"; lat = []; nbytes = 0; redundant = 0; polls = 0
async def poll(s, pid, every):
    global nbytes, redundant, polls
    await asyncio.sleep(random.random() * every); last = None; end = time.time() + DUR
    while time.time() < end:
        t0 = time.time()
        async with s.get(f"{BASE}/latest/{pid}") as r: body = await r.read()
        now = time.time(); w_ = ok(); nbytes += len(body) * w_; polls += w_; d = json.loads(body)
        if d.get("seq") and d["seq"] != last:
            if last is not None and w_: lat.append((now - d["t"]) * 1000)
            last = d["seq"]
        elif w_: redundant += 1
        await asyncio.sleep(max(0, every - (time.time() - t0)))
async def ws(s, pid):
    global nbytes
    async with s.ws_connect(f"{BASE.replace('http', 'ws')}/ws/{pid}") as w:
        end = time.time() + DUR; first = True
        while time.time() < end:
            m = await w.receive(timeout=5); w_ = ok(); nbytes += len(m.data) * w_; d = json.loads(m.data)
            if not first and w_: lat.append((time.time() - d["t"]) * 1000)
            first = False
async def sse(s, pid):
    global nbytes
    async with s.get(f"{BASE}/sse/{pid}") as r:
        end = time.time() + DUR; first = True
        async for line in r.content:
            nbytes += len(line) * ok()
            if time.time() > end: break
            if line.startswith(b"data: "):
                d = json.loads(line[6:])
                if not first and ok(): lat.append((time.time() - d["t"]) * 1000)
                first = False
async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as s:
        f = {"polling_1s": lambda s, p: poll(s, p, 1.0), "polling_250ms": lambda s, p: poll(s, p, .25), "ws": ws, "sse": sse}[mode]
        await asyncio.gather(*[f(s, (p0 + i) % 200) for i in range(N)])
    print(json.dumps({"lat": lat, "bytes": nbytes, "redundant": redundant, "polls": polls}))
asyncio.run(main())
