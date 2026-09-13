import json, urllib.request, statistics
from pathlib import Path

US=['NVDA','AAPL','MSFT','GOOGL','AMZN','META','AMD','AVGO']
DE=['SAP.DE','S92.DE','NCH2.DE','SIE.DE','BMW.DE','MBG.DE','VOW3.DE','IFX.DE']
MARKETS={'ABD':US,'Almanya':DE}

def fetch(sym):
    last=None
    for host in ('query1.finance.yahoo.com','query2.finance.yahoo.com'):
        try:
            u=f'https://{host}/v8/finance/chart/{sym}?range=1y&interval=1d&events=div%2Csplits&includeAdjustedClose=true'
            req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 BorsaRadarResearch/1.0'})
            with urllib.request.urlopen(req,timeout=15) as r:j=json.load(r)
            rr=j['chart']['result'][0];q=rr['indicators']['quote'][0];out=[]
            for i,t in enumerate(rr['timestamp']):
                try:
                    o,h,l,c,v=q['open'][i],q['high'][i],q['low'][i],q['close'][i],q['volume'][i]
                    if None not in (o,h,l,c):out.append({'t':int(t),'o':float(o),'h':float(h),'l':float(l),'c':float(c),'v':float(v or 0)})
                except: pass
            return out
        except Exception as e:last=e
    raise last

def ema(x,p):
    k=2/(p+1);e=x[0]
    for v in x[1:]:e=v*k+e*(1-k)
    return e

def atr(a,p=14):
    if len(a)<2:return 0
    z=a[-min(p+1,len(a)):];v=[]
    for i in range(1,len(z)):
        q,c=z[i-1],z[i];v.append(max(c['h']-c['l'],abs(c['h']-q['c']),abs(c['l']-q['c'])))
    return sum(v)/len(v) if v else 0

def cmf(a,p=20):
    z=a[-min(p,len(a)):];x=y=0
    for c in z:
        d=c['h']-c['l'];m=0 if d==0 else ((c['c']-c['l'])-(c['h']-c['c']))/d;x+=m*c['v'];y+=c['v']
    return x/y if y else 0

def rsi(a,p=14):
    c=[x['c'] for x in a]
    if len(c)<=p:return 50
    d=[c[i]-c[i-1] for i in range(len(c)-p,len(c))];g=sum(max(x,0) for x in d)/p;l=sum(max(-x,0) for x in d)/p
    return 100 if l==0 else 100-100/(1+g/l)

def signal(a,i):
    if i<25:return False
    z=a[:i+1];c=[x['c'] for x in z];e20=ema(c[-80:],20);e8=ema(c[-40:],8);e12=ema(c[-50:],12)
    flow=cmf(z,20);a7=atr(z,7);a14=atr(z,14);comp=a7/a14 if a14 else 1
    hi=max(x['h'] for x in z[-20:]);prox=z[-1]['c']/hi if hi else 0
    av=sum(x['v'] for x in z[-11:-1])/10;rv=z[-1]['v']/av if av else 1
    m3=z[-1]['c']/z[-4]['c']-1;m8=z[-1]['c']/z[-9]['c']-1;acc=m3-m8*3/8
    stretch=z[-1]['c']/e20-1;rr=rsi(z,14)
    score=(2 if comp<.92 else 0)+(2 if prox>.965 else 0)+(2 if flow>0 else 0)+(2 if acc>0 else 0)+(1 if .8<=rv<=2.8 else 0)+(1 if e8>e12 and z[-1]['c']>e20 else 0)
    return score>=5 and stretch<=.085 and rr<78

