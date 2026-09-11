import json, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import backtest_month as b

START=100000.; FEE=.001
WINDOWS=[(0,31),(31,62),(62,93),(93,124)]
EXCLUDE={'ASELS','ALTNY','TUPRS'}

data={};fails=[]
syms=[s for s in b.SYMS if s not in EXCLUDE]
with ThreadPoolExecutor(max_workers=12) as ex:
    fut={ex.submit(b.fetch,s):s for s in syms}
    for i,f in enumerate(as_completed(fut),1):
        s=fut[f]
        try:
            a=f.result()
            if len(a)>=100:data[s]=a
            else:fails.append(s)
        except Exception:fails.append(s)
        if i%100==0:print('FETCH',i,'OK',len(data),'FAIL',len(fails),flush=True)

bysym={s:{r['t']:i for i,r in enumerate(a)} for s,a in data.items()};dates=sorted(set(r['t'] for a in data.values() for r in a));END=max(dates)
mc={};fc={};qc={}
def M(s,i):
    k=(s,i)
    if k not in mc:mc[k]=b.method(data[s][:i])
    return mc[k]
def quality(s,i):
    k=(s,i)
    if k in qc:return qc[k]
    z=data[s][max(0,i-20):i];turn=sum(x['c']*x['v'] for x in z)/max(1,len(z));vol=sum(x['v'] for x in z)/max(1,len(z));j=sum(abs(data[s][q]['c']/data[s][q-1]['c']-1)>=.075 for q in range(max(1,i-10),i));qc[k]=(turn,vol,j);return qc[k]
def feat(s,i):
    k=(s,i)
    if k in fc:return fc[k]
    a=data[s];m=M(s,i);m2=M(s,i-2);c=[x['c'] for x in a[:i]]
    e5=b.ema(c[-30:],5);e10=b.ema(c[-50:],10);e20=b.ema(c[-80:],20);e50=b.ema(c[-120:],50)
    cp=[x['c'] for x in a[:max(1,i-3)]];e20p=b.ema(cp[-80:],20);slope=e20/e20p-1 if e20p else 0
    z=a[max(0,i-20):i];cm=b.cmf(z,20);vv=a[max(0,i-21):i-1];av=sum(x['v'] for x in vv)/max(1,len(vv));rv=a[i-1]['v']/av if av else 1
    rsi=b.rsi(c,14);st=b.stoch(a[:i],14);cci=b.cci(a[:i],20);adx=b.adx(a[:i],14)
    mom3=a[i-1]['c']/a[i-4]['c']-1;mom8=a[i-1]['c']/a[i-9]['c']-1;acc=mom3-mom8*3/8
    f={'m':m,'imp':m['pct']-m2['pct'],'e5':e5,'e10':e10,'e20':e20,'e50':e50,'slope':slope,'cmf':cm,'rv':rv,'rsi':rsi,'stoch':st,'cci':cci,'adx':adx,'acc':acc,'mom3':mom3}
    fc[k]=f;return f

def breadth(day):
    good=up=0
    for s,a in data.items():
        i=bysym[s].get(day)
        if i is None or i<55:continue
        turn,vol,j=quality(s,i)
        if turn<100_000_000:continue
        f=feat(s,i);good+=1;up+=a[i-1]['c']>f['e20'] and f['slope']>0
    return up/good if good else 0
breadth_cache={d:breadth(d) for d in dates}

def market_regime(day):
    br=breadth_cache.get(day,0)
    if br>=.55:return 'BULL'
    if br<=.35:return 'BEAR'
    return 'SIDE'

# Indicator families. Each family must earn its place via ablation.
FAMILIES={
 'TREND':lambda f: f['e5']>f['e10']>f['e20'] and f['slope']>0 and f['e20']>f['e50'],
 'MOMENTUM':lambda f: f['imp']>=2 and f['acc']>-.004 and 48<=f['rsi']<=72,
 'FLOW':lambda f: f['cmf']>=0 and f['rv']>=.9 and f['m']['vp']>.02,
 'STRENGTH':lambda f: f['adx']>=16 and f['cci']>-50 and f['stoch']<96,
 'BASE':lambda f: f['m']['pct']>=72 and not f['m']['trap'],
}

def passes(f, enabled, regime):
    if not FAMILIES['BASE'](f):return False
    # Regime-aware: bear requires stricter trend/flow, bull can be a bit more permissive.
    if regime=='BEAR':
        if f['m']['pct']<78 or f['rv']<1.05 or f['cmf']<.03:return False
    elif regime=='SIDE':
        if f['m']['pct']<74:return False
    for name in enabled:
        if name!='BASE' and not FAMILIES[name](f):return False
    return True

