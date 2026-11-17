import numpy as np, warnings, time
warnings.filterwarnings("ignore")
import purgedcv as pc
from itertools import combinations
from scipy.stats import norm, skew, kurtosis, rankdata
rng=np.random.default_rng(7); T=2520
def sr(x): return x.mean(0)/x.std(0,ddof=1)
def dsr_ref(r,N,varsr):
    g=0.5772156649
    z=(1-g)*norm.ppf(1-1/N)+g*norm.ppf(1-1/(N*np.e))
    sr0=np.sqrt(varsr)*z; s=sr(r); n=len(r); sk=skew(r); ku=kurtosis(r,fisher=False)
    return norm.cdf((s-sr0)*np.sqrt(n-1)/np.sqrt(1-sk*s+(ku-1)/4*s*s))
def pbo_ref(R,S=16):   # CSCV, Bailey et al.
    blocks=np.array_split(np.arange(len(R)),S); lam=[]
    sums=np.array([R[b].sum(0) for b in blocks]); sq=np.array([(R[b]**2).sum(0) for b in blocks]); cnt=np.array([len(b) for b in blocks])
    def shp(ix):
        n=cnt[ix].sum(); m=sums[ix].sum(0)/n; v=(sq[ix].sum(0)-n*m*m)/(n-1); return m/np.sqrt(v)
    allb=set(range(S))
    for c in combinations(range(S),S//2):
        i=list(c); o=list(allb-set(c)); best=shp(i).argmax()
        w=rankdata(shp(o))[best]/(R.shape[1]+1); lam.append(np.log(w/(1-w)))
    return float((np.array(lam)<=0).mean())
def run(label,R,S):
    s=sr(R); b=s.argmax(); N=R.shape[1]; v=s.var(ddof=1)
    t=time.time(); p=pc.probability_of_backtest_overfitting(R,S); tl=time.time()-t
    t=time.time(); pr=pbo_ref(R,S); tr=time.time()-t
    print(f"{label}: best annual SR {s[b]*np.sqrt(252):.2f} | DSR lib {pc.deflated_sharpe_ratio(R[:,b],N,v):.3f} ref {dsr_ref(R[:,b],N,v):.3f} | PBO lib {p.pbo:.2f} ({tl:.1f}s) ref {pr:.2f} ({tr:.1f}s) S={S}",flush=True)
R0=rng.normal(0,0.01,(T,50)); run("noise x50",R0,8)
R1=R0.copy(); R1[:,17]+=1.5/np.sqrt(252)*0.01; run("planted SR1.5",R1,8)
R2=R0.copy(); R2[:,17]+=0.5/np.sqrt(252)*0.01; run("planted SR0.5",R2,8)
t=time.time(); print("ref PBO S=16, 200 trials:",pbo_ref(rng.normal(0,0.01,(T,200)),16),f"{time.time()-t:.1f}s",flush=True)
fp=0
for k in range(300):
    R=rng.normal(0,0.01,(T,100)); s=sr(R); b=s.argmax()
    fp+= dsr_ref(R[:,b],100,s.var(ddof=1))>0.95
print("noise experiments where best-of-100 passes DSR>0.95:",fp,"of 300",flush=True)
print("MinBTL years, 100 trials SR1:",round(pc.minimum_backtest_length(100,1.0),2))
print((pc.effective_n_trials.__doc__ or '')[:300].replace('\n',' '))
