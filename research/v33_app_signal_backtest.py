import json, math
from datetime import datetime, timezone
from pathlib import Path
import backtest_indicators as bi

START=100000.0
FEE=0.001
MAX_POS=5
MIN_BARS=30
MAX_HOLD=10

# v3.7 ShortPulseEngine mantığını Python'da birebir yaklaştırır.
def ema(a,p):
    st=max(0,len(a)-p*3)
    z=a[st:]
    k=2.0/(p+1)
    e=z[0]['c']
    for q in z[1:]: e=q['c']*k+e*(1-k)
    return e

def rsi(a,p):
    if len(a)<=p:return 50.0
    g=l=0.0
    for i in range(len(a)-p,len(a)):
        d=a[i]['c']-a[i-1]['c']
        if d>=0:g+=d
        else:l-=d
    return 100.0 if l==0 else 100-100/(1+(g/p)/(l/p))

def roc(a,p):
    if len(a)<=p:return 0.0
    x=a[-1-p]['c']
    return 0.0 if x==0 else (a[-1]['c']/x-1)*100

def relvol(a,p):
    z=a[max(0,len(a)-1-p):len(a)-1]
    av=sum(x['v'] for x in z)/max(1,len(z))
    return 1.0 if av<=0 else a[-1]['v']/av

def atr(a,p):
    z=a[max(1,len(a)-p):]
    vals=[]
    for i in range(len(a)-len(z),len(a)):
        c=a[i];pr=a[i-1]
        vals.append(max(c['h']-c['l'],abs(c['h']-pr['c']),abs(c['l']-pr['c'])))
    return sum(vals)/max(1,len(vals))

def cmf(a,p):
    z=a[-min(p,len(a)):];mfv=v=0.0
    for c in z:
        den=c['h']-c['l'];m=0 if den==0 else ((c['c']-c['l'])-(c['h']-c['c']))/den
        mfv+=m*c['v'];v+=c['v']
    return 0 if v==0 else mfv/v

def efficiency(a,p):
    z=a[-min(p+1,len(a)):]
    path=sum(abs(z[i]['c']-z[i-1]['c']) for i in range(1,len(z)))
    return 0 if path==0 else (z[-1]['c']-z[0]['c'])/path

def vp(a,p):
    z=a[-min(p+1,len(a)):];sig=tot=0.0
    for i in range(1,len(z)):
        v=z[i]['v'];sig+=(1 if z[i]['c']>z[i-1]['c'] else -1 if z[i]['c']<z[i-1]['c'] else 0)*v;tot+=v
    return 0 if tot==0 else sig/tot

def high(a,p,exclude_last=True):
    z=a[:-1] if exclude_last else a
    z=z[-min(p,len(z)):]
    return max((x['h'] for x in z),default=a[-1]['c'])

