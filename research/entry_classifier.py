# Chronological out-of-sample classifier for early-entry quality. Pure Python logistic regression.
import json, math
from pathlib import Path
import entry_feature_study as es
features=['histDelta','adx','slope','acc','dist20','rv','cmf','rsi','br','cp']
rows=sorted(es.rows,key=lambda x:x['day'])
cut=int(len(rows)*.70);train=rows[:cut];test=rows[cut:]
means={k:sum(r[k] for r in train)/len(train) for k in features}
stds={}
for k in features:
    v=sum((r[k]-means[k])**2 for r in train)/max(1,len(train)-1);stds[k]=max(v**.5,1e-9)
def vec(r):return [(r[k]-means[k])/stds[k] for k in features]
def sig(z):
    if z>30:return 1.0
    if z<-30:return 0.0
    return 1/(1+math.exp(-z))
w=[0.0]*(len(features)+1);lr=.025;lam=.002
for epoch in range(240):
    g=[0.0]*len(w)
    for r in train:
        x=vec(r);p=sig(w[0]+sum(w[j+1]*x[j] for j in range(len(x))));e=p-(1 if r['good'] else 0);g[0]+=e
        for j in range(len(x)):g[j+1]+=e*x[j]
    n=len(train);w[0]-=lr*g[0]/n
    for j in range(1,len(w)):w[j]-=lr*(g[j]/n+lam*w[j])
def score(r):
    x=vec(r);return sig(w[0]+sum(w[j+1]*x[j] for j in range(len(x))))
sc=sorted([(score(r),r['good']) for r in test],reverse=True)
base=sum(y for _,y in sc)/len(sc) if sc else 0
levels=[]
for frac in (.10,.20,.30,.50,1.0):
    n=max(1,int(len(sc)*frac));z=sc[:n];levels.append({'frac':frac,'n':n,'precision':sum(y for _,y in z)/n,'lift':(sum(y for _,y in z)/n/base if base else 0)})
# pairwise AUC without dependencies
pos=[p for p,y in sc if y];neg=sorted(p for p,y in sc if not y);wins=0
import bisect
for p in pos:wins+=bisect.bisect_left(neg,p)+.5*(bisect.bisect_right(neg,p)-bisect.bisect_left(neg,p))
auc=wins/(len(pos)*len(neg)) if pos and neg else .5
coef=sorted([(abs(w[i+1]),features[i],w[i+1]) for i in range(len(features))],reverse=True)
summary={'train':len(train),'test':len(test),'base':base,'auc':auc,'levels':levels,'weights':{features[i]:w[i+1] for i in range(len(features))},'intercept':w[0]}
lines=['# Entry Classifier OOS',f'Chronological split: train **{len(train)}**, untouched test **{len(test)}**. Test base-rate **{base:.1%}**, AUC **{auc:.3f}**.','','|Top slice|N|Precision|Lift|','|---:|---:|---:|---:|']
for x in levels:lines.append(f'|{x["frac"]:.0%}|{x["n"]}|{x["precision"]:.1%}|{x["lift"]:.2f}x|')
lines+=['','|Feature|Weight|','|---|---:|']
for _,k,v in coef:lines.append(f'|{k}|{v:.3f}|')
Path('research/result_entry_classifier.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_entry_classifier.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print('\n'.join(lines))