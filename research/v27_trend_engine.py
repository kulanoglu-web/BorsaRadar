# BR-SMART v27: independent bull trend-following engine diagnostic
# Goal: test a genuinely different trend/breakout sleeve, not relaxed BR-SMART.
import json
from pathlib import Path
import backtest_br_smart as b
import v25_concentration_benchmark as v25

D=b.DATES; START=100000.; FEE=b.FEE
CANDS=[
 {'name':'T1','br':.54,'adx':22,'rv':1.05,'mom20':.03,'break_n':20,'maxpos':3,'risk':.0015},
 {'name':'T2','br':.56,'adx':24,'rv':1.10,'mom20':.04,'break_n':20,'maxpos':3,'risk':.0015},
 {'name':'T3','br':.58,'adx':24,'rv':1.05,'mom20':.03,'break_n':30,'maxpos':3,'risk':.0014},
 {'name':'T4','br':.54,'adx':26,'rv':1.00,'mom20':.05,'break_n':30,'maxpos':2,'risk':.0017},
]

def prev_high(a,i,n):
 return max(x['h'] for x in a[max(0,i-n-1):i-1]) if i>=3 else 1e99

def mom20(a,i):
 return a[i-1]['c']/a[i-21]['c']-1 if i>=21 and a[i-21]['c'] else 0

def sig(s,i,day,c):
 if i<70:return None
 br,bd,strong,recovery,weak=b.state(day)
 if weak or br<c['br']:return None
 a=b.bi.data[s]; f=b.bi.feat(s,i); bar=a[i-1]; close=bar['c']; m20=mom20(a,i)
 # independent trend logic: EMA structure + momentum + breakout + money flow
 if not (close>f['e20'] and f['e20']>f['e50'] and f['adx']>=c['adx'] and f['rv']>=c['rv'] and f['cmf']>0):return None
 if m20<c['mom20'] or f['rsi']<52 or f['rsi']>76:return None
 ph=prev_high(a,i,c['break_n'])
 if close<ph*.995:return None
 breakout=close/ph-1
 sc=35*min(1,max(0,m20/.15))+25*min(1,max(0,(f['adx']-18)/25))+20*min(1,max(0,(f['rv']-1)/1.2))+20*min(1,max(0,(breakout+.005)/.04))
 return sc,f

def sim(days,c):
 ds=[d for d in days if d in b.bi.breadth_cache]
 if not ds:return {'ret':0,'dd':0,'n':0,'pf':0,'win':0}
 cash=START;pos={};tr=[];peak=START;dd=0;last=ds[-1]
 for day in ds:
  for s in list(pos):
   i=b.bi.bysym[s].get(day)
   if i is None:continue
   a=b.bi.data[s];bar=a[i];p=pos[s];f=b.bi.feat(s,i);p['hi']=max(p['hi'],bar['h']);p['age']+=1
   stop=max(p['hard'],p['hi']-2.8*p['atr'])
   if p['hi']/p['en']-1>=.06:stop=max(stop,p['en']*1.01)
   ex=reason=None
   if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
   elif p['age']>=3 and a[i-1]['c']<f['e20']:ex=bar['o'];reason='EMA20'
   elif p['age']>=5 and mom20(a,i)<0:ex=bar['o'];reason='MOM'
   if ex:
    pro=p['q']*ex*(1-FEE);cash+=pro;tr.append(pro-p['cost']);del pos[s]
  br,bd,strong,recovery,weak=b.state(day);slots=(0 if weak else c['maxpos'])-len(pos)
  if slots>0:
   ca=[]
   for s,a in b.bi.data.items():
    if s in pos:continue
    i=b.bi.bysym[s].get(day)
    if i is None:continue
    turn,vol,j=b.bi.quality(s,i)
    if turn<120_000_000 or vol<120_000 or j>=2:continue
    gap=a[i]['o']/a[i-1]['c']-1
    if a[i]['o']<5 or not(-.025<=gap<=.018):continue
    z=sig(s,i,day,c)
    if z:ca.append((z[0],s,i,z[1]))
   ca.sort(reverse=True)
   for sc,s,i,f in ca[:slots]:
    px=b.bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-2.0*atr;q=int(min(cash/(max(1,slots)*px*(1+FEE)),START*c['risk']/max(.01,px-hard)))
    if q<=0:continue
    cost=q*px*(1+FEE);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
  eq=cash
  for s,p in pos.items():
   i=b.bi.bysym[s].get(day)
   if i is None:i=v25.idx_at_or_before(s,day)
   eq+=p['q']*(b.bi.data[s][i]['c'] if i is not None else p['en'])
  peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
 for s,p in list(pos.items()):
  i=v25.idx_at_or_before(s,last);px=b.bi.data[s][i]['c'];pro=p['q']*px*(1-FEE);cash+=pro;tr.append(pro-p['cost'])
 gp=sum(x for x in tr if x>0);gl=-sum(x for x in tr if x<0)
 return {'ret':100*(cash/START-1),'dd':100*dd,'n':len(tr),'pf':gp/gl if gl else (99 if gp else 0),'win':100*sum(x>0 for x in tr)/len(tr) if tr else 0}

chunks=[D[i:i+22] for i in range(0,len(D)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for c in CANDS:
 rr=[sim(x,c) for x in dev];active=[x for x in rr if x['n']];avg=sum(x['ret'] for x in rr)/6;worst=min(x['ret'] for x in rr);dd=sum(x['dd'] for x in rr)/6;pf=sum(min(5,x['pf']) for x in active)/len(active) if active else 0;n=sum(x['n'] for x in rr);pos=sum(x['ret']>0 for x in rr);score=avg+.65*worst-.45*dd+.25*(pf-1)+.06*pos-(.25 if n<12 else 0);rows.append({'c':c,'avg':avg,'worst':worst,'dd':dd,'pf':pf,'n':n,'pos':pos,'score':score})
best=max(rows,key=lambda x:x['score']);hr=[sim(x,best['c']) for x in hold];full=sim(D,best['c']);bench=v25.proxy_benchmark(D)
lines=['# BR-SMART v27 Independent Trend Engine','Ayrı trend/breakout motoru. Parametre seçimi yalnız ilk 6 geliştirme foldu; holdout seçime katılmadı.','','|Engine|DevAvg|Worst|DD|PF|N|Pos|Score|','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in sorted(rows,key=lambda z:z['score'],reverse=True):lines.append(f'|{x["c"]["name"]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["dd"]:.2f}%|{x["pf"]:.2f}|{x["n"]}|{x["pos"]}/6|{x["score"]:.3f}|')
lines+=['',f'Seçilen **{best["c"]["name"]}**. Full **{full["ret"]:.2f}%**, DD **{full["dd"]:.2f}%**, PF **{full["pf"]:.2f}**, N **{full["n"]}**. Proxy **{bench:.2f}%**.',f'Holdout avg **{sum(x["ret"] for x in hr)/len(hr):.2f}%**, worst **{min(x["ret"] for x in hr):.2f}%**, positive **{sum(x["ret"]>0 for x in hr)}/{len(hr)}**, N **{sum(x["n"] for x in hr)}**.','','|Hold|Ret|DD|PF|N|','|---:|---:|---:|---:|---:|']
for i,x in enumerate(hr,1):lines.append(f'|{i}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["pf"]:.2f}|{x["n"]}|')
Path('research/result_v27_trend.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v27_trend.json').write_text(json.dumps({'rows':rows,'best':best,'full':full,'benchmark':bench,'holdout':hr},indent=2),encoding='utf-8');print('\n'.join(lines))