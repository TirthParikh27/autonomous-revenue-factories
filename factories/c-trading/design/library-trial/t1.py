import numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
import vectorbt as vbt
rng=np.random.default_rng(0)
def mk(n,freq,assets=3):
    idx=pd.date_range("2022-01-01",periods=n,freq=freq)
    r=rng.normal(0,0.002,(n,assets)); close=pd.DataFrame(100*np.exp(np.cumsum(r,0)),index=idx,columns=[f"A{i}" for i in range(assets)])
    open_=close.shift(1).fillna(100)*np.exp(rng.normal(0,0.0003,(n,assets)))
    return open_,close
# reference engine: weights decided on close[t] info, traded at open[t+1], costs on turnover
def ref(open_,close,w,fee,slip):
    n,a=close.shape; cash=1.0; pos=np.zeros(a); eq=np.empty(n); O=open_.values;C=close.values;W=w.values
    for t in range(n):
        if t>0:
            val=cash+(pos*O[t]).sum()
            tgt=W[t-1]*val/O[t]          # target units from yesterday's decision
            d=tgt-pos
            # sells first then buys, costs
            for i in np.argsort(d):
                if d[i]==0: continue
                px=O[t,i]*(1+slip*np.sign(d[i])); notional=abs(d[i])*px
                cash-= d[i]*px + notional*fee; pos[i]+=d[i]
        eq[t]=cash+(pos*C[t]).sum()
    return pd.Series(eq,index=close.index)
open_,close=mk(2000,"15min")
fast=close.rolling(20).mean(); slow=close.rolling(80).mean()
w=((fast>slow).astype(float)/3).fillna(0)          # long-only, up to 1/3 each
fee,slip=0.001,0.0005
e_ref=ref(open_,close,w,fee,slip)
# vectorbt: shift decisions one bar, execute at open
pf=vbt.Portfolio.from_orders(close, size=w.shift(1).fillna(0), size_type="targetpercent", price=open_, fees=fee, slippage=slip,
    init_cash=1.0, cash_sharing=True, group_by=True, call_seq="auto", freq="15min")
e_vbt=pf.value()
print("final ref",e_ref.iloc[-1],"vbt",float(e_vbt.iloc[-1]),"max abs diff",float((e_ref-e_vbt).abs().max()))
print("orders",pf.orders.count(), "fees paid",float(pf.orders.fees.sum()))
r=pf.returns(); print("per-bar returns len",len(r), "sharpe",float(pf.sharpe_ratio()))
# short + per-asset cost arrays
w2=(np.sign(fast-slow)/3).fillna(0)
fees_arr=np.array([[0.001,0.0002,0.00005]]); slip_arr=np.array([[0.0005,0.0001,0.00005]])
pf2=vbt.Portfolio.from_orders(close,size=w2.shift(1).fillna(0),size_type="targetpercent",price=open_,fees=fees_arr,slippage=slip_arr,init_cash=1.0,cash_sharing=True,group_by=True,call_seq="auto",freq="15min")
print("long-short per-asset costs ok, final",float(pf2.value().iloc[-1]))
# time-varying slippage (e.g. vol-scaled) as full array
sl=pd.DataFrame(rng.uniform(0.0001,0.001,close.shape),index=close.index,columns=close.columns)
pf3=vbt.Portfolio.from_orders(close,size=w.shift(1).fillna(0),size_type="targetpercent",price=open_,fees=fee,slippage=sl,init_cash=1.0,cash_sharing=True,group_by=True,call_seq="auto",freq="15min")
print("time-varying slippage ok, final",float(pf3.value().iloc[-1]))
