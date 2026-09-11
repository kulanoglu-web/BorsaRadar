import json, math, re, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

START_CASH=100000.0
MAX_POS=5
FEE=0.001
HORIZON_DAYS=31

JAVA=Path('app/src/main/java/com/kulanoglu/borsaradar/BistUniverse.java').read_text(encoding='utf-8')
SYMS=[]
for m in re.finditer(r'"([A-Z0-9]{2,8})\s+•', JAVA):
    s=m.group(1)
    if s not in SYMS and s not in {'ASELS','ALTNY'}:
        SYMS.append(s)

def fetch(sym):
    last=None
    for host in ('query1.finance.yahoo.com','query2.finance.yahoo.com'):
        try:
            url=f'https://{host}/v8/finance/chart/{sym}.IS?range=1y&interval=1d&events=div%2Csplits&includeAdjustedClose=true'
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 BorsaRadarResearch/1.0','Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=15) as r: j=json.load(r)
            rr=j['chart']['result'][0]; ts=rr['timestamp']; q=rr['indicators']['quote'][0]; out=[]
            for i,t in enumerate(ts):
                try:
                    o,h,l,c,v=q['open'][i],q['high'][i],q['low'][i],q['close'][i],q['volume'][i]
                    if None in (o,h,l,c): continue
                    out.append({'t':int(t),'o':float(o),'h':float(h),'l':float(l),'c':float(c),'v':float(v or 0)})
                except Exception: pass
            return out
        except Exception as e: last=e
    raise last or RuntimeError('fetch failed')

def ema(a,p):
    k=2/(p+1); e=a[0]
    for x in a[1:]: e=x*k+e*(1-k)
    return e

def rsi(c,p=14):
    if len(c)<=p:return 50
    d=[c[i]-c[i-1] for i in range(len(c)-p,len(c))]; g=sum(max(x,0) for x in d)/p; l=sum(max(-x,0) for x in d)/p
    return 100 if l==0 else 100-100/(1+g/l)

def atr(x,p=14):
    if len(x)<2:return 0
    z=x[-min(p,len(x)-1):]; prev=x[len(x)-len(z)-1]['c']; vals=[]
    for c in z: vals.append(max(c['h']-c['l'],abs(c['h']-prev),abs(c['l']-prev))); prev=c['c']
    return sum(vals)/len(vals)

def cmf(x,p=20):
    z=x[-min(p,len(x)):]; a=b=0
    for c in z:
        den=c['h']-c['l']; m=0 if den==0 else ((c['c']-c['l'])-(c['h']-c['c']))/den; a+=m*c['v']; b+=c['v']
    return 0 if b==0 else a/b

def stoch(x,p=14):
    z=x[-min(p,len(x)):]; hi=max(c['h'] for c in z); lo=min(c['l'] for c in z); return 50 if hi==lo else 100*(z[-1]['c']-lo)/(hi-lo)

def cci(x,p=20):
    z=x[-min(p,len(x)):]; tp=[(c['h']+c['l']+c['c'])/3 for c in z]; m=sum(tp)/len(tp); d=sum(abs(t-m) for t in tp)/len(tp); return 0 if d==0 else (tp[-1]-m)/(0.015*d)

def adx(x,p=14):
    if len(x)<3:return 0
    z=x[-min(p+1,len(x)):]; tr=plus=minus=0
    for i in range(1,len(z)):
        c,q=z[i],z[i-1]; tr+=max(c['h']-c['l'],abs(c['h']-q['c']),abs(c['l']-q['c'])); up=c['h']-q['h']; dn=q['l']-c['l']
        if up>dn and up>0: plus+=up
        if dn>up and dn>0: minus+=dn
    if tr==0:return 0
    pdi=100*plus/tr; mdi=100*minus/tr; return 0 if pdi+mdi==0 else 100*abs(pdi-mdi)/(pdi+mdi)

