# BR-SMART v24: micro plateau around D1.8 + directional slippage stress
import json
from pathlib import Path
import v21_long_wf_diagnostics as v
import backtest_br_smart as b

START=100000.; DATES=b.DATES; CFG=b.BASE; FEE=b.FEE; DPOS={d:i for i,d in enumerate(DATES)}

def idx_at_or_before(s,day):
    i=DPOS.get(day,len(DATES)-1)
    for j in range(i,-1,-1):
        z=b.bi.bysym[s].get(DATES[j])
        if z is not None:return z
    return None

def run(days, disaster_mult=None, fee=FEE, slip=0.0):
    ds=[d for d in days if d in b.bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0,'reasons':{}}
    last=ds[-1];cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in ds:
        for s in list(pos):
            i=b.bi.bysym[s].get(day)
            if i is None:continue
            a=b.bi.data[s];bar=a[i];p=pos[s];f=b.bi.feat(s,i);m=f['m'];p['hi']=max(p['hi'],bar['h']);p['age']+=1
            gain=p['hi']/p['en']-1;normal=p['hard']
            if gain>=CFG['be']:normal=max(normal,p['en']*1.001)
            if gain>=CFG['trail_on']:normal=max(normal,p['hi']-CFG['trail_atr']*p['atr'])
            if gain>=.08:normal=max(normal,p['en']*1.025,p['hi']-(CFG['trail_atr']-.3)*p['atr'])
            if gain>=.13:normal=max(normal,p['en']*1.07,p['hi']-(CFG['trail_atr']-.6)*p['atr'])
            ex=reason=None
            if disaster_mult is not None:
                disaster=min(p['en']-disaster_mult*p['atr'],p['en']*.97)
                if bar['l']<=disaster:
                    raw=bar['o'] if bar['o']<disaster else disaster;ex=raw*(1-slip);reason='DISASTER'
            if ex is None and a[i-1]['c']<=normal:
                ex=bar['o']*(1-slip);reason='CLOSESTOP'
            if ex is None:
                cp=a[i-1]['c'];un=cp/p['en']-1;ok,_,_=b.allowed(day)
                if not ok and p['age']>=2 and un<.015:ex=bar['o']*(1-slip);reason='REGIME'
                elif p['age']>=4 and un<-.007 and gain<.02:ex=bar['o']*(1-slip);reason='FAIL'
                elif gain>=CFG['trail_on'] and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o']*(1-slip);reason='TREND'
            if ex:
                pro=p['q']*ex*(1-fee);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,reason));del pos[s];cool[s]=day
        ok,maxpos,risk=b.allowed(day);slots=maxpos-len(pos)
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
                z=v.v20_sig(s,i,day)
                if z:ca.append((z[0],s,i,z[1]))
            ca.sort(reverse=True)
            for sc,s,i,f in ca[:slots]:
                raw=b.bi.data[s][i]['o'];px=raw*(1+slip);atr=max(f['m']['atr'],raw*.01);hard=px-max(CFG['hard_atr']*atr,px*.012);q=int(min(cash/(max(1,slots)*px*(1+fee)),START*risk/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+fee);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=b.bi.bysym[s].get(day)
            if i is None:i=idx_at_or_before(s,day)
            eq+=p['q']*(b.bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        i=idx_at_or_before(s,last);raw=b.bi.data[s][i]['c'] if i is not None else p['en'];px=raw*(1-slip);pro=p['q']*px*(1-fee);cash+=pro;tr.append((pro-p['cost'],'SON'))
    gp=sum(x[0] for x in tr if x[0]>0);gl=-sum(x[0] for x in tr if x[0]<0);wins=sum(x[0]>0 for x in tr);reasons={}
    for _,r in tr:reasons[r]=reasons.get(r,0)+1
    return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*wins/len(tr) if tr else 0,'pf':gp/gl if gl else (99 if gp else 0),'reasons':reasons}

def summarize(rr):
    aa=[x for x in rr if x['n']]
    return {'avg':sum(x['ret'] for x in rr)/len(rr) if rr else 0,'worst':min((x['ret'] for x in rr),default=0),'pos':sum(x['ret']>0 for x in rr),'dd':sum(x['dd'] for x in rr)/len(rr) if rr else 0,'n':sum(x['n'] for x in rr),'pf':sum(min(5,x['pf']) for x in aa)/len(aa) if aa else 0}

folds=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)];wf_folds=folds[4:]
models=[('CLOSE_ONLY',None),('D1.6',1.6),('D1.8',1.8),('D2.0',2.0)]
rows=[]
for name,mult in models:
    full=run(DATES,mult);wf=summarize([run(ch,mult) for ch in wf_folds]);score=full['ret']-0.70*full['dd']+1.25*wf['avg']+0.45*wf['worst']+0.10*min(3,full['pf'])
    rows.append({'name':name,'mult':mult,'full':full,'wf':wf,'score':score})
