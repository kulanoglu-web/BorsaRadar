# v32: preserve v30 S3 selection, add portfolio drawdown brake only
import json
from pathlib import Path
import backtest_br_smart as b
import v24_microplateau_slippage as v24
import v25_concentration_benchmark as v25
import v30_structural_bull_rs as v30
D=b.DATES; START=100000.; FEE=b.FEE
CFG=next(c for c in v30.CANDS if c['name']=='S3')
BRAKES=[None,0.08,0.10,0.12,0.15]
COOLS=[5,10,15]

def sleeve(days,brake=None,cool=10):
 ds=[d for d in days if d in b.bi.breadth_cache]
 cash=START; pos={}; peak=START; dd=0.; maxdd=0.; cooldown=0; tr=[]; exposure=[]; brake_hits=0
 for day in ds:
  if cooldown>0: cooldown-=1
  on=v30.regime(day) and cooldown==0
  for s in list(pos):
   i=v30.idx(s,day)
   if i is None: continue
   p=pos[s]; p['age']+=1; f=b.bi.feat(s,i)
   if p['age']>=CFG['hold'] or v30.close(s,i)<f['e20'] or not on:
    px=b.bi.data[s][i]['o']; pro=p['q']*px*(1-FEE); cash+=pro; tr.append(pro-p['cost']); del pos[s]
  if on:
   for _,s,i in v30.candidates(day,CFG):
    if s in pos or len(pos)>=CFG['top']: continue
    px=b.bi.data[s][i]['o']; alloc=(cash*(1-CFG['cash']))/max(1,CFG['top']-len(pos)); q=int(alloc/(px*(1+FEE)))
    if q<=0: continue
    cost=q*px*(1+FEE); cash-=cost; pos[s]={'q':q,'cost':cost,'age':0}
  eq=cash; invested=0
  for s,p in pos.items():
   i=v30.idx(s,day)
   if i is not None: val=p['q']*v30.close(s,i); eq+=val; invested+=val
  peak=max(peak,eq); dd=(peak-eq)/peak; maxdd=max(maxdd,dd); exposure.append(invested/eq if eq else 0)
  if brake and dd>=brake and pos:
   for s,p in list(pos.items()):
    i=v30.idx(s,day)
    if i is None: continue
    px=v30.close(s,i); pro=p['q']*px*(1-FEE); cash+=pro; tr.append(pro-p['cost']); del pos[s]
   cooldown=cool; peak=cash; brake_hits+=1
 last=ds[-1]
 for s,p in list(pos.items()):
  i=v25.idx_at_or_before(s,last); px=v30.close(s,i); pro=p['q']*px*(1-FEE); cash+=pro; tr.append(pro-p['cost'])
 return {'ret':(cash/START-1)*100,'dd':maxdd*100,'n':len(tr),'exp':100*sum(exposure)/max(1,len(exposure)),'hits':brake_hits}

def mix(days,brake,cool,w=.35):
 a=v24.run(days,1.6); s=sleeve(days,brake,cool); return {'ret':(1-w)*a['ret']+w*s['ret'],'dd':(1-w)*a['dd']+w*s['dd'],'active':a['ret'],'sleeve':s['ret'],'sdd':s['dd'],'exp':s['exp'],'hits':s['hits']}
chunks=[D[i:i+22] for i in range(0,len(D)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for brake in BRAKES:
 for cool in ([0] if brake is None else COOLS):
  rr=[mix(x,brake,cool) for x in dev]; avg=sum(x['ret'] for x in rr)/len(rr); worst=min(x['ret'] for x in rr); dd=sum(x['dd'] for x in rr)/len(rr); score=avg+.7*worst-.45*dd
  rows.append({'brake':brake,'cool':cool,'avg':avg,'worst':worst,'dd':dd,'score':score})
best=max(rows,key=lambda x:x['score']); full=mix(D,best['brake'],best['cool']); base=mix(D,None,0); hr=[mix(x,best['brake'],best['cool']) for x in hold]
lines=['# v32 — Preserve v30 S3, Drawdown Brake','v30 S3 seçim mantığı ve %35 bull pay aynen korunur; yalnız bull sleeve portföy drawdown freni test edilir. Seçim ilk 6 fold.','','|Brake|Cool|Dev avg|Worst|DD|Score|','|---:|---:|---:|---:|---:|---:|']
for x in sorted(rows,key=lambda z:z['score'],reverse=True): lines.append(f'|{("OFF" if x["brake"] is None else f"{x["brake"]:.0%}")}|{x["cool"]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["dd"]:.2f}%|{x["score"]:.3f}|')
lines += ['',f'Base v30: mix **{base["ret"]:.2f}%**, approx DD **{base["dd"]:.2f}%**, sleeve **{base["sleeve"]:.2f}%**, sleeve DD **{base["sdd"]:.2f}%**.',f'Selected: brake **{best["brake"]}**, cool **{best["cool"]}**. Full mix **{full["ret"]:.2f}%**, approx DD **{full["dd"]:.2f}%**, sleeve **{full["sleeve"]:.2f}%**, sleeve DD **{full["sdd"]:.2f}%**, avg exposure **{full["exp"]:.1f}%**, brake hits **{full["hits"]}**.',f'Holdout avg **{sum(x["ret"] for x in hr)/len(hr):.2f}%**, worst **{min(x["ret"] for x in hr):.2f}%**, positive **{sum(x["ret"]>0 for x in hr)}/{len(hr)}**.']
Path('research/result_v32_v30_brake.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v32_v30_brake.json').write_text(json.dumps({'rows':rows,'best':best,'base':base,'full':full,'holdout':hr},indent=2),encoding='utf-8');print('\n'.join(lines))