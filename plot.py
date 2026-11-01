import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
plt.rcParams.update({'font.family':'Liberation Serif','font.size':11,'axes.edgecolor':'#444','axes.linewidth':0.8,
  'xtick.color':'#333','ytick.color':'#333','axes.labelcolor':'#111','axes.spines.top':False,'axes.spines.right':False})
ST=[dict(color='#000000',marker='o',ls='-'),dict(color='#555555',marker='s',ls='--'),dict(color='#888888',marker='^',ls='-.'),dict(color='#333333',marker='D',ls=':'),dict(color='#999999',marker='v',ls='--')]
idn=lambda v: f"{v:,.0f}".replace(',','.')
def fmt_ms(v): return (f"{v:.1f}".replace('.',',') if v<100 else idn(v))+' ms'
def finish(ax,fig,title,note,fn,legend_loc='upper left'):
    ax.set_title(title,loc='left',fontsize=13,fontweight='bold',pad=12)
    ax.grid(axis='y',color='#dddddd',lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False,loc=legend_loc,fontsize=10)
    fig.text(0.01,0.01,note,fontsize=8.5,color='#555',ha='left',va='bottom')
    fig.tight_layout(rect=(0,0.05,1,1)); fig.savefig('grafik/'+fn,dpi=200); plt.close(fig)
def endlabel(ax,x,y,txt,dy=0):
    ax.annotate(txt,(x,y),xytext=(6,dy),textcoords='offset points',va='center',fontsize=9,color='#222')

# 1 Frontend
d=json.load(open('hasil/fe_results.json'))
fig,ax=plt.subplots(figsize=(7.2,4.2))
names={'canvas':'Canvas 2D (dipilih)','chartjs':'Chart.js','svg':'SVG / DOM'}
for k,s in zip(['canvas','chartjs','svg'],ST):
    xs=[r['n'] for r in d[k]]; ys=[r['frameMs'] for r in d[k]]
    ax.plot(xs,ys,label=names[k],lw=1.8,ms=6,**s); endlabel(ax,xs[-1],ys[-1],fmt_ms(ys[-1]))
ax.axhline(16.7,color='#000',lw=0.8,ls=(0,(1,2))); ax.text(5200,17.3,'batas 60 fps (16,7 ms)',fontsize=9,color='#333')
ax.set_xscale('log'); ax.set_xticks([1250,2500,5000,10000,20000,40000]); ax.set_xticklabels(['1.250','2.500\n(10 dtk, 1 pasien)','5.000','10.000','20.000','40.000'],fontsize=9)
ax.minorticks_off(); ax.set_xlim(1100,62000); ax.set_ylim(0,20)
ax.set_xlabel('Jumlah titik sinyal di layar'); ax.set_ylabel('Waktu per frame (ms), makin kecil makin baik')
finish(ax,fig,'Front-end: kecepatan menggambar grafik EKG live','Diukur di Chromium headless, kanvas 1200x300 px, grafik digeser 4 sampel per frame, median dari 5 kali uji.','1_frontend_render.png',legend_loc=(0.02,0.42))

# 2 Backend transport
rows=[json.loads(l) for l in open('hasil/be_results.jsonl')]
fig,ax=plt.subplots(figsize=(7.2,4.2))
names={'polling':'REST polling tiap 1 detik','sse':'Server-Sent Events','ws':'WebSocket (dipilih)'}
for k,s in zip(['ws','sse','polling'],ST):
    r=[x for x in rows if x['mode']==k]; xs=[x['n'] for x in r]; ys=[x['median'] for x in r]
    ax.plot(xs,ys,label=names[k],lw=1.8,ms=6,**s); endlabel(ax,xs[-1],ys[-1],fmt_ms(ys[-1]),dy=(7 if k=='sse' else -7 if k=='ws' else 0))