def pulse(a):
    if len(a)<15:return None
    e3,e5,e8,e12,e20=[ema(a,p) for p in (3,5,8,12,20)]
    rr=rsi(a,7);r3=roc(a,3);r5=roc(a,5)
    prev=a[:-3]
    prev_r3=roc(prev,3) if len(prev)>=7 else 0
    accel=r3-prev_r3
    rv=relvol(a,10);a7=atr(a,7);a14=atr(a,14);ef=efficiency(a,10);vv=vp(a,10);cc=cmf(a,12)
    price=a[-1]['c'];h10=high(a,10);h20=high(a,20)
    breakout=price>h20
    near=h20>0 and not breakout and (h20-price)/h20<=.03
    stack=e3>e5 and e5>e8 and e8>=e12*.995
    compression=a14>0 and a7/a14<=.92
    flow=cc>.02 or vv>.06
    acceleration=accel>.35 and r3>-.5
    tight=e20>0 and price>=e20*.985 and price<=e20*1.085
    mini=h10>0 and price>h10 and not breakout
    last=a[-1];rng=max(1e-9,last['h']-last['l']);uw=last['h']-max(last['o'],last['c'])
    stretch=0 if e20==0 else (price/e20-1)*100
    stretched=stretch>10.5 or rr>77
    trap=(uw/rng>.58 and rv>1.35) or (rr>80 and breakout)
    early=0.0
    if near:early+=1.25
    if mini:early+=.75
    if stack:early+=1.0
    if compression:early+=.9
    if flow:early+=.9
    if acceleration:early+=.9
    if 1.05<=rv<=2.4:early+=.65
    if tight:early+=.65
    if stretched:early-=1.6
    if trap:early-=2.0
    earlybreak=(not breakout and early>=4.0)
    s=0.0
    s += .7 if e3>e5 else -.7
    s += .9 if e5>e8 else -.9
    s += .7 if e8>e12 else -.7
    if 48<=rr<=68:s+=.8
    elif rr>76:s-=1.3
    elif rr<34:s-=.6
    if r3>.4:s+=.55
    elif r3<-1.5:s-=.7
    if r5>.8:s+=.65
    elif r5<-2:s-=.9
    if rv>1.05:s+=.65
    elif rv<.65:s-=.4
    if cc>.04:s+=.75
    elif cc<-.08:s-=.8
    if vv>.06:s+=.65
    elif vv<-.10:s-=.7
    if ef>.22:s+=.55
    elif ef<-.25:s-=.7
    if breakout and not stretched:s+=.45
    if earlybreak:s+=1.35
    elif near:s+=.55
    if acceleration:s+=.45
    if stretched:s-=1.45
    if trap:s-=2.2
    if trap or (breakout and stretched):rec='KOVALAMA / BEKLE'
    elif earlybreak and s>=3:rec='ERKEN AL / KIRILIM ÖNCESİ'
    elif s>=4.8 and not stretched:rec='AL'
    elif s>=2.7:rec='KADEMELİ AL / İZLE'
    elif s<=-2.8:rec='SAT / RİSKİ AZALT'
    elif s<=-1.3:rec='ZAYIF / BEKLE'
    else:rec='TUT / NÖTR'
    conf=max(30,min(92,46+abs(s)*5.4+max(0,early)*3+(3 if rv>1.05 else 0)-(7 if stretched else 0)-(12 if trap else 0)))
    stop=max(0,price-1.8*a7)
    return {'rec':rec,'score':s,'conf':conf,'stop':stop,'early':early,'price':price,'rv':rv,'stretch':stretch}

def dt(t): return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')

