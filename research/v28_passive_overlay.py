# v28: regime-aware passive participation overlay diagnostic
# Combines fixed v24 D1.6 active return with investable equal-weight liquid-universe proxy sleeve.
# Overlay parameters selected on first 6 x 22d folds only; later folds are validation.
import json
from pathlib import Path
import backtest_br_smart as b
import v23_hybrid_stop as h
import v25_concentration_benchmark as v

D=b.DATES
WEIGHTS=[0.25,0.50,0.75]
BR=[0.50,0.55,0.60]

def px(s,d):
 i=v.idx_at_or_before(s,d)
 return b.bi.data[s][i]['c'] if i is not None else None

def liquid(day):
 out=[]
 for s,a in b.bi.data.items():
  i=b.bi.bysym[s].get(day)
  if i is None or i<65: continue
  turn,vol,j=b.bi.quality(s,i)
  if turn>=120_000_000 and vol>=120_000 and j<2: out.append(s)
 return out

def proxy_path(days):
 ds=[d for d in days if d in b.bi.breadth_cache]
 if len(ds)<2:return [1.0]*len(ds)
 names=liquid(ds[0]); vals=[1.0]
 for k in range(1,len(ds)):
  re=[]
  for s in names:
   p0=px(s,ds[k-1]);p1=px(s,ds[k])
   if p0 and p1: re.append(p1/p0-1)
  vals.append(vals[-1]*(1+(sum(re)/len(re) if re else 0)))
 return vals

def active(days):
 r=h.sim_hybrid(days,1.6,b.FEE)
 return r

def overlay(days,w,brmin):
 ds=[d for d in days if d in b.bi.breadth_cache]; a=active(ds); pp=proxy_path(ds)
 # Approximation: fixed active sleeve return plus daily regime-gated proxy sleeve.
 # Costs charged 10bp one-way on each overlay regime transition.
 ov=1.;on=False;turns=0;peak=1.;dd=0
 for k in range(1,len(ds)):
  br,bd,strong,recovery,weak=b.state(ds[k])
  want=(br>=brmin and bd>=-.01 and not weak)
  if want!=on: ov*=1-0.001*w;turns+=1;on=want
  r=pp[k]/pp[k-1]-1
  if on: ov*=1+w*r
  peak=max(peak,ov);dd=max(dd,(peak-ov)/peak)
 # active result and overlay are separate capital sleeves: active engine remains on full capital;
 # overlay is reported as incremental diagnostic, not executable combined leverage.
 inc=(ov-1)*100
 return {'active':a['ret'],'inc':inc,'combined_diag':a['ret']+inc,'overlay_dd':dd*100,'turns':turns,'n':a['n'],'pf':a['pf']}

chunks=[D[i:i+22] for i in range(0,len(D)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for w in WEIGHTS:
 for br in BR:
  rr=[overlay(x,w,br) for x in dev];avg=sum(x['combined_diag'] for x in rr)/6;worst=min(x['combined_diag'] for x in rr);odd=sum(x['overlay_dd'] for x in rr)/6;pos=sum(x['combined_diag']>0 for x in rr);turn=sum(x['turns'] for x in rr);score=avg+.6*worst-.35*odd+.05*pos-.005*turn
  rows.append({'w':w,'br':br,'avg':avg,'worst':worst,'odd':odd,'pos':pos,'turns':turn,'score':score})
best=max(rows,key=lambda x:x['score']);hr=[overlay(x,best['w'],best['br']) for x in hold];full=overlay(D,best['w'],best['br']);bench=v.proxy_benchmark(D)
lines=['# BR-SMART v28 Regime-aware Passive Overlay','v24 D1.6 aktif motor sabit. Pasif katman yalnız piyasa breadth rejiminde açılıyor. Parametre seçimi ilk 6 geliştirme foldunda. **combined_diag kaldıraçsız gerçek portföy getirisi değildir; overlay fikrinin artı değer teşhisidir.**','','|W|Breadth|DevAvg diag|Worst|OverlayDD|Pos|Turns|Score|','|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in sorted(rows,key=lambda z:z['score'],reverse=True):lines.append(f'|{x["w"]:.0%}|{x["br"]:.2f}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["odd"]:.2f}%|{x["pos"]}/6|{x["turns"]}|{x["score"]:.3f}|')
lines+=['',f'Seçilen overlay: **{best["w"]:.0%} / breadth>={best["br"]:.2f}**.',f'Full aktif **{full["active"]:.2f}%**, overlay incremental **{full["inc"]:.2f}%**, diagnostic toplam **{full["combined_diag"]:.2f}%**, overlay DD **{full["overlay_dd"]:.2f}%**, geçiş **{full["turns"]}**, proxy **{bench:.2f}%**.',f'Holdout diagnostic avg **{sum(x["combined_diag"] for x in hr)/len(hr):.2f}%**, worst **{min(x["combined_diag"] for x in hr):.2f}%**, positive **{sum(x["combined_diag"]>0 for x in hr)}/{len(hr)}**.','','|Hold|Active|Overlay inc|Combined diag|OverlayDD|Turns|','|---:|---:|---:|---:|---:|---:|']
for i,x in enumerate(hr,1):lines.append(f'|{i}|{x["active"]:.2f}%|{x["inc"]:.2f}%|{x["combined_diag"]:.2f}%|{x["overlay_dd"]:.2f}%|{x["turns"]}|')
Path('research/result_v28_overlay.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v28_overlay.json').write_text(json.dumps({'rows':rows,'best':best,'full':full,'benchmark':bench,'holdout':hr},indent=2),encoding='utf-8');print('\n'.join(lines))