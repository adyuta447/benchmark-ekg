import os; os.environ["KERAS_BACKEND"]="jax"
import keras, numpy as np, time, json, statistics
from keras import layers as L
from sklearn.ensemble import RandomForestClassifier
rng=np.random.default_rng(0); T=175
def heads(x,rr):
    h=L.Concatenate()([x,rr]); h=L.Dense(64,activation='relu')(h); h=L.Dropout(.3)(h); return L.Dense(5,activation='softmax')(h)
def cnn():
    i=keras.Input((T,1)); r=keras.Input((3,))
    x=L.Conv1D(32,7,padding='same',activation='relu')(i); x=L.MaxPooling1D(2)(x)
    x=L.Conv1D(64,5,padding='same',activation='relu')(x); x=L.MaxPooling1D(2)(x)
    x=L.Conv1D(128,3,padding='same',activation='relu')(x); x=L.GlobalAveragePooling1D()(x)
    return keras.Model([i,r],heads(x,r))
def lstm():
    i=keras.Input((T,1)); r=keras.Input((3,)); x=L.LSTM(64)(i); return keras.Model([i,r],heads(x,r))
def cnnlstm():
    i=keras.Input((T,1)); r=keras.Input((3,))
    x=L.Conv1D(32,7,padding='same',activation='relu')(i); x=L.MaxPooling1D(2)(x)
    x=L.Conv1D(64,5,padding='same',activation='relu')(x); x=L.MaxPooling1D(2)(x); x=L.LSTM(64)(x)
    return keras.Model([i,r],heads(x,r))
def transformer():
    i=keras.Input((T,1)); r=keras.Input((3,))
    x=L.Conv1D(64,5,strides=5,padding='same')(i)  # 35 token
    for _ in range(2):
        a=L.MultiHeadAttention(4,16)(x,x); x=L.LayerNormalization()(x+a)
        f=L.Dense(128,activation='relu')(x); f=L.Dense(64)(f); x=L.LayerNormalization()(x+f)
    x=L.GlobalAveragePooling1D()(x); return keras.Model([i,r],heads(x,r))
NS=[1,10,50,100,200]; BEATS=12; out={}; info={}
for name,fn in [('CNN 1D (usulan)',cnn),('CNN-LSTM',cnnlstm),('LSTM',lstm),('Transformer kecil',transformer)]:
    m=fn(); info[name]={'params':int(m.count_params())}; out[name]=[]
    for n in NS:
        b=n*BEATS; X=[rng.normal(size=(b,T,1)).astype('float32'),rng.normal(size=(b,3)).astype('float32')]
        for _ in range(3): m.predict_on_batch(X)
        ts=[]
        for _ in range(10):
            t=time.perf_counter(); m.predict_on_batch(X); ts.append((time.perf_counter()-t)*1000)
        out[name].append({'n':n,'ms':statistics.median(ts)}); print(name,n,round(statistics.median(ts),2),flush=True)
# Random Forest pada 6 fitur manual (RR sebelum, RR sesudah, rasio RR, lebar QRS, amplitudo R, energi)
Xtr=rng.normal(size=(20000,6)); ytr=rng.integers(0,5,20000)
rf=RandomForestClassifier(n_estimators=100,max_depth=12,n_jobs=1,random_state=0).fit(Xtr,ytr)
info['Random Forest']={'trees':100,'max_depth':12}; out['Random Forest']=[]
for n in NS:
    X=rng.normal(size=(n*BEATS,6)); rf.predict(X); ts=[]
    for _ in range(10):
        t=time.perf_counter(); rf.predict(X); ts.append((time.perf_counter()-t)*1000)
    out['Random Forest'].append({'n':n,'ms':statistics.median(ts)}); print('RF',n,round(statistics.median(ts),2),flush=True)
json.dump({'results':out,'info':info},open('ml_results.json','w'),indent=1); print(info)
