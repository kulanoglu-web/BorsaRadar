# BR-SMART v26: bull participation overlay, selected on development folds only
import json
from pathlib import Path
import v25_concentration_benchmark as v
import backtest_br_smart as b

DATES=b.DATES; START=100000.; FEE=b.FEE; CFG=b.BASE; DISASTER=1.6

# Candidate overlays deliberately coarse. Base v24 entry remains unchanged outside strong breadth.
OVERLAYS=[
 {'name':'BASE','br':9.0,'maxpos':2,'risk':1.0,'adx':35,'rvol':1.35,'score':0},
 {'name':'BULL_A','br':.58,'maxpos':3,'risk':.85,'adx':38,'rvol':1.20,'score':0},
 {'name':'BULL_B','br':.60,'maxpos':3,'risk':.85,'adx':40,'rvol':1.15,'score':0},
 {'name':'BULL_C','br':.62,'maxpos':4,'risk':.70,'adx':38,'rvol':1.15,'score':0},
 {'name':'BULL_D','br':.58,'maxpos':3,'risk':.75,'adx':38,'rvol':1.10,'score':4},
]

def run(days,o):
 ds=[d for d in days if d in b.bi.breadth_cache]
 if not ds:return {'ret':0,'dd':0,'n':0,'pf':0,'win':0,'trades':[]}
 last=ds[-1];cash=START;pos={};tr=[];peak=START;dd=0;cool={}
 for day in ds:
  for s in list(pos):
   i=b.bi.bysym[s].get(day)
   if i is None:continue
   a=b.bi.data[s];bar=a[i];p=pos[s];f=b.bi.feat(s,i);m=f['m'];p['hi']=max(p['hi'],bar['h']);p['age']+=1;gain=p['hi']/p['en']-1;normal=p['hard']
   if gain>=CFG['be']:normal=max(normal,p['en']*1.001)
   if gain>=CFG['trail_on']:normal=max(normal,p['hi']-CFG['trail_atr']*p['atr'])
   if gain>=.08:normal=max(normal,p['en']*1.025,p['hi']-(CFG['trail_atr']-.3)*p['atr'])
   if gain>=.13:normal=max(normal,p['en']*1.07,p['hi']-(CFG['trail_atr']-.6)*p['atr'])
   ex=reason=None; disaster=min(p['en']-DISASTER*p['atr'],p['en']*.97)
   if bar['l']<=disaster:ex=bar['o'] if bar['o']<disaster else disaster;reason='DISASTER'
   if ex is None and a[i-1]['c']<=normal:ex=bar['o'];reason='CLOSESTOP'
   if ex is None:
    cp=a[i-1]['c'];un=cp/p['en']-1;ok,_,_=b.allowed(day)
    if not ok and p['age']>=2 and un<.015:ex=bar['o'];reason='REGIME'
    elif p['age']>=4 and un<-.007 and gain<.02:ex=bar['o'];reason='FAIL'
    elif gain>=CFG['trail_on'] and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
   if ex:
    pro=p['q']*ex*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append({'s':s,'pnl':pnl,'bull':p['bull']});del pos[s];cool[s]=day
  ok,base_mp,base_risk=b.allowed(day);br,bd,strong,recovery,weak=b.state(day);bull=(br>=o['br'] and bd>=-.01 and not weak)
  if bull:ok=True;maxpos=o['maxpos'];risk=base_risk*o['risk']
  else:maxpos=base_mp;risk=base_risk
  slots=maxpos-len(pos)
  if slots>0 and ok:
   ca=[]
   for s,a in b.bi.data.items():
    if s in pos:continue
    i=b.bi.bysym[s].get(day)
    if i is None or i<65 or (s in cool and day-cool[s]<4*86400):continue
    turn,vol,j=b.bi.quality(s,i)
    if turn<120_000_000 or vol<120_000 or j>=2:continue
    gap=a[i]['o']/a[i-1]['c']-1
    if a[i]['o']<5 or not(-.03<=gap<=.012):continue
    z=v.v.v20_sig(s,i,day)
    if z:ca.append((z[0],s,i,z[1]));continue
    if bull:
     f=b.bi.feat(s,i);m=f['m'];pm=b.bi.feat(s,i-1)['m'];bar=a[i-1];rng=max(.001,bar['h']-bar['l']);cp=(bar['c']-bar['l'])/rng;dh=(m['mac']-m['ms'])-(pm['mac']-pm['ms'])
     if (not m['trap'] and f['rv']>=o['rvol'] and f['cmf']>=0 and cp>=.52 and 48<=f['rsi']<=72 and 16<=f['adx']<=o['adx'] and dh>0 and f['acc']>-.005 and bar['c']>=f['e20']*.995):
      sc=50+12*min(2,f['rv'])+8*min(1,max(0,f['acc']/.04))+o['score'];ca.append((sc,s,i,f))
   ca.sort(reverse=True)
   for sc,s,i,f in ca[:slots]:
    px=b.bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(CFG['hard_atr']*atr,px*.012);q=int(min(cash/(max(1,slots)*px*(1+FEE)),START*risk/max(.01,px-hard)))
    if q<=0:continue
    cost=q*px*(1+FEE);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost,'bull':bull};slots-=1
  eq=cash
  for s,p in pos.items():
   i=b.bi.bysym[s].get(day)
   if i is None:i=v.idx_at_or_before(s,day)
   eq+=p['q']*(b.bi.data[s][i]['c'] if i is not None else p['en'])
  peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
 for s,p in list(pos.items()):
  i=v.idx_at_or_before(s,last);px=b.bi.data[s][i]['c'] if i is not None else p['en'];pro=p['q']*px*(1-FEE);cash+=pro;tr.append({'s':s,'pnl':pro-p['cost'],'bull':p['bull']})
 gp=sum(x['pnl'] for x in tr if x['pnl']>0);gl=-sum(x['pnl'] for x in tr if x['pnl']<0);wins=sum(x['pnl']>0 for x in tr)
 return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'pf':gp/gl if gl else (99 if gp else 0),'win':100*wins/len(tr) if tr else 0,'trades':tr}

