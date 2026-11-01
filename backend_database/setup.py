import os
CONN=dict(user=os.getenv('PGUSER','postgres'),host=os.getenv('PGHOST','localhost'),password=os.getenv('PGPASSWORD',''))
import numpy as np, psycopg2, io, time
rng=np.random.default_rng(1)
def beat(t):
    g=lambda m,s,a: a*np.exp(-((t-m)**2)/(2*s*s))
    return g(.2,.025,.12)+g(.37,.01,-.12)+g(.4,.012,1.0)+g(.43,.01,-.25)+g(.65,.04,.3)
pool=[]
for k in range(1000):
    hr=rng.uniform(60,100); n=np.arange(250); ph=(n/250*hr/60+rng.uniform())%1
    x=beat(ph)+0.05*np.sin(2*np.pi*n/250*0.3+rng.uniform(0,6))+rng.normal(0,0.02,250)
    pool.append(np.clip(2048+x*600,0,4095).astype(int))
buf=io.StringIO()
for k,a in enumerate(pool):
    buf.write(f"{k}\t{{{','.join(map(str,a))}}}\t{a.min()}\t{a.max()}\t{a.mean():.2f}\n")
DAYS=30
for db in ['plain','ts']:
    c=psycopg2.connect(dbname=db,**CONN); c.autocommit=True; cur=c.cursor()
    cur.execute("drop table if exists pool; create unlogged table pool(k int, s int2[], pmin int2, pmax int2, pmean real)")
    buf.seek(0); cur.copy_from(buf,'pool')
    cur.execute("drop table if exists packets cascade; create table packets(device_id int, seq bigint, ts timestamptz not null, samples int2[], pmin int2, pmax int2, pmean real)")
    if db=='ts': cur.execute("select create_hypertable('packets', by_range('ts', interval '1 day'))")
    t=time.time()
    cur.execute(f"""insert into packets select 1, i, timestamptz '2026-09-01' + i*interval '1 second', p.s, p.pmin, p.pmax, p.pmean
      from generate_series(0,{DAYS}*86400-1) i join pool p on p.k = ((i::bigint*7919)%1000)::int""")
    cur.execute("create unique index on packets(device_id, ts)")
    if db=='ts':
        cur.execute("""create materialized view hist_1m with (timescaledb.continuous) as
          select device_id, time_bucket('1 minute', ts) b, min(pmin) mn, max(pmax) mx, avg(pmean) av from packets group by 1,2 with no data""")
        cur.execute("call refresh_continuous_aggregate('hist_1m', null, null)")
    cur.execute("vacuum analyze packets")
    print(db,'loaded in',round(time.time()-t),'s',flush=True)