def simulate(enabled,w):
    off0,off1=w;we=END-off0*86400;ws=END-off1*86400;cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in dates:
        if day<ws or day>we:continue
        reg=market_regime(day)
        for s in list(pos):
            i=bysym[s].get(day)
            if i is None:continue
            bar=data[s][i];p=pos[s];p['hi']=max(p['hi'],bar['h']);gain=p['hi']/p['en']-1;f=feat(s,i);m=f['m']
            trail=.955 if reg=='BULL' else .965 if reg=='SIDE' else .975
            stop=max(p['hard'],p['hi']*trail,p['hi']-2.0*m['atr'])
            if gain>=.04:stop=max(stop,p['en']*1.006)
            if gain>=.08:stop=max(stop,p['hi']*.965,p['en']*1.03)
            xp=reason=None
            if bar['l']<=stop:xp=bar['o'] if bar['o']<stop else stop;reason='STOP'
            elif m['pct']<48 or f['imp']<-5 or (reg=='BEAR' and f['cmf']<0):xp=bar['o'];reason='ZAYIF'
            if xp:
                cash+=p['q']*xp*(1-FEE);tr.append((s,p['day'],day,(xp/p['en']-1)*100-.2,reason,reg));del pos[s];cool[s]=day
        maxpos=5 if reg=='BULL' else 3 if reg=='SIDE' else 1
        slots=maxpos-len(pos)
        if slots>0:
            ca=[]
            for s,a in data.items():
                if s in pos:continue
                i=bysym[s].get(day)
                if i is None or i<57 or (s in cool and day-cool[s]<3*86400):continue
                turn,vol,j=quality(s,i)
                if turn<100_000_000 or vol<100_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.05<=gap<=.025):continue
                f=feat(s,i)
                if passes(f,enabled,reg):
                    rank=f['m']['pct']+2*f['imp']+min(5,(f['rv']-1)*4)+min(5,f['cmf']*20)+min(4,f['adx']/10);ca.append((rank,s,i,f))
            ca.sort(reverse=True)
            for rank,s,i,f in ca[:slots]:
                px=data[s][i]['o'];sd=max(.018,min(.032,1.8*f['m']['atr']/px));risk=.005 if reg!='BEAR' else .0025;rc=START*risk;q1=math.floor(rc/max(.01,px*sd));cap=min(cash/max(1,slots),START/maxpos);q2=math.floor(cap/(px*(1+FEE)));q=max(0,min(q1,q2))
                if q:cash-=q*px*(1+FEE);pos[s]={'q':q,'en':px,'day':day,'hi':px,'hard':px*(1-sd)};slots-=1
                if slots<=0:break
        eq=cash
        for s,p in pos.items():
            i=bysym[s].get(day);eq+=p['q']*(data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        cand=[x for x in data[s] if x['t']<=we]
        if not cand:continue
        x=cand[-1];cash+=p['q']*x['c']*(1-FEE);tr.append((s,p['day'],x['t'],(x['c']/p['en']-1)*100-.2,'SON',market_regime(x['t'])))
    win=sum(x[3]>0 for x in tr);gw=sum(max(0,x[3]) for x in tr);gl=-sum(min(0,x[3]) for x in tr)
    return {'ret':(cash/START-1)*100,'end':cash,'dd':dd*100,'n':len(tr),'win':100*win/len(tr) if tr else 0,'pf':gw/gl if gl else (99 if gw else 0),'details':tr}

sets=[('BASE',[]),('TREND',['TREND']),('MOMENTUM',['MOMENTUM']),('FLOW',['FLOW']),('STRENGTH',['STRENGTH']),('TREND+FLOW',['TREND','FLOW']),('TREND+MOM',['TREND','MOMENTUM']),('MOM+FLOW',['MOMENTUM','FLOW']),('ALL',['TREND','MOMENTUM','FLOW','STRENGTH'])]
rows=[]
for name,en in sets:
    rs=[simulate(en,w) for w in WINDOWS];rets=[r['ret'] for r in rs];dds=[r['dd'] for r in rs];ns=[r['n'] for r in rs];pfs=[r['pf'] for r in rs];active=[r for r in rs if r['n']>0]
    avg=sum(rets)/4;worst=min(rets);avgdd=sum(dds)/4;n=sum(ns);pos=sum(x>0 for x in rets);pf=sum(min(3,r['pf']) for r in active)/len(active) if active else 0
    score=avg+.5*worst-.5*avgdd+.4*(pf-1)+.15*pos+min(.5,n/60)
    rows.append({'name':name,'enabled':en,'rs':rs,'avg':avg,'worst':worst,'avgdd':avgdd,'n':n,'pos':pos,'pf':pf,'score':score})
rows.sort(key=lambda x:x['score'],reverse=True);best=rows[0]
lines=['# BorsaRadar İndikatör Ablation + Rejim Testi',f'Evren {len(syms)}, veri {len(data)}, 4 x 31 gün. TUPRS ve savunma hisseleri hariç. Lookahead yok, tek yön maliyet %0.10.','', '## Sonuç','|Model|Ort Getiri|En Kötü|Ort DD|İşlem|Pozitif Dönem|PF|','|---|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'|{r["name"]}|{r["avg"]:.2f}%|{r["worst"]:.2f}%|{r["avgdd"]:.2f}%|{r["n"]}|{r["pos"]}/4|{r["pf"]:.2f}|')
lines+=['',f'**En iyi model: {best["name"]}**','', '## En iyi model dönemleri','|Dönem|Getiri|DD|N|Win|PF|','|---|---:|---:|---:|---:|---:|']
for i,r in enumerate(best['rs'],1):lines.append(f'|{i}|{r["ret"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["win"]:.1f}%|{r["pf"]:.2f}|')
Path('research/result_indicators.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_indicators.json').write_text(json.dumps({'best':best,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines),flush=True)