chunks=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for o in OVERLAYS:
 rr=[run(ch,o) for ch in dev];active=[x for x in rr if x['n']];avg=sum(x['ret'] for x in rr)/len(rr);worst=min(x['ret'] for x in rr);dd=sum(x['dd'] for x in rr)/len(rr);pf=sum(min(5,x['pf']) for x in active)/len(active) if active else 0;n=sum(x['n'] for x in rr);pos=sum(x['ret']>0 for x in rr);score=avg+.65*worst-.45*dd+.25*(pf-1)+.06*pos-(.2 if n<14 else 0);rows.append({'o':o,'avg':avg,'worst':worst,'dd':dd,'pf':pf,'n':n,'pos':pos,'score':score})
best=max(rows,key=lambda x:x['score']);hr=[run(ch,best['o']) for ch in hold];full=run(DATES,best['o']);bench=v.proxy_benchmark(DATES);bulltr=[x for x in full['trades'] if x['bull']]
lines=['# BR-SMART v26 Bull Participation','Boğa katılım parametreleri yalnız ilk 6 geliştirme foldunda seçildi. v24 D1.6 defansif motor sabit. TUPRS/savunma hariç.','','|Mod|DevAvg|Worst|DD|PF|N|Pos|Score|','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in sorted(rows,key=lambda z:z['score'],reverse=True):lines.append(f'|{x["o"]["name"]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["dd"]:.2f}%|{x["pf"]:.2f}|{x["n"]}|{x["pos"]}/6|{x["score"]:.3f}|')
lines+=['',f'Seçilen: **{best["o"]["name"]}**.',f'Full: **{full["ret"]:.2f}%**, DD **{full["dd"]:.2f}%**, PF **{full["pf"]:.2f}**, N **{full["n"]}**, bull işlemi **{len(bulltr)}**. Proxy **{bench:.2f}%**, relatif **{full["ret"]-bench:.2f} puan**.',f'Holdout avg **{sum(x["ret"] for x in hr)/len(hr):.2f}%**, worst **{min(x["ret"] for x in hr):.2f}%**, positive **{sum(x["ret"]>0 for x in hr)}/{len(hr)}**, N **{sum(x["n"] for x in hr)}**.','','|Hold|Ret|DD|PF|N|','|---:|---:|---:|---:|---:|']
for i,x in enumerate(hr,1):lines.append(f'|{i}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["pf"]:.2f}|{x["n"]}|')
Path('research/result_v26_bull.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v26_bull.json').write_text(json.dumps({'rows':rows,'best':best,'full':{k:full[k] for k in ('ret','dd','pf','n','win')},'benchmark':bench,'holdout':[{k:x[k] for k in ('ret','dd','pf','n','win')} for x in hr]},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))