import asyncio, aiohttp, time, json, sys, random, statistics
mode,N,DUR=sys.argv[1],int(sys.argv[2]),float(sys.argv[3])
BASE="http://127.0.0.1:8000"; lat=[]
async def poll(s,pid):
    await asyncio.sleep(random.random()); last=None; end=time.time()+DUR
    while time.time()<end:
        t0=time.time()
        async with s.get(f"{BASE}/latest/{pid}") as r: d=json.loads(await r.text())
        now=time.time()
        if d.get("seq") and d["seq"]!=last:
            if last is not None: lat.append((now-d["t"])*1000)
            last=d["seq"]
        await asyncio.sleep(max(0,1-(time.time()-t0)))
async def ws(s,pid):
    async with s.ws_connect(f"{BASE.replace('http','ws')}/ws/{pid}") as w:
        end=time.time()+DUR; first=True
        while time.time()<end:
            m=await w.receive(timeout=5); d=json.loads(m.data)
            if not first: lat.append((time.time()-d["t"])*1000)
            first=False
async def sse(s,pid):
    async with s.get(f"{BASE}/sse/{pid}") as r:
        end=time.time()+DUR; first=True
        async for line in r.content:
            if time.time()>end: break
            if line.startswith(b"data: "):
                d=json.loads(line[6:])
                if not first: lat.append((time.time()-d["t"])*1000)
                first=False
async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as s:
        f={'polling':poll,'ws':ws,'sse':sse}[mode]
        await asyncio.gather(*[f(s,i%200) for i in range(N)])
    lat.sort(); print(json.dumps({"mode":mode,"n":N,"count":len(lat),"median":statistics.median(lat),"p95":lat[int(len(lat)*.95)-1]}))
asyncio.run(main())
