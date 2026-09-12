# v31 risk-controlled structural bull sleeve
import json
from pathlib import Path
import backtest_br_smart as b
import v24_microplateau_slippage as v24
import v25_concentration_benchmark as v25

D=b.DATES; START=100000.; FEE=b.FEE
CANDS=[
 {'name':'R1','look':40,'top':3,'hold':15,'risk':.006,'stop':2.2,'trail':3.0},
 {'name':'R2','look':40,'top':3,'hold':20,'risk':.005,'stop':2.5,'trail':3.2},
 {'name':'R3','look':20,'top':3,'hold':12,'risk':.005,'stop':2.2,'trail':2.8},
 {'name':'R4','look':40,'top':4,'hold':15,'risk':.004,'stop':2.2,'trail':3.0},
]

def idx(s,d): return b.bi.bysym[s].get(d)
def C(s,i):return b.bi.data[s][i]['c']
def regime(day):
 p=D.index(day)
 if p<60:return False
 good=0
 for k in range(3):
  br,bd,strong,recovery,weak=b.state(D[p-k])
  if br>=.55 and not weak: good+=1
 return good==3

def rank(day,c):
 out=[]
 for s,a in b.bi.data.items():
  i=idx(s,day)
  if i is None or i<max(65,c['look']+2):continue
  turn,vol,j=b.bi.quality(s,i)
  if turn<120_000_000 or vol<120_000 or j>=2:continue
  f=b.bi.feat(s,i); px=C(s,i); p0=C(s,i-c['look'])
  if f['adx']<18 or f['cmf']<=0 or px<=f['e20'] or px>f['e20']*1.15:continue
  mom=px/p0-1
  if mom<=.02:continue
  atr=max(f['m']['atr'],px*.01)
  score=mom+0.0015*f['adx']-0.20*(atr/px)
  out.append((score,s,i,atr))
 return sorted(out,reverse=True)[:c['top']]

def run(days,c,fee=FEE):
 ds=[d for d in days if d in b.bi.breadth_cache]
 if not ds:return {'ret':0,'dd':0,'n':0,'turns':0,'win':0}
 cash=START;pos={};peak=START;dd=0;tr=[];turns=0;last=ds[-1]
 for day in ds:
  on=regime(day)
  for s in list(pos):
   i=idx(s,day)
   if i is None:continue
   a=b.bi.data[s]; bar=a[i];p=pos[s];p['age']+=1;p['hi']=max(p['hi'],bar['h'])
   f=b.bi.feat(s,i); dyn=max(p['stop'],p['hi']-c['trail']*p['atr'])
   ex=None
   if bar['l']<=dyn:ex=bar['o'] if bar['o']<dyn else dyn
   elif not on or p['age']>=c['hold'] or C(s,i)<f['e20']:ex=bar['o']
   if ex is not None:
    pro=p['q']*ex*(1-fee);cash+=pro;tr.append(pro-p['cost']);del pos[s];turns+=1
  if on and len(pos)<c['top']:
   for _,s,i,atr in rank(day,c):
    if s in pos or len(pos)>=c['top']:continue
    px=b.bi.data[s][i]['o']; stop=px-c['stop']*atr; riskps=max(.01,px-stop)
    q_risk=int((START*c['risk'])/riskps)
    q_cash=int((cash/max(1,c['top']-len(pos)))/(px*(1+fee)))
    q=min(q_risk,q_cash)
    if q<=0:continue
    cost=q*px*(1+fee);cash-=cost;pos[s]={'q':q,'cost':cost,'stop':stop,'atr':atr,'hi':px,'age':0};turns+=1
  eq=cash
  for s,p in pos.items():
   i=idx(s,day)
   if i is not None:eq+=p['q']*C(s,i)
  peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
 for s,p in list(pos.items()):
  i=v25.idx_at_or_before(s,last);px=C(s,i) if i is not None else p['cost']/max(1,p['q']);pro=p['q']*px*(1-fee);cash+=pro;tr.append(pro-p['cost'])
 gp=sum(x for x in tr if x>0);gl=-sum(x for x in tr if x<0);win=sum(x>0 for x in tr)
 return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'turns':turns,'win':100*win/len(tr) if tr else 0,'pf':gp/gl if gl else (99 if gp else 0)}

def mix(days,c,w):
 a=v24.run(days,1.6);s=run(days,c);return {'ret':(1-w)*a['ret']+w*s['ret'],'dd':(1-w)*a['dd']+w*s['dd'],'active':a['ret'],'sleeve':s['ret'],'sdd':s['dd'],'n':s['n'],'pf':s['pf']}
chunks=[D[i:i+22] for i in range(0,len(D)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for c in CANDS:
 for w in (.15,.20,.25):
  rr=[mix(x,c,w) for x in dev];avg=sum(x['ret'] for x in rr)/6;worst=min(x['ret'] for x in rr);dd=sum(x['dd'] for x in rr)/6;pos=sum(x['ret']>0 for x in rr); score=avg+.8*worst-.65*dd+.05*pos
  rows.append({'c':c['name'],'w':w,'avg':avg,'worst':worst,'dd':dd,'pos':pos,'score':score})
best=max(rows,key=lambda x:x['score']);cfg=next(c for c in CANDS if c['name']==best['c']);hr=[mix(x,cfg,best['w']) for x in hold];full=mix(D,cfg,best['w']);bench=v25.proxy_benchmark(D)
lines=['# BR-SMART v31 Risk-Controlled Relative Strength','v30 yönü korunup bull sleeve ATR risk sizing + hard/trailing stop ile sınırlandı. Seçim yalnız ilk 6 fold.','','|Cfg|Bull pay|DevAvg|Worst|DD|Pos|Score|','|---|---:|---:|---:|---:|---:|---:|']
for x in sorted(rows,key=lambda z:z['score'],reverse=True):lines.append(f'|{x["c"]}|{x["w"]:.0%}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["dd"]:.2f}%|{x["pos"]}/6|{x["score"]:.3f}|')
lines+=['',f'Seçilen **{best["c"]} / {best["w"]:.0%} bull pay**.',f'Full mix **{full["ret"]:.2f}%**, DD approx **{full["dd"]:.2f}%**; active **{full["active"]:.2f}%**, bull sleeve **{full["sleeve"]:.2f}%**, sleeve DD **{full["sdd"]:.2f}%**, proxy **{bench:.2f}%**.',f'Holdout avg **{sum(x["ret"] for x in hr)/len(hr):.2f}%**, worst **{min(x["ret"] for x in hr):.2f}%**, positive **{sum(x["ret"]>0 for x in hr)}/{len(hr)}**.','','|Hold|Mix|Active|Sleeve|Sleeve DD|N|PF|','|---:|---:|---:|---:|---:|---:|---:|']
for i,x in enumerate(hr,1):lines.append(f'|{i}|{x["ret"]:.2f}%|{x["active"]:.2f}%|{x["sleeve"]:.2f}%|{x["sdd"]:.2f}%|{x["n"]}|{x["pf"]:.2f}|')
Path('research/result_v31_risk_controlled_rs.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v31_risk_controlled_rs.json').write_text(json.dumps({'rows':rows,'best':best,'full':full,'holdout':hr,'benchmark':bench},indent=2),encoding='utf-8');print('\n'.join(lines))