def method(x):
    c=[r['c'] for r in x]; n=len(x); close=c[-1]
    e20=ema(c[-min(len(c),80):],20); e50=ema(c[-min(len(c),120):],50); e12=ema(c[-min(len(c),48):],12); e26=ema(c[-min(len(c),104):],26); mac=e12-e26
    macs=[]
    for k in range(max(26,n-9),n+1):
        cc=[r['c'] for r in x[:k]]
        if len(cc)>=26: macs.append(ema(cc[-48:],12)-ema(cc[-104:],26))
    ms=ema(macs,9) if macs else mac
    a=atr(x); rr=rsi(c); m=cmf(x); prevvol=x[-21:-1]; av=sum(q['v'] for q in prevvol)/max(1,len(prevvol)); rv=x[-1]['v']/av if av>0 else 1
    st=stoch(x); ax=adx(x); z=x[-min(21,n):]; path=sum(abs(z[i]['c']-z[i-1]['c']) for i in range(1,len(z))); eff=0 if path==0 else (z[-1]['c']-z[0]['c'])/path; mom=0 if a<=0 else (z[-1]['c']-z[0]['c'])/(a*math.sqrt(max(1,len(z)-1)))
    vv=x[-min(20,n):]; signed=sum((1 if vv[i]['c']>vv[i-1]['c'] else -1 if vv[i]['c']<vv[i-1]['c'] else 0)*vv[i]['v'] for i in range(1,len(vv))); total=sum(q['v'] for q in vv[1:]); vp=0 if total==0 else signed/total
    prev=x[-21:-1] if len(x)>=21 else x[:-1]; hh=max([q['h'] for q in prev],default=close); br=close>hh; pre=(not br and hh>0 and 0<=(hh-close)/hh<=.025 and rv>=1)
    last=x[-1]; rng=max(1e-6,last['h']-last['l']); uw=last['h']-max(last['o'],last['c']); trap=(uw/rng>.55 and rv>1.4) or (rr>78 and br); trend=close>e20>e50
    pulse=max(0,min(100,50+max(-1,min(1,eff))*22+max(-1,min(1,mom/2.5))*17+max(-1,min(1,vp))*11))
    flow=max(0,min(100,50+max(-1,min(1,m/.25))*16+max(-1,min(1,(rv-1)/1.3))*12+(14 if br else 8 if pre else 0)-(26 if trap else 0)))
    guard=max(0,min(100,50+(15 if trend else -15 if close<e50 else 0)+(10 if mac>ms else -8)+(8 if ax>=20 and trend else 0)+(8 if 48<=rr<=69 else -10 if rr>76 else 0)+(-7 if st>94 else 0)))
    pct=.42*pulse+.33*flow+.25*guard
    if trap:pct=min(pct,44)
    return {'pct':max(5,min(95,pct)),'atr':a,'trap':trap,'trend':trend,'vp':vp,'mac':mac,'ms':ms}

def simulate(data, base_stop, trail_pct):
    dates=sorted(set(r['t'] for arr in data.values() for r in arr)); end=max(dates); start=end-HORIZON_DAYS*86400; cash=START_CASH; pos={}; trades=[]; peak=START_CASH; maxdd=0; bysym={s:{r['t']:i for i,r in enumerate(a)} for s,a in data.items()}
    for day in dates:
        if day<start: continue
        for s in list(pos):
            a=data[s]; idx=bysym[s].get(day)
            if idx is None: continue
            bar=a[idx]; p=pos[s]; p['high']=max(p['high'],bar['h']); gain=p['high']/p['entry']-1; atr_now=method(a[:idx])['atr'] if idx>=30 else p['atr']; stop=max(p['hard'],p['high']*(1-trail_pct),p['high']-2.2*atr_now)
            if gain>=.06: stop=max(stop,p['entry']*1.012)
            if gain>=.12: stop=max(stop,p['high']*.945,p['entry']*1.06)
            exit_price=reason=None
            if bar['l']<=stop: exit_price=min(bar['o'],stop) if bar['o']<stop else stop; reason='STOP/KAR-KORU'
            elif idx>=31:
                m=method(a[:idx])
                if m['pct']<42 or (gain>.04 and (m['vp']<-.08 or m['mac']<m['ms'])): exit_price=bar['o']; reason='METOD-ZAYIFLADI'
            if exit_price:
                cash+=p['qty']*exit_price*(1-FEE); ret=(exit_price/p['entry']-1)*100-2*FEE*100; trades.append((s,p['entry_day'],day,p['entry'],exit_price,ret,reason)); del pos[s]
        slots=MAX_POS-len(pos)
        if slots>0:
            cand=[]
            for s,a in data.items():
                if s in pos: continue
                idx=bysym[s].get(day)
                if idx is None or idx<55: continue
                m=method(a[:idx])
                if m['pct']>=68 and not m['trap'] and m['trend']: cand.append((m['pct'],s,idx,m))
            cand.sort(reverse=True)
            for pct,s,idx,m in cand[:slots]:
                price=data[s][idx]['o']; allocation=min(cash/max(1,slots),START_CASH/MAX_POS); qty=math.floor(allocation/(price*(1+FEE)))
                if qty<=0: continue
                cash-=qty*price*(1+FEE); pos[s]={'qty':qty,'entry':price,'entry_day':day,'high':price,'atr':m['atr'],'hard':price*(1-base_stop)}; slots-=1
                if slots<=0: break
        equity=cash+sum(p['qty']*(data[s][bysym[s][day]]['c'] if day in bysym[s] else p['entry']) for s,p in pos.items()); peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    for s,p in list(pos.items()):
        bar=data[s][-1]; cash+=p['qty']*bar['c']*(1-FEE); ret=(bar['c']/p['entry']-1)*100-2*FEE*100; trades.append((s,p['entry_day'],bar['t'],p['entry'],bar['c'],ret,'DONEM-SONU'))
    wins=sum(t[5]>0 for t in trades); return {'stop':base_stop,'trail':trail_pct,'end':cash,'ret':(cash/START_CASH-1)*100,'maxdd':maxdd*100,'trades':len(trades),'winrate':100*wins/len(trades) if trades else 0,'details':trades}

