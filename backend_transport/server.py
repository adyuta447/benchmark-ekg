import asyncio, time, json, random
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse, Response
app=FastAPI()
PATIENTS=200
latest={}; subs={}  # pid -> set of queues
async def producer():
    seq=0
    while True:
        seq+=1; now=time.time()
        samples=json.dumps([random.randint(1800,2600) for _ in range(250)])
        for pid in range(PATIENTS):
            pkt='{"pid":%d,"seq":%d,"t":%.6f,"s":%s}'%(pid,seq,time.time(),samples)
            latest[pid]=pkt
            for q in list(subs.get(pid,())): q.put_nowait(pkt)
        await asyncio.sleep(max(0,1-(time.time()-now)))
@app.on_event("startup")
async def st(): asyncio.create_task(producer())
@app.get("/latest/{pid}")
async def lt(pid:int): return Response(latest.get(pid,"{}"),media_type="application/json")
@app.websocket("/ws/{pid}")
async def ws(w:WebSocket,pid:int):
    await w.accept(); q=asyncio.Queue(); subs.setdefault(pid,set()).add(q)
    try:
        while True: await w.send_text(await q.get())
    except Exception: pass
    finally: subs[pid].discard(q)
@app.get("/sse/{pid}")
async def sse(pid:int):
    q=asyncio.Queue(); subs.setdefault(pid,set()).add(q)
    async def gen():
        try:
            while True: yield "data: "+(await q.get())+"\n\n"
        finally: subs[pid].discard(q)
    return StreamingResponse(gen(),media_type="text/event-stream")
