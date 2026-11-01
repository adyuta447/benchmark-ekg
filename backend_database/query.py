import os
CONN=dict(user=os.getenv('PGUSER','postgres'),host=os.getenv('PGHOST','localhost'),password=os.getenv('PGPASSWORD',''))
import psycopg2, time, json, statistics
END="timestamptz '2026-10-01'"
R=[('1 jam','1 hour'),('6 jam','6 hours'),('1 hari','1 day'),('7 hari','7 days'),('30 hari','30 days')]
raw="select date_trunc('minute',ts) b, min(pmin), max(pmax), avg(pmean) from packets where device_id=1 and ts >= {e} - interval '{r}' and ts < {e} group by 1 order by 1"
agg="select b, mn, mx, av from hist_1m where device_id=1 and b >= {e} - interval '{r}' and b < {e} order by 1"
cases=[('PostgreSQL biasa','plain',raw),('TimescaleDB hypertable','ts',raw),('TimescaleDB + continuous aggregate','ts',agg)]
out={}
for name,db,q in cases:
    c=psycopg2.connect(dbname=db,**CONN); cur=c.cursor()
    out[name]=[]
    for lab,r in R:
        sql=q.format(e=END,r=r); ts=[]
        for k in range(7):
            t=time.perf_counter(); cur.execute(sql); rows=cur.fetchall(); ts.append((time.perf_counter()-t)*1000)
        ts=ts[2:]; m=statistics.median(ts)
        out[name].append({'range':lab,'ms':m,'rows':len(rows)}); print(name,lab,round(m,2),'ms',len(rows),flush=True)
for db in ['plain','ts']:
    c=psycopg2.connect(dbname=db,**CONN); cur=c.cursor()
    cur.execute("select pg_size_pretty(pg_total_relation_size('packets'))" if db=='plain' else "select pg_size_pretty(hypertable_size('packets'))"); print(db,'size',cur.fetchone())
json.dump(out,open('db_results.json','w'),indent=1)