def simulate(a,start,end,fee=.001):
    cash=1.0;shares=0.0;entry=0;high=0;hard=0;trail=0;age=0;pending=None;tr=[];peak=1;dd=0
    for i in range(start,end+1):
        b=a[i]
        if pending=='BUY' and shares==0:
            px=b['o'];shares=cash/(px*(1+fee));cash=0;entry=px;high=px;age=0;at=max(atr(a[:i+1]),px*.01);hard=px-1.6*at;trail=hard;pending=None
        elif pending=='SELL' and shares>0:
            px=b['o'];cash=shares*px*(1-fee);tr.append(px/entry-1-2*fee);shares=0;pending=None
        if shares>0:
            age+=1;high=max(high,b['h']);at=max(atr(a[:i+1]),entry*.01);gain=high/entry-1
            trail=max(trail,hard,high-2.6*at)
            if gain>=.05:trail=max(trail,entry*1.002)
            if gain>=.09:trail=max(trail,entry*1.035,high-2.1*at)
            if gain>=.14:trail=max(trail,entry*1.075,high-1.8*at)
            if b['l']<=trail or age>=15:pending='SELL'
        elif signal(a,i): pending='BUY'
        eq=cash+(shares*b['c'] if shares else 0);peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    if shares>0:
        px=a[end]['c'];cash=shares*px*(1-fee);tr.append(px/entry-1-2*fee)
    return {'ret':(cash-1)*100,'dd':dd*100,'n':len(tr),'win':100*sum(x>0 for x in tr)/len(tr) if tr else 0}

def rolling(a,win,step):
    rs=[]
    for end in range(win-1,len(a),step):
        start=end-win+1;r=simulate(a,start,end)
        if r['n']>0:rs.append(r)
    return rs

rows=[];detail=[]
for market,syms in MARKETS.items():
    all1=[];all3=[]
    for s in syms:
        try:a=fetch(s)
        except Exception as e:
            detail.append({'market':market,'symbol':s,'error':str(e)});continue
        r1=rolling(a,22,5);r3=rolling(a,66,11);all1+=r1;all3+=r3
        detail.append({'market':market,'symbol':s,'m1_n':len(r1),'m1_avg':sum(x['ret'] for x in r1)/len(r1) if r1 else 0,'m3_n':len(r3),'m3_avg':sum(x['ret'] for x in r3)/len(r3) if r3 else 0})
    for label,rs in [('1AY',all1),('3AY',all3)]:
        rows.append({'market':market,'period':label,'active':len(rs),'avg':sum(x['ret'] for x in rs)/len(rs) if rs else 0,'median':statistics.median([x['ret'] for x in rs]) if rs else 0,'worst':min((x['ret'] for x in rs),default=0),'best':max((x['ret'] for x in rs),default=0),'positive':sum(x['ret']>0 for x in rs),'avgdd':sum(x['dd'] for x in rs)/len(rs) if rs else 0})

lines=['# V41 ABD + Almanya manuel hisse 1AY/3AY testi','Bu test BIST V35 ile birebir ayni degildir. Manuel hisse moduna uygun, frozen EarlyBreak + ATR/trailing + ertesi acilis cikis mantigi kullanilir. Tarama/top-3 piyasa secimi yoktur.','','|Piyasa|Donem|Aktif pencere|Ort getiri|Medyan|En kotu|En iyi|Pozitif|Ort DD|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f"|{r['market']}|{r['period']}|{r['active']}|{r['avg']:.2f}%|{r['median']:.2f}%|{r['worst']:.2f}%|{r['best']:.2f}%|{r['positive']}/{r['active']}|{r['avgdd']:.2f}%|")
lines+=['','## Hisse bazinda ortalama']
for d in detail:
    if 'error' in d: lines.append(f"- {d['market']} {d['symbol']}: veri hatasi")
    else: lines.append(f"- {d['market']} {d['symbol']}: 1AY {d['m1_avg']:.2f}% ({d['m1_n']}), 3AY {d['m3_avg']:.2f}% ({d['m3_n']})")
Path('research/result_v41_us_de_manual_1m3m.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v41_us_de_manual_1m3m.json').write_text(json.dumps({'rows':rows,'detail':detail},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))