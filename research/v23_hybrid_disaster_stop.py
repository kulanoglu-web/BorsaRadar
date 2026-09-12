# BR-SMART v23: v22 close-confirm + wider intraday disaster stop validation
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

def run(days, disaster_mult=None, fee=FEE):
    ds=[d for d in days if d in b.bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0}
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
            # Wider intraday disaster floor; normal stop requires previous close confirmation.
            if disaster_mult is not None:
                disaster=p['en']-disaster_mult*p['atr']
                # never place disaster stop tighter than 3.0% below entry
                disaster=min(disaster,p['en']*.97)
                if bar['l']<=disaster:
                    ex=bar['o'] if bar['o']<disaster else disaster;reason='DISASTER'
            if ex is None and a[i-1]['c']<=normal:
                ex=bar['o'];reason='CLOSESTOP'
            if ex is None:
                cp=a[i-1]['c'];un=cp/p['en']-1;ok,_,_=b.allowed(day)
                if not ok and p['age']>=2 and un<.015:ex=bar['o'];reason='REGIME'
                elif p['age']>=4 and un<-.007 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=CFG['trail_on'] and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
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
                px=b.bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(CFG['hard_atr']*atr,px*.012);q=int(min(cash/(max(1,slots)*px*(1+fee)),START*risk/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+fee);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=b.bi.bysym[s].get(day)
            if i is None:i=idx_at_or_before(s,day)
            eq+=p['q']*(b.bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        i=idx_at_or_before(s,last);px=b.bi.data[s][i]['c'] if i is not None else p['en'];pro=p['q']*px*(1-fee);cash+=pro;tr.append((pro-p['cost'],'SON'))
    gp=sum(x[0] for x in tr if x[0]>0);gl=-sum(x[0] for x in tr if x[0]<0);wins=sum(x[0]>0 for x in tr)
    reasons={}
    for _,r in tr:reasons[r]=reasons.get(r,0)+1
    return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*wins/len(tr) if tr else 0,'pf':gp/gl if gl else (99 if gp else 0),'reasons':reasons}

def summarize(rr):
    aa=[x for x in rr if x['n']]
    return {'avg':sum(x['ret'] for x in rr)/len(rr) if rr else 0,'worst':min((x['ret'] for x in rr),default=0),'pos':sum(x['ret']>0 for x in rr),'dd':sum(x['dd'] for x in rr)/len(rr) if rr else 0,'n':sum(x['n'] for x in rr),'pf':sum(min(5,x['pf']) for x in aa)/len(aa) if aa else 0}

folds=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)];wf_folds=folds[4:]
models=[('CLOSE_ONLY',None),('D1.8',1.8),('D2.2',2.2),('D2.6',2.6),('D3.0',3.0)]
rows=[]
for name,mult in models:
    rr=[run(ch,mult) for ch in wf_folds];s=summarize(rr);full=run(DATES,mult);rows.append({'name':name,'mult':mult,'full':full,'wf':s})
# Pick on robust criteria without cherry-picking a single fold: positive full, higher WF avg, low worst/DD.
# CLOSE_ONLY is benchmark; no parameter is deployed automatically.
windows=[]
for name,mult in models:
    for w in (15,22,30):
        for off in (0,5,10):
            ps=[DATES[i:i+w] for i in range(off,len(DATES)-w+1,w)];windows.append({'name':name,'w':w,'off':off,**summarize([run(ch,mult) for ch in ps])})
costs=[]
for name,mult in models:
    for fee in (.001,.0015,.002,.003):
        full=run(DATES,mult,fee);wf=summarize([run(ch,mult,fee) for ch in wf_folds]);costs.append({'name':name,'fee':fee,'full':full,'wf':wf})
lines=['# BR-SMART v23 Hybrid Disaster Stop','v20 girişleri sabit. Normal stop kapanış teyitli; yalnız daha geniş intraday felaket stopu değiştirildi. TUPRS/savunma hariç, maliyet dahil.','','## Fixed 22-day rolling OOS','|Model|Full Ret|Full DD|PF|N|WF Avg|Worst|Positive|WF DD|WF PF|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    f=r['full'];s=r['wf'];lines.append(f'|{r["name"]}|{f["ret"]:.2f}%|{f["dd"]:.2f}%|{f["pf"]:.2f}|{f["n"]}|{s["avg"]:.2f}%|{s["worst"]:.2f}%|{s["pos"]}/{len(wf_folds)}|{s["dd"]:.2f}%|{s["pf"]:.2f}|')
lines+=['','## Window sensitivity (averages)','|Model|W|Offset|Avg|Worst|Positive|DD|PF|','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in windows:lines.append(f'|{x["name"]}|{x["w"]}|{x["off"]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["pos"]}|{x["dd"]:.2f}%|{x["pf"]:.2f}|')
lines+=['','## Cost stress','|Model|Round-trip ~|Full Ret|DD|PF|WF Avg|Worst|WF PF|','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in costs:
    f=x['full'];s=x['wf'];lines.append(f'|{x["name"]}|{200*x["fee"]:.2f}%|{f["ret"]:.2f}%|{f["dd"]:.2f}%|{f["pf"]:.2f}|{s["avg"]:.2f}%|{s["worst"]:.2f}%|{s["pf"]:.2f}|')
Path('research/result_v23_hybrid_stop.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v23_hybrid_stop.json').write_text(json.dumps({'rows':rows,'windows':windows,'costs':costs},indent=2),encoding='utf-8');print('\n'.join(lines))
