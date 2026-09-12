import json, math
from pathlib import Path
import backtest_indicators as bi
import v33_app_signal_backtest as v33

START=100000.0
FEE=bi.FEE
DATES=bi.dates
DPOS={d:i for i,d in enumerate(DATES)}
CFG={'breadth':.55,'look':40,'top':3,'hold':15,'cash':.25}
EXCLUDE={'TUPRS','ASELS','ALTNY'}


def state(day):
    i=DPOS.get(day,0); br=bi.breadth_cache.get(day,0)
    prev=[bi.breadth_cache.get(DATES[j],br) for j in range(max(0,i-3),i)]
    avg=sum(prev)/len(prev) if prev else br
    weak=(br<.44 or (br<.52 and br-avg<-.035))
    return br, weak

def regime(day,confirm=3):
    p=DPOS.get(day,0)
    if p<60:return False
    for k in range(confirm):
        d=DATES[p-k];br,weak=state(d)
        if br<CFG['breadth'] or weak:return False
    return True

def quality(s,i): return bi.quality(s,i)

def candidates(day):
    out=[]
    for s,a in bi.data.items():
        if s in EXCLUDE: continue
        i=bi.bysym[s].get(day)
        if i is None or i<65: continue
        turn,vol,j=quality(s,i)
        if turn<120_000_000 or vol<120_000 or j>=2: continue
        f=bi.feat(s,i); p1=a[i]['c']; p0=a[i-CFG['look']]['c']
        if p0<=0 or p1<=0: continue
        mom=p1/p0-1
        if mom<=0 or f['adx']<18 or f['cmf']<=0: continue
        if p1<=f['e20'] or p1>f['e20']*1.18: continue
        z=v33.pulse(a[:i+1])
        if not z: continue
        early=('ERKEN AL' in z['rec']) or ('KADEMELİ AL' in z['rec']) or z['rec']=='AL'
        if not early or z['conf']<68 or z['stretch']>8.5: continue
        # V30 structural rank + EarlyBreak timing bonus
        rank=(mom+0.002*f['adx'])*100 + z['early']*2.5 + z['score'] + max(0,z['conf']-68)*.15
        out.append((rank,s,i,z,f))
    out.sort(reverse=True)
    return out[:CFG['top']]

def run(days, close_confirm=True, profit_guard=True):
    ds=[d for d in days if d in bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0,'trades':[]}
    cash=START;pos={};pending={};tr=[];peak=START;maxdd=0;last=ds[-1]
    for day in ds:
        # execute pending next open
        for s,o in list(pending.items()):
            i=bi.bysym.get(s,{}).get(day)
            if i is None: continue
            px=bi.data[s][i]['o']
            if o['kind']=='BUY' and s not in pos and len(pos)<CFG['top']:
                slots=max(1,CFG['top']-len(pos)); alloc=min(cash*(1-CFG['cash'])/slots, START/CFG['top'])
                q=int(alloc/(px*(1+FEE)))
                if q>0:
                    cost=q*px*(1+FEE);cash-=cost
                    atr=max(bi.feat(s,i)['m']['atr'],px*.01)
                    pos[s]={'q':q,'en':px,'cost':cost,'age':0,'hi':px,'atr':atr,'hard':px-1.6*atr,'trail':px-1.6*atr,'entry_day':day}
            elif o['kind']=='SELL' and s in pos:
                p=pos.pop(s);pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];ret=100*pnl/p['cost']
                tr.append((s,p['entry_day'],day,p['en'],px,ret,o['reason']))
            del pending[s]

        on=regime(day)
        # position management on close; action next open except disaster gap handled same open only if already known impossible, so no same-day reaction
        for s,p in list(pos.items()):
            i=bi.bysym[s].get(day)
            if i is None: continue
            a=bi.data[s]; bar=a[i]; p['age']+=1; p['hi']=max(p['hi'],bar['h'])
            f=bi.feat(s,i); z=v33.pulse(a[:i+1]); gain=p['hi']/p['en']-1
            # adaptive trailing, but close-confirmed
            trail=max(p['hard'],p['hi']-2.6*p['atr'])
            if gain>=.05: trail=max(trail,p['en']*1.002)
            if gain>=.09: trail=max(trail,p['en']*1.035,p['hi']-2.1*p['atr'])
            if gain>=.14: trail=max(trail,p['en']*1.075,p['hi']-1.8*p['atr'])
            p['trail']=max(p['trail'],trail)
            reason=None
            if close_confirm and bar['c']<=p['trail']: reason='CLOSE-STOP'
            elif (not close_confirm) and bar['l']<=p['trail']: reason='INTRADAY-STOP'
            elif z and ('SAT' in z['rec'] or 'RİSK' in z['rec']) and bar['c']<f['e20']: reason='SAT/RİSK+EMA20'
            elif not on and p['age']>=3 and bar['c']<p['en']*1.02: reason='REJİM'
            elif profit_guard and gain>=.06 and z and z['score']<1.0: reason='KÂR-KORU'
            elif p['age']>=CFG['hold']: reason='15-GÜN'
            if reason and s not in pending: pending[s]={'kind':'SELL','reason':reason}

        # entries only in V30 bull regime
        if on:
            held=set(pos)|set(pending)
            slots=CFG['top']-len(pos)-sum(1 for x in pending.values() if x['kind']=='BUY')
            if slots>0:
                for _,s,i,z,f in candidates(day):
                    if slots<=0:break
                    if s in held:continue
                    pending[s]={'kind':'BUY','reason':z['rec']};slots-=1

        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day)
            eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)

    for s,p in list(pos.items()):
        i=bi.bysym[s].get(last)
        if i is None: continue
        px=bi.data[s][i]['c'];pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];ret=100*pnl/p['cost']
        tr.append((s,p['entry_day'],last,p['en'],px,ret,'DÖNEM SONU'))
    wins=sum(t[5]>0 for t in tr);gp=sum(max(0,t[5]) for t in tr);gl=-sum(min(0,t[5]) for t in tr)
    return {'ret':(cash/START-1)*100,'end':cash,'dd':maxdd*100,'n':len(tr),'win':100*wins/len(tr) if tr else 0,'pf':gp/gl if gl else (99 if gp else 0),'trades':tr}


