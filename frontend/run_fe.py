import asyncio, json, pathlib
PAGE=pathlib.Path(__file__).resolve().parent.joinpath('page.html').as_uri()
from playwright.async_api import async_playwright
NS=[1250,2500,5000,10000,20000,40000]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--disable-frame-rate-limit","--disable-gpu-vsync"])
        out={}
        for mode in ['canvas','svg','chartjs']:
            out[mode]=[]
            for n in NS:
                reps=[]
                for r in range(5):
                    pg=await b.new_page(viewport={'width':1250,'height':400})
                    await pg.goto(PAGE)
                    reps.append(await pg.evaluate(f"runBench('{mode}',{n},2500)"))
                    await pg.close()
                reps.sort(key=lambda x:x['frameMs'])
                med=reps[2]; out[mode].append({'n':n,**med}); print(mode,n,med,flush=True)
        json.dump(out,open('fe_results.json','w'),indent=1)
        await b.close()
asyncio.run(main())