ax.axhline(200,color='#000',lw=0.8,ls=(0,(1,2))); ax.text(1.05,215,'target laporan: di bawah 200 ms',fontsize=9,color='#333')
ax.set_yscale('log'); ax.set_ylim(0.5,2000); ax.set_xlim(0,235)
ax.set_yticks([1,10,100,1000]); ax.set_yticklabels(['1','10','100','1.000'])
ax.set_xticks([1,10,50,100,200])
ax.set_xlabel('Jumlah klien dashboard yang terhubung bersamaan'); ax.set_ylabel('Jeda server ke dashboard, median (ms, skala log)')
finish(ax,fig,'Back-end: jeda kirim data live dari FastAPI ke dashboard','Diukur lokal dengan FastAPI + Uvicorn (1 worker), 200 pasien simulasi, 1 paket per detik berisi 250 sampel, 15 detik per uji.','2_backend_transport.png',legend_loc='center right')

# 3 Backend database
d=json.load(open('hasil/db_results.json'))
fig,ax=plt.subplots(figsize=(7.2,4.2))
labs=[x['range'] for x in d['PostgreSQL biasa']]; X=list(range(len(labs)))
names={'PostgreSQL biasa':'PostgreSQL biasa','TimescaleDB hypertable':'TimescaleDB, hypertable saja','TimescaleDB + continuous aggregate':'TimescaleDB + continuous aggregate (dipilih)'}
for k,s in zip(['TimescaleDB + continuous aggregate','TimescaleDB hypertable','PostgreSQL biasa'],ST):
    ys=[x['ms'] for x in d[k]]; ax.plot(X,ys,label=names[k],lw=1.8,ms=6,**s)
    endlabel(ax,X[-1],ys[-1],fmt_ms(ys[-1]),dy=(8 if k=='TimescaleDB hypertable' else -6 if k=='PostgreSQL biasa' else 0))
ax.set_yscale('log'); ax.set_ylim(0.2,10000); ax.set_yticks([1,10,100,1000,10000]); ax.set_yticklabels(['1','10','100','1.000','10.000'])
ax.set_xticks(X); ax.set_xticklabels(labs); ax.set_xlim(-0.2,4.9)
ax.set_xlabel('Rentang riwayat yang dibuka dokter (ringkasan per menit)'); ax.set_ylabel('Waktu query, median (ms, skala log)')
finish(ax,fig,'Back-end: waktu memuat grafik riwayat satu pasien','PostgreSQL 16 + TimescaleDB 2.29, data sintetis 30 hari (2,59 juta paket, 1 paket per detik), median dari 5 kali uji.','3_backend_database.png')

# 4 ML
d=json.load(open('hasil/ml_results.json'))['results']
fig,ax=plt.subplots(figsize=(7.2,4.2))
order=['CNN 1D (usulan)','CNN-LSTM','LSTM','Transformer kecil','Random Forest']
offs={'CNN 1D (usulan)':-4,'CNN-LSTM':0,'LSTM':0,'Transformer kecil':0,'Random Forest':0}
for k,s in zip(order,ST):
    xs=[x['n'] for x in d[k]]; ys=[x['ms'] for x in d[k]]
    lab=k+(' (fitur manual)' if k=='Random Forest' else '')
    ax.plot(xs,ys,label=lab,lw=1.8,ms=6,**s); endlabel(ax,xs[-1],ys[-1],fmt_ms(ys[-1]),dy=offs[k])
ax.set_xticks([1,10,50,100,200]); ax.set_xlim(0,240); ax.set_ylim(0,650)
ax.set_xlabel('Jumlah pasien yang dianalisis bersamaan (12 detak per pasien)'); ax.set_ylabel('Waktu inferensi per jendela 10 detik (ms)')
finish(ax,fig,'Machine learning: kecepatan inferensi tiap model','Diukur di CPU 2 inti (Keras 3 + JAX, scikit-learn). Hanya kecepatan, akurasi belum diuji karena model belum dilatih dengan MIT-BIH.','4_ml_inferensi.png')
print('ok')