def main():
    data={}; fails=[]
    with ThreadPoolExecutor(max_workers=12) as ex:
        fut={ex.submit(fetch,s):s for s in SYMS}
        for i,f in enumerate(as_completed(fut),1):
            s=fut[f]
            try:
                a=f.result(); data[s]=a if len(a)>=70 else data.get(s)
                if len(a)<70: fails.append((s,'short'))
            except Exception as e: fails.append((s,str(e)[:80]))
            if i%50==0: print('FETCH',i,'OK',len(data),'FAIL',len(fails),flush=True)
    data={k:v for k,v in data.items() if v}
    print('UNIVERSE',len(SYMS),'DATA_OK',len(data),'FAIL',len(fails),flush=True)
    results=[simulate(data,bs,tr) for bs in (.025,.035,.045) for tr in (.04,.06,.08)]; results.sort(key=lambda r:(r['ret']-.45*r['maxdd'],r['ret']),reverse=True); best=results[0]
    def dt(t): return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
    report=['# BorsaRadar 1 Aylık Geniş BIST Backtest',f'Evren: {len(SYMS)} | veri alınan: {len(data)} | başlangıç: {START_CASH:.0f} TL | max pozisyon: {MAX_POS}','Savunma hisseleri varsayılan olarak hariç. Sinyal dünkü kapanış verisiyle, işlem ertesi seans açılış/stop fiyatıyla yapılır. Tek yön maliyet %0.10.','\n## Parametre karşılaştırması','| İlk stop | Trailing | Son TL | Getiri % | MaxDD % | İşlem | Kazanma % |','|---:|---:|---:|---:|---:|---:|---:|']
    for r in results: report.append(f"| {r['stop']*100:.1f} | {r['trail']*100:.1f} | {r['end']:.2f} | {r['ret']:.2f} | {r['maxdd']:.2f} | {r['trades']} | {r['winrate']:.1f} |")
    report += [f"\n## Seçilen denge\nİlk stop %{best['stop']*100:.1f}, trailing %{best['trail']*100:.1f}; **{best['end']:.2f} TL**, getiri **%{best['ret']:.2f}**, MaxDD **%{best['maxdd']:.2f}**, kazanma **%{best['winrate']:.1f}**.",'\n## İşlemler','| Hisse | Giriş | Çıkış | Giriş fiyatı | Çıkış fiyatı | Net % | Neden |','|---|---|---|---:|---:|---:|---|']
    for t in best['details']: report.append(f'| {t[0]} | {dt(t[1])} | {dt(t[2])} | {t[3]:.2f} | {t[4]:.2f} | {t[5]:.2f} | {t[6]} |')
    Path('research/result_month.md').write_text('\n'.join(report),encoding='utf-8'); Path('research/result_month.json').write_text(json.dumps({'best':best,'all':results,'data_ok':len(data),'fails':fails},ensure_ascii=False,indent=2),encoding='utf-8'); print('\n'.join(report),flush=True)
if __name__=='__main__': main()