def run():
    dates=bi.dates
    cash=START;pos={};trades=[];peak=START;maxdd=0.0;pending={}
    for day in dates:
        # Önce bir önceki kapanışta üretilen emirleri bugünkü açılışta uygula.
        for s,side in list(pending.items()):
            i=bi.bysym.get(s,{}).get(day)
            if i is None: continue
            bar=bi.data[s][i]
            if side['kind']=='BUY' and s not in pos and len(pos)<MAX_POS:
                slots=max(1,MAX_POS-len(pos));alloc=min(cash/slots,START/MAX_POS)
                q=int(alloc/(bar['o']*(1+FEE)))
                if q>0:
                    cost=q*bar['o']*(1+FEE);cash-=cost
                    pos[s]={'q':q,'en':bar['o'],'entry_day':day,'age':0,'cost':cost,'peak':bar['o']}
            elif side['kind']=='SELL' and s in pos:
                p=pos.pop(s);pro=p['q']*bar['o']*(1-FEE);cash+=pro
                pnl=pro-p['cost'];ret=100*pnl/p['cost']
                trades.append((s,p['entry_day'],day,p['en'],bar['o'],ret,side['reason']))
            del pending[s]

        # Gün sonu mark-to-market ve sinyal üretimi.
        candidates=[]
        for s,a in bi.data.items():
            i=bi.bysym[s].get(day)
            if i is None or i<MIN_BARS: continue
            hist=a[:i+1]
            z=pulse(hist)
            if z is None: continue
            if s in pos:
                p=pos[s];p['age']+=1;p['peak']=max(p['peak'],a[i]['h'])
                stop_hit=z['price']<=z['stop']
                risk=('SAT' in z['rec'] or 'RİSK' in z['rec'])
                if stop_hit: pending[s]={'kind':'SELL','reason':'STOP-REF'}
                elif risk: pending[s]={'kind':'SELL','reason':'SAT/RİSK'}
                elif p['age']>=MAX_HOLD: pending[s]={'kind':'SELL','reason':'10-GÜN'}
            else:
                good=(('ERKEN AL' in z['rec']) or z['rec']=='AL' or ('KADEMELİ AL' in z['rec'])) and z['conf']>=72
                if good:
                    # Likidite filtresi: son 20 gün ortalama ciro > 120m TL, hacim >120k
                    w=a[max(0,i-19):i+1];turn=sum(x['c']*x['v'] for x in w)/len(w);vol=sum(x['v'] for x in w)/len(w)
                    if turn>=120_000_000 and vol>=120_000:
                        candidates.append((z['conf']+3*z['early']+z['score'],s,z))
        candidates.sort(reverse=True)
        slots=MAX_POS-len(pos)-sum(1 for x in pending.values() if x['kind']=='BUY')
        for _,s,z in candidates:
            if slots<=0:break
            if s in pending or s in pos:continue
            pending[s]={'kind':'BUY','reason':z['rec']};slots-=1

        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day)
            eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)

    last=dates[-1]
    for s,p in list(pos.items()):
        i=max((i for t,i in bi.bysym[s].items() if t<=last),default=None)
        if i is None:continue
        px=bi.data[s][i]['c'];pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];ret=100*pnl/p['cost']
        trades.append((s,p['entry_day'],last,p['en'],px,ret,'DÖNEM SONU'))
    wins=sum(1 for t in trades if t[5]>0);gp=sum(max(0,t[5]) for t in trades);gl=-sum(min(0,t[5]) for t in trades)
    pf=gp/gl if gl else (99 if gp else 0)
    rets=[t[5] for t in trades]
    best=sorted(trades,key=lambda x:x[5],reverse=True)[:10]
    worst=sorted(trades,key=lambda x:x[5])[:10]
    out={'start':START,'end':cash,'ret':(cash/START-1)*100,'dd':maxdd*100,'n':len(trades),'win':100*wins/len(trades) if trades else 0,'pf':pf,'from':dt(dates[0]),'to':dt(dates[-1]),'best':best,'worst':worst,'details':trades}
    lines=['# BorsaRadar v3.7 App Sinyali Geriye Dönük AL/SAT Testi',f"Dönem: **{out['from']} → {out['to']}** | Başlangıç: **100.000 TL** | Max 5 pozisyon | Tek yön maliyet **%0,10**",'Sinyal kapanışta hesaplanır, işlem **ertesi seans açılışında** yapılır. Bu yüzden lookahead yoktur. TUPRS + savunma hisseleri hariçtir.','',f"Son portföy: **{out['end']:.2f} TL** | Getiri **%{out['ret']:.2f}** | MaxDD **%{out['dd']:.2f}** | İşlem **{out['n']}** | Kazanma **%{out['win']:.1f}** | PF **{out['pf']:.2f}**",'', '## En iyi işlemler','|Hisse|Giriş|Çıkış|Giriş|Çıkış|Net %|Neden|','|---|---|---|---:|---:|---:|---|']
    for t in best:lines.append(f'|{t[0]}|{dt(t[1])}|{dt(t[2])}|{t[3]:.2f}|{t[4]:.2f}|{t[5]:.2f}|{t[6]}|')
    lines+=['','## En kötü işlemler','|Hisse|Giriş|Çıkış|Giriş|Çıkış|Net %|Neden|','|---|---|---|---:|---:|---:|---|']
    for t in worst:lines.append(f'|{t[0]}|{dt(t[1])}|{dt(t[2])}|{t[3]:.2f}|{t[4]:.2f}|{t[5]:.2f}|{t[6]}|')
    Path('research/result_v33_app_signal.md').write_text('\n'.join(lines),encoding='utf-8')
    Path('research/result_v33_app_signal.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('\n'.join(lines),flush=True)

if __name__=='__main__': run()
