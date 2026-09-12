# v29: capital-split participation with hysteresis; avoids v28 double-counting
import json
from pathlib import Path
import backtest_br_smart as b
import v24_microplateau_slippage as h
import v25_concentration_benchmark as v

D=b.DATES
CANDS=[]
for w in (.10,.15,.25):
 for enter,exit_ in ((.58,.48),(.60,.50),(.62,.52)):
  for confirm in (1,2): CANDS.append({'w':w,'enter':enter,'exit':exit_,'confirm':confirm})

def px(s,d):
 i=v.idx_at_or_before(s,d);return b.bi.data[s][i]['c'] if i is not None else None

def liquid(day):
 out=[]
 for s,a in b.bi.data.items():
  i=b.bi.bysym[s].get(day)
  if i is None or i<65:continue
  turn,vol,j=b.bi.quality(s,i)
  if turn>=120_000_000 and vol>=120_000 and j<2:out.append(s)
 return out

def pp(days):
 ds=[d for d in days if d in b.bi.breadth_cache]
 if len(ds)<2:return ds,[1.]
 names=liquid(ds[0]);z=[1.]
 for k in range(1,len(ds)):
  rr=[]
  for s in names:
   p0,p1=px(s,ds[k-1]),px(s,ds[k])
   if p0 and p1:rr.append(p1/p0-1)
  z.append(z[-1]*(1+(sum(rr)/len(rr) if rr else 0)))
 return ds,z

def passive(days,c,fee=.001):
 ds,p=pp(days);val=1.;on=False;en=ex=0;turns=0;peak=1.;dd=0;days_on=0
 for k in range(1,len(ds)):
  br,bd,strong,recovery,weak=b.state(ds[k])
  if not on:
   en=en+1 if br>=c['enter'] and bd>=0 and not weak else 0
   if en>=c['confirm']:on=True;val*=1-fee;turns+=1;en=0
  else:
   ex=ex+1 if br<=c['exit'] or weak else 0
   if ex>=c['confirm']:on=False;val*=1-fee;turns+=1;ex=0
  if on:
   val*=p[k]/p[k-1];days_on+=1
  peak=max(peak,val);dd=max(dd,(peak-val)/peak)
 return {'ret':(val-1)*100,'dd':dd*100,'turns':turns,'days_on':days_on}

def split(days,c,fee=.001):
 a=h.run(days,1.6,b.FEE,0.0);q=passive(days,c,fee);w=c['w']
 # Separate non-levered sleeves. Active sleeve gets 1-w, passive/cash sleeve gets w.
 ret=(1-w)*a['ret']+w*q['ret']
 # conservative DD upper bound by weighted component DDs
 dd=(1-w)*a['dd']+w*q['dd']
 return {'ret':ret,'dd':dd,'active':a['ret'],'passive':q['ret'],'turns':q['turns'],'days_on':q['days_on'],'n':a['n']}

chunks=[D[i:i+22] for i in range(0,len(D)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for c in CANDS:
 r=[split(x,c) for x in dev];avg=sum(x['ret'] for x in r)/6;worst=min(x['ret'] for x in r);dd=sum(x['dd'] for x in r)/6;pos=sum(x['ret']>0 for x in r);turn=sum(x['turns'] for x in r);score=avg+.65*worst-.45*dd+.06*pos-.006*turn
 rows.append({'c':c,'avg':avg,'worst':worst,'dd':dd,'pos':pos,'turns':turn,'score':score})
best=max(rows,key=lambda x:x['score']);hr=[split(x,best['c']) for x in hold];full=split(D,best['c']);bench=v.proxy_benchmark(D)
lines=['# BR-SMART v29 Hysteresis Capital Split','Aynı 100.000 TL sermaye iki kovaya ayrılıyor; kaldıraç yok. Aktif v24 D1.6 payı + rejim teyitli pasif pay. Parametre yalnız ilk 6 fold.','','|Passive pay|Enter/Exit|Confirm|DevAvg|Worst|DD est|Pos|Turns|Score|','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
for x in sorted(rows,key=lambda z:z['score'],reverse=True)[:12]:
 c=x['c'];lines.append(f'|{c["w"]:.0%}|{c["enter"]:.2f}/{c["exit"]:.2f}|{c["confirm"]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["dd"]:.2f}%|{x["pos"]}/6|{x["turns"]}|{x["score"]:.3f}|')
c=best['c'];lines+=['',f'Seçilen: pasif **{c["w"]:.0%}**, enter/exit **{c["enter"]:.2f}/{c["exit"]:.2f}**, confirm **{c["confirm"]}**.',f'Full split **{full["ret"]:.2f}%**, DD tahmini **{full["dd"]:.2f}%**, aktif motor tek başına **{full["active"]:.2f}%**, pasif sleeve kendi sermayesinde **{full["passive"]:.2f}%**, geçiş **{full["turns"]}**, proxy **{bench:.2f}%**.',f'Holdout avg **{sum(x["ret"] for x in hr)/len(hr):.2f}%**, worst **{min(x["ret"] for x in hr):.2f}%**, positive **{sum(x["ret"]>0 for x in hr)}/{len(hr)}**.','','|Hold|Split|Active|Passive sleeve|DD est|Turns|','|---:|---:|---:|---:|---:|---:|']
for i,x in enumerate(hr,1):lines.append(f'|{i}|{x["ret"]:.2f}%|{x["active"]:.2f}%|{x["passive"]:.2f}%|{x["dd"]:.2f}%|{x["turns"]}|')
Path('research/result_v29_split.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v29_split.json').write_text(json.dumps({'rows':rows,'best':best,'full':full,'benchmark':bench,'holdout':hr},indent=2),encoding='utf-8');print('\n'.join(lines))