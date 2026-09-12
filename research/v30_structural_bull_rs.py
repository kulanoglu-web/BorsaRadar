# v30 structural bull + cross-sectional relative strength sleeve
# Fixed v24 D1.6 defensive engine remains benchmark. New bull sleeve selected on dev only.
import json, math
from pathlib import Path
import backtest_br_smart as b
import v24_microplateau_slippage as v24
import v25_concentration_benchmark as v25

D=b.DATES; START=100000.; FEE=b.FEE
CANDS=[
 {'name':'S1','breadth':.55,'look':20,'top':3,'hold':10,'cash':.25},
 {'name':'S2','breadth':.60,'look':20,'top':3,'hold':10,'cash':.25},
 {'name':'S3','breadth':.55,'look':40,'top':3,'hold':15,'cash':.25},
 {'name':'S4','breadth':.60,'look':40,'top':3,'hold':15,'cash':.25},
 {'name':'S5','breadth':.55,'look':40,'top':5,'hold':15,'cash':.20},
]

def idx(s,day): return b.bi.bysym[s].get(day)
def close(s,i): return b.bi.data[s][i]['c']

def regime(day, confirm=3):
 p=D.index(day)
 if p<60:return False
 ok=0
 for k in range(confirm):
  d=D[p-k]; br,bd,strong,recovery,weak=b.state(d)
  if br>=.55 and not weak: ok+=1
 return ok==confirm

def candidates(day,c):
 out=[]
 for s,a in b.bi.data.items():
  i=idx(s,day)
  if i is None or i<max(65,c['look']+2): continue
  turn,vol,j=b.bi.quality(s,i)
  if turn<120_000_000 or vol<120_000 or j>=2: continue
  f=b.bi.feat(s,i)
  if f['adx']<18 or f['cmf']<=0: continue
  p0=close(s,i-c['look']); p1=close(s,i)
  if not p0 or p1<=0:continue
  mom=p1/p0-1
  if mom<=0: continue
  if p1<=f['e20'] or p1>f['e20']*1.18: continue
  out.append((mom+0.002*f['adx'],s,i))
 out.sort(reverse=True)
 return out[:c['top']]

def sleeve(days,c,fee=FEE):
 ds=[d for d in days if d in b.bi.breadth_cache]
 if not ds:return {'ret':0,'dd':0,'n':0,'turns':0}
 cash=START; pos={}; peak=START; dd=0; tr=[]; last=ds[-1]; turns=0
 for day in ds:
  on=regime(day)
  for s in list(pos):
   i=idx(s,day)
   if i is None: continue
   p=pos[s]; p['age']+=1; f=b.bi.feat(s,i)
   if p['age']>=c['hold'] or close(s,i)<f['e20'] or not on:
    px=b.bi.data[s][i]['o'] if i>0 else close(s,i); pro=p['q']*px*(1-fee); cash+=pro; tr.append(pro-p['cost']); del pos[s]; turns+=1
  if on:
   picks=candidates(day,c)
   for _,s,i in picks:
    if s in pos or len(pos)>=c['top']: continue
    px=b.bi.data[s][i]['o']; alloc=(cash*(1-c['cash']))/max(1,c['top']-len(pos)); q=int(alloc/(px*(1+fee)))
    if q<=0: continue
    cost=q*px*(1+fee); cash-=cost; pos[s]={'q':q,'cost':cost,'age':0}; turns+=1
  eq=cash
  for s,p in pos.items():
   i=idx(s,day)
   if i is not None:eq+=p['q']*close(s,i)
  peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
 for s,p in list(pos.items()):
  i=v25.idx_at_or_before(s,last); px=close(s,i) if i is not None else p['cost']/max(1,p['q']); pro=p['q']*px*(1-fee); cash+=pro; tr.append(pro-p['cost']); turns+=1
 return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'turns':turns}

def mix(days,c,w):
 a=v24.run(days,1.6)
 s=sleeve(days,c)
 ret=(1-w)*a['ret']+w*s['ret']; dd=(1-w)*a['dd']+w*s['dd']
 return {'ret':ret,'dd':dd,'active':a['ret'],'sleeve':s['ret'],'n':s['n'],'turns':s['turns']}

chunks=[D[i:i+22] for i in range(0,len(D)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for c in CANDS:
 for w in (.15,.25,.35):
  rr=[mix(x,c,w) for x in dev]; avg=sum(x['ret'] for x in rr)/len(rr); worst=min(x['ret'] for x in rr); dd=sum(x['dd'] for x in rr)/len(rr); pos=sum(x['ret']>0 for x in rr); turns=sum(x['turns'] for x in rr)
  score=avg+.7*worst-.4*dd+.05*pos-.002*turns
  rows.append({'c':c['name'],'w':w,'avg':avg,'worst':worst,'dd':dd,'pos':pos,'turns':turns,'score':score})
best=max(rows,key=lambda x:x['score']); cfg=next(c for c in CANDS if c['name']==best['c'])
hr=[mix(x,cfg,best['w']) for x in hold]; full=mix(D,cfg,best['w']); bench=v25.proxy_benchmark(D)
lines=['# BR-SMART v30 Structural Bull + Relative Strength','v24 D1.6 savunma motoru sabit. Boğa katmanı: 3 günlük rejim teyidi + likit evrende relatif momentum/ADX/CMF seçimi. Parametreler yalnız ilk 6 fold.','','|Cfg|Bull pay|DevAvg|Worst|DD|Pos|Turns|Score|','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in sorted(rows,key=lambda z:z['score'],reverse=True):lines.append(f'|{x["c"]}|{x["w"]:.0%}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["dd"]:.2f}%|{x["pos"]}/6|{x["turns"]}|{x["score"]:.3f}|')
lines+=['',f'Seçilen: **{best["c"]} / bull pay {best["w"]:.0%}**.',f'Full mix **{full["ret"]:.2f}%**, DD yaklaşık **{full["dd"]:.2f}%**; aktif **{full["active"]:.2f}%**, bull sleeve **{full["sleeve"]:.2f}%**, proxy **{bench:.2f}%**.',f'Holdout avg **{sum(x["ret"] for x in hr)/len(hr):.2f}%**, worst **{min(x["ret"] for x in hr):.2f}%**, positive **{sum(x["ret"]>0 for x in hr)}/{len(hr)}**.','','|Hold|Mix|Active|Bull sleeve|DD|N|Turns|','|---:|---:|---:|---:|---:|---:|---:|']
for i,x in enumerate(hr,1):lines.append(f'|{i}|{x["ret"]:.2f}%|{x["active"]:.2f}%|{x["sleeve"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["turns"]}|')
Path('research/result_v30_structural_bull_rs.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v30_structural_bull_rs.json').write_text(json.dumps({'rows':rows,'best':best,'full':full,'holdout':hr,'benchmark':bench},indent=2),encoding='utf-8');print('\n'.join(lines))