# independent window robustness
windows=[]
for name,mult in models:
    rr=[]
    for w in (15,22,30):
      for off in (0,5,10):
        ps=[DATES[i:i+w] for i in range(off,len(DATES)-w+1,w)];s=summarize([run(ch,mult) for ch in ps]);rr.append(s);windows.append({'name':name,'w':w,'off':off,**s})
    r=next(x for x in rows if x['name']==name);r['window_avg']=sum(x['avg'] for x in rr)/len(rr);r['window_worst']=min(x['worst'] for x in rr)
# directional slippage: each entry worse by slip and each exit worse by slip; fee fixed at baseline
slips=[]
for name,mult in models:
  for slip in (0.0,.0005,.001,.002,.003):
    full=run(DATES,mult,FEE,slip);wf=summarize([run(ch,mult,FEE,slip) for ch in wf_folds]);slips.append({'name':name,'slip':slip,'full':full,'wf':wf})
# Combined heavier execution friction: fee + directional slippage
combo=[]
for name,mult in models:
  for fee,slip in ((.0015,.0005),(.002,.001),(.003,.002)):
    full=run(DATES,mult,fee,slip);wf=summarize([run(ch,mult,fee,slip) for ch in wf_folds]);combo.append({'name':name,'fee':fee,'slip':slip,'full':full,'wf':wf})
rows.sort(key=lambda x:x['score'],reverse=True)
lines=['# BR-SMART v24 Micro-Plateau + Slippage Stress','v20 girişleri sabit. Close-confirm normal stop sabit. Felaket stopu 1.6/1.8/2.0 ATR mikro-platosu; ayrıca yönlü slippage ve birleşik maliyet stresi. TUPRS/savunma hariç.','','## Risk-adjusted comparison','|Model|Full Ret|DD|PF|N|WF Avg|Worst|WF PF|WinAvg|WinWorst|Score|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
 f=r['full'];w=r['wf'];lines.append(f'|{r["name"]}|{f["ret"]:.2f}%|{f["dd"]:.2f}%|{f["pf"]:.2f}|{f["n"]}|{w["avg"]:.2f}%|{w["worst"]:.2f}%|{w["pf"]:.2f}|{r["window_avg"]:.2f}%|{r["window_worst"]:.2f}%|{r["score"]:.3f}|')
lines+=['','## Directional slippage stress','|Model|Slip each side|Full Ret|DD|PF|WF Avg|Worst|WF PF|','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in slips:
 f=x['full'];w=x['wf'];lines.append(f'|{x["name"]}|{100*x["slip"]:.2f}%|{f["ret"]:.2f}%|{f["dd"]:.2f}%|{f["pf"]:.2f}|{w["avg"]:.2f}%|{w["worst"]:.2f}%|{w["pf"]:.2f}|')
lines+=['','## Combined fee + slippage','|Model|Fee one-way|Slip each side|Full Ret|DD|PF|WF Avg|Worst|','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in combo:
 f=x['full'];w=x['wf'];lines.append(f'|{x["name"]}|{100*x["fee"]:.2f}%|{100*x["slip"]:.2f}%|{f["ret"]:.2f}%|{f["dd"]:.2f}%|{f["pf"]:.2f}|{w["avg"]:.2f}%|{w["worst"]:.2f}%|')
Path('research/result_v24_microplateau_slippage.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v24_microplateau_slippage.json').write_text(json.dumps({'rows':rows,'windows':windows,'slippage':slips,'combo':combo},indent=2),encoding='utf-8');print('\n'.join(lines))