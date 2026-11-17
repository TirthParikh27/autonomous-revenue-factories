import numpy as np, warnings, time
warnings.filterwarnings("ignore")
import purgedcv as pc
exec(open('t5.py').read().split("def run")[0])
T=2520
for label,edge in [("noise",0),("planted SR 1.5",1.5),("planted SR 0.5",0.5)]:
    lib=[];ref=[];d=[]
    for seed in range(5):
        rng=np.random.default_rng(100+seed); R=rng.normal(0,0.01,(T,30)); R[:,3]+=edge/np.sqrt(252)*0.01
        s=sr(R); b=s.argmax()
        lib.append(pc.probability_of_backtest_overfitting(R.T,8).pbo); ref.append(pbo_ref(R,8)); d.append(dsr_ref(R[:,b],30,s.var(ddof=1)))
    print(f"{label}: PBO lib {np.round(lib,2)} ref {np.round(ref,2)} DSR {np.round(d,3)}",flush=True)
rng=np.random.default_rng(1); R=rng.normal(0,0.01,(T,200))
t=time.time(); p=pc.probability_of_backtest_overfitting(R.T,16); tl=time.time()-t
t=time.time(); q=pbo_ref(R,16); tr=time.time()-t
print(f"S=16, 200 trials x {T} bars: lib {p.pbo:.3f} in {tl:.1f}s; ref {q:.3f} in {tr:.1f}s")
