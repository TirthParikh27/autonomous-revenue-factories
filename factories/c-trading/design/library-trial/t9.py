import numpy as np, pandas as pd, warnings, inspect
warnings.filterwarnings("ignore")
from skfolio.model_selection import CombinatorialPurgedCV, WalkForward
print(inspect.signature(CombinatorialPurgedCV.__init__)); print(inspect.signature(WalkForward.__init__))
rng=np.random.default_rng(0); T=2000
X=pd.DataFrame(rng.normal(0,0.01,(T,3)),index=pd.date_range("2018-01-01",periods=T,freq="B"))
cv=CombinatorialPurgedCV(n_folds=10,n_test_folds=2,purged_size=10,embargo_size=5)
print("CPCV splits:",cv.n_splits,"test paths:",cv.n_test_paths)
ok_overlap=True; ok_purge=True; k=0
for train,tests in cv.split(X):
    k+=1
    te=np.concatenate(tests) if isinstance(tests,(list,tuple)) else tests
    ok_overlap&= len(np.intersect1d(train,te))==0
    # purge: no train index within 10 bars before/after any test block edge
    for blk in (tests if isinstance(tests,(list,tuple)) else [tests]):
        lo,hi=blk.min(),blk.max()
        near=train[(train>=lo-10)&(train<lo)]; ok_purge&= len(near)==0
        after=train[(train>hi)&(train<=hi+15)]; ok_purge&= len(after)==0
print("splits iterated:",k,"| train/test never overlap:",ok_overlap,"| purge and embargo gaps respected:",ok_purge)
wf=WalkForward(test_size=250,train_size=750)
sp=list(wf.split(X)); print("walk-forward splits:",len(sp),"| every test after its train:",all(tr.max()<te.min() for tr,te in sp))
