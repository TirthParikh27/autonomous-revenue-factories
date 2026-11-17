import numpy as np, pandas as pd, time, warnings, inspect
warnings.filterwarnings("ignore")
import vectorbt as vbt, talib
rng=np.random.default_rng(1)
n=35040*3
idx=pd.date_range("2023-01-01",periods=n,freq="15min")
close=pd.Series(100*np.exp(np.cumsum(rng.normal(0,0.002,n))),index=idx); open_=close.shift(1).fillna(100)
high=np.maximum(close,open_)*1.0005; low=np.minimum(close,open_)*0.9995
# --- simple in-house vectorised engine vs vectorbt on one config
w=(close.rolling(20).mean()>close.rolling(400).mean()).astype(float)
t=time.time()
r_open=open_.shift(-1)/open_-1            # return from open[t] to open[t+1]
wl=w.shift(1).fillna(0)                   # held from open[t]
own=(wl*r_open).shift(1).fillna(0) - wl.diff().abs().fillna(0)*(0.001+0.0005)
t_own=time.time()-t
pf=vbt.Portfolio.from_orders(close,size=wl,size_type="targetpercent",price=open_,fees=0.001,slippage=0.0005,init_cash=1.0,freq="15min")
print("own total",float((1+own).prod()-1),"vbt total",float(pf.total_return()),f"own time {t_own*1000:.0f}ms; vbt orders",int(pf.orders.count()))
# --- indicators: TA-Lib vs pandas, plus causality check
c=close.values
checks={
 "SMA20":(talib.SMA(c,20), close.rolling(20).mean().values),
 "EMA20":(talib.EMA(c,20), None),
 "RSI14":(talib.RSI(c,14), None),
 "ATR14":(talib.ATR(high.values,low.values,c,14), None),
}
print("SMA talib vs pandas max diff",np.nanmax(np.abs(checks["SMA20"][0]-checks["SMA20"][1])))
c2=c.copy(); cut=50000; c2[cut:]*=1.5   # change the future
for name,fn in [("SMA",lambda x:talib.SMA(x,20)),("EMA",lambda x:talib.EMA(x,20)),("RSI",lambda x:talib.RSI(x,14)),("BBANDS",lambda x:talib.BBANDS(x,20)[0]),("MACD",lambda x:talib.MACD(x)[0])]:
    a,b=fn(c)[:cut],fn(c2)[:cut]
    print(name,"past values unchanged when future changes:",bool(np.allclose(a,b,equal_nan=True)))
t=time.time(); [talib.RSI(c,k) for k in range(5,205)]; print(f"200 RSI variants on {n} bars: {time.time()-t:.2f}s")
print("talib functions:",len(talib.get_functions()))
print("vbt built-in indicators:",[x for x in dir(vbt) if x.isupper()][:20])
