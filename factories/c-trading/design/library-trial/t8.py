import numpy as np, pandas as pd, warnings, time
warnings.filterwarnings("ignore")
import optuna, vectorbt as vbt, purgedcv as pc
optuna.logging.set_verbosity(optuna.logging.WARNING)
rng=np.random.default_rng(3)
n=24*365*3; idx=pd.date_range("2023-01-01",periods=n,freq="1h")
# price with a mild planted trend component so there is something to find
drift=np.repeat(rng.normal(0,0.0004,n//200+1),200)[:n]
close=pd.Series(100*np.exp(np.cumsum(drift+rng.normal(0,0.004,n))),index=idx); open_=close.shift(1).fillna(100)
rets={}
def bt(fast,slow):
    w=(close.rolling(fast).mean()>close.rolling(slow).mean()).astype(float).shift(1).fillna(0)
    pf=vbt.Portfolio.from_orders(close,size=w,size_type="targetpercent",price=open_,fees=0.001,slippage=0.0005,init_cash=1.0,freq="1h")
    return pf.returns()
def objective(trial):
    f=trial.suggest_int("fast",5,100); s=trial.suggest_int("slow",f+10,600)   # declared ranges
    r=bt(f,s); rets[trial.number]=r.values
    return float(r.mean()/r.std()*np.sqrt(8760))
t=time.time()
study=optuna.create_study(direction="maximize",sampler=optuna.samplers.TPESampler(seed=0))
study.optimize(objective,n_trials=60)
print(f"Optuna: 60 trials in {time.time()-t:.1f}s; best {study.best_params} annual SR {study.best_value:.2f}")
print("every trial recorded:",len(study.trials)==len(rets)==60, "| trials dataframe cols:",list(study.trials_dataframe().columns)[:6])
R=np.array([rets[i] for i in range(60)])           # (configs, obs)
srs=R.mean(1)/R.std(1,ddof=1); b=srs.argmax()
print("DSR of Optuna's best, counting all 60 trials:",round(pc.deflated_sharpe_ratio(R[b],60,srs.var(ddof=1)),3))
print("PBO of the sweep:",round(pc.probability_of_backtest_overfitting(R,8).pbo,2))
print("effective trials (lib, autocorr):",pc.effective_n_trials(np.array([t.value for t in study.trials])))
# parameter stability: neighbours of the best
bp=study.best_params
nb=[float((lambda r:r.mean()/r.std()*np.sqrt(8760))(bt(bp['fast']+df,bp['slow']+ds))) for df in(-5,0,5) for ds in(-30,0,30)]
print("Sharpe at 9 neighbouring parameter points:",np.round(nb,2))
# resumable storage (trial log persistence)
st=optuna.create_study(storage="sqlite:///trials.db",study_name="x",load_if_exists=True,direction="maximize"); st.optimize(lambda tr: tr.suggest_float("x",0,1),n_trials=3)
print("sqlite-backed study persisted trials:",len(optuna.load_study(study_name="x",storage="sqlite:///trials.db").trials)>=3)