def dt(t):
    import datetime
    return datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d')

chunks=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)]
variants=[('A close-stop+guard',True,True),('B close-stop',True,False),('C intraday-stop+guard',False,True)]
rows=[]
for name,cc,pg in variants:
    rr=[run(ch,cc,pg) for ch in chunks]
    full=run(DATES,cc,pg)
    rows.append({'name':name,'full':full,'folds':rr,'avg':sum(x['ret'] for x in rr)/len(rr),'worst':min(x['ret'] for x in rr),'pos':sum(x['ret']>0 for x in rr)})
best=max(rows,key=lambda x:(x['full']['ret']-.55*x['full']['dd']+.25*x['full']['pf'],x['avg']))

lines=['# v35 V30 + EarlyBreak Hybrid','V30 structural selection and bull regime are preserved as the stock-selection layer. EarlyBreak is used only for entry timing. Exits compare close-confirmed ATR/trailing and profit-guard variants. TUPRS + defense exclusions remain.','','|Variant|Full Ret|MaxDD|PF|Win|N|Fold Avg|Worst|Positive folds|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    f=r['full'];lines.append(f"|{r['name']}|{f['ret']:.2f}%|{f['dd']:.2f}%|{f['pf']:.2f}|{f['win']:.1f}%|{f['n']}|{r['avg']:.2f}%|{r['worst']:.2f}%|{r['pos']}/{len(r['folds'])}|")
lines+=['',f"Selected: **{best['name']}**",'', '## Best trades','|Stock|Entry|Exit|Buy|Sell|Net %|Reason|','|---|---|---|---:|---:|---:|---|']
for t in sorted(best['full']['trades'],key=lambda x:x[5],reverse=True)[:10]:lines.append(f'|{t[0]}|{dt(t[1])}|{dt(t[2])}|{t[3]:.2f}|{t[4]:.2f}|{t[5]:.2f}|{t[6]}|')
lines+=['','## Worst trades','|Stock|Entry|Exit|Buy|Sell|Net %|Reason|','|---|---|---|---:|---:|---:|---|']
for t in sorted(best['full']['trades'],key=lambda x:x[5])[:10]:lines.append(f'|{t[0]}|{dt(t[1])}|{dt(t[2])}|{t[3]:.2f}|{t[4]:.2f}|{t[5]:.2f}|{t[6]}|')
Path('research/result_v35_v30_earlybreak_hybrid.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_v35_v30_earlybreak_hybrid.json').write_text(json.dumps({'rows':rows,'best':best},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines))
