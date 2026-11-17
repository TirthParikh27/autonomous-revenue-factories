import numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
import vectorbt as vbt
rng=np.random.default_rng(1)
n=35040*3   # 3 years of 15-min bars, 24/7
idx=pd.date_range("2023-01-01",periods=n,freq="15min")
close=pd.Series(100*np.exp(np.cumsum(rng.normal(0,0.002,n))),index=idx); open_=close.shift(1).fillna(100)
# sweep: 400 fast/slow combos on one asset
fasts=np.arange(5,105,5); slows=np.arange(50,1050,50)
t=time.time()
cols={}
for f in fasts:
    mf=close.rolling(f).mean()
    for s in slows:
        cols[(f,s)]=(mf>close.rolling(s).mean()).astype(float)
W=pd.DataFrame(cols).shift(1).fillna(0)
t1=time.time()-t
t=time.time()
pf=vbt.Portfolio.from_orders(close,size=W,size_type="targetpercent",price=open_,fees=0.001,slippage=0.0005,init_cash=1.0,freq="15min")
rets=pf.returns()
t2=time.time()-t
print(f"signals {t1:.1f}s, 400 backtests x {n} bars first call {t2:.1f}s; returns matrix {rets.shape}")
t=time.time()
pf=vbt.Portfolio.from_orders(close,size=W,size_type="targetpercent",price=open_,fees=0.001,slippage=0.0005,init_cash=1.0,freq="15min"); rets=pf.returns()
print(f"second call (compiled) {time.time()-t:.1f}s")
# funding / carry: not a from_orders arg -> apply as adjustment to per-bar returns
pos_frac=(pf.asset_value()/pf.value())   # exposure per bar
funding=0.0001/32                         # 0.01% per 8h, per 15-min bar
adj=rets-pos_frac.shift(1).fillna(0)*funding
print("funding adjustment applied post-hoc, mean drag/bar",float((rets-adj).mean().mean()))
# daily and hourly freq annualisation
for fq,m in [("1h",8760),("1D",365)]:
    c=close.resample(fq).last(); o=close.resample(fq).first()
    p=vbt.Portfolio.from_orders(c,size=(c.rolling(20).mean()>c.rolling(100).mean()).astype(float).shift(1).fillna(0),size_type="targetpercent",price=o,fees=0.001,freq=fq)
    print(fq,"bars",len(c),"sharpe",round(float(p.sharpe_ratio()),3),"max dd",round(float(p.max_drawdown()),3),"trades",int(p.trades.count()))
