import json, math
from pathlib import Path
import backtest_regime_v2 as r
import backtest_indicators as bi

# Test entry timing: relative strength, 2-day persistence, exhaustion and volume sustainability.
# Reuses the already fetched universe and no-lookahead regime simulator inputs.
START=bi.START; FEE=bi.FEE

def extra(s,i):
    a=bi.data[s]
    if i<25:return None
    c=[x['c'] for x in a]
    ret3=c[i-1]/c[i-4]-1; ret10=c[i-1]/c[i-11]-1
    # cross-sectional market median approximated by breadth regime: demand stronger stock return in weak regimes
    r1=c[i-1]/c[i-2]-1; r2=c[i-2]/c[i-3]-1
    f=bi.feat(s,i); atr=max(f['m']['atr'],.0001)
    ext=(c[i-1]-f['e20'])/atr
    upper=(a[i-1]['h']-max(a[i-1]['o'],a[i-1]['c']))/max(.0001,a[i-1]['h']-a[i-1]['l'])
    av5=sum(x['v'] for x in a[i-5:i])/5; av20=sum(x['v'] for x in a[i-20:i])/20
    volpersist=av5/av20 if av20 else 1
    persist=(r1>-.012 and r2>-.018 and (r1>0 or r2>0))
    return ret3,ret10,ext,upper,volpersist,persist

def simulate(cfg,w):
    bull,side,tb,ts,rb,rs,mb,ms,rel3,extmax,vpmin,confirm=cfg
    off0,off1=w;we=bi.END-off0*86400;ws=bi.END-off1*86400
    cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in bi.dates:
        if day<ws or day>we:continue
        reg=r.regime(day,bull,side)
        for s in list(pos):
            i=bi.bysym[s].get(day)
            if i is None:continue
            bar=bi.data[s][i];p=pos[s];p['hi']=max(p['hi'],bar['h']);f=bi.feat(s,i);gain=p['hi']/p['en']-1
            trail=.955 if reg=='BULL' else .965 if reg=='SIDE' else .98
            stop=max(p['hard'],p['hi']*trail,p['hi']-2*f['m']['atr'])
            if gain>=.04:stop=max(stop,p['en']*1.006)
            if gain>=.08:stop=max(stop,p['hi']*.965,p['en']*1.03)
            xp=None;why=None
            if bar['l']<=stop:xp=bar['o'] if bar['o']<stop else stop;why='STOP'
            elif reg=='RISKOFF':xp=bar['o'];why='RISKOFF'
            elif f['m']['pct']<50 or f['imp']<-4 or (gain>.03 and f['cmf']<0):xp=bar['o'];why='ZAYIF'
            if xp:cash+=p['q']*xp*(1-FEE);tr.append((s,(xp/p['en']-1)*100-.2,why));del pos[s];cool[s]=day
        if reg=='RISKOFF':continue
        maxp=mb if reg=='BULL' else ms;slots=maxp-len(pos)
        if slots<=0:continue
        ca=[]
        for s,a in bi.data.items():
            if s in pos:continue
            i=bi.bysym[s].get(day)
            if i is None or i<57 or (s in cool and day-cool[s]<3*86400):continue
            turn,vol,j=bi.quality(s,i)
            if turn<100_000_000 or vol<100_000 or j>=2:continue
            gap=a[i]['o']/a[i-1]['c']-1
            if a[i]['o']<5 or not(-.04<=gap<=.018):continue
            f=bi.feat(s,i)
            if not r.passes_all(f,reg,tb,ts):continue
            e=extra(s,i)
            if not e:continue
            ret3,ret10,ext,wick,vper,persist=e
            # Market-relative proxy: require positive short return; stronger requirement outside bull.
            need=rel3 if reg=='BULL' else rel3+.005
            if ret3<need or ret10<0 or ext>extmax or wick>.55 or vper<vpmin or (confirm and not persist):continue
            rank=f['m']['pct']+2*f['imp']+ret3*100+min(5,(vper-1)*4)-max(0,ext-1.5)*2
            ca.append((rank,s,i,f))
        ca.sort(reverse=True)
        for _,s,i,f in ca[:slots]:
            px=bi.data[s][i]['o'];sd=max(.018,min(.032,1.8*f['m']['atr']/px));risk=rb if reg=='BULL' else rs
            q1=math.floor((START*risk)/max(.01,px*sd));cap=min(cash/max(1,slots),START/maxp);q2=math.floor(cap/(px*(1+FEE)));q=max(0,min(q1,q2))
            if q:cash-=q*px*(1+FEE);pos[s]={'q':q,'en':px,'hi':px,'hard':px*(1-sd)};slots-=1
            if slots<=0:break
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        z=[x for x in bi.data[s] if x['t']<=we]
        if z:
            px=z[-1]['c'];cash+=p['q']*px*(1-FEE);tr.append((s,(px/p['en']-1)*100-.2,'SON'))
    gw=sum(max(0,x[1]) for x in tr);gl=-sum(min(0,x[1]) for x in tr);win=sum(x[1]>0 for x in tr)
    return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*win/len(tr) if tr else 0,'pf':gw/gl if gl else (99 if gw else 0)}

rows=[]
base=(.50,.38,74,74,.005,.0025,3,1)
for rel in (0,.005,.01):
 for ext in (2.5,3.0,3.5):
  for vp in (.85,1.0,1.1):
   for conf in (False,True):
    cfg=base+(rel,ext,vp,conf);rs=[simulate(cfg,w) for w in bi.WINDOWS];active=[x for x in rs if x['n']]
    avg=sum(x['ret'] for x in rs)/4;worst=min(x['ret'] for x in rs);dd=sum(x['dd'] for x in rs)/4;n=sum(x['n'] for x in rs);pos=sum(x['ret']>0 for x in rs);pf=sum(min(3,x['pf']) for x in active)/len(active) if active else 0
    score=avg+.8*worst-.5*dd+.45*(pf-1)+.15*pos+min(.35,n/50)
    rows.append({'cfg':cfg,'rs':rs,'avg':avg,'worst':worst,'dd':dd,'n':n,'pos':pos,'pf':pf,'score':score})
rows.sort(key=lambda x:x['score'],reverse=True);b=rows[0]
lines=['# BR-Entry v3 Giriş Zamanlaması Testi',f'Evren {len(bi.syms)}, veri {len(bi.data)}, 4 x 31 gün; TUPRS/savunma hariç; lookahead yok; maliyet %0.10/yon.','',f'EN İYİ: rel3>={b["cfg"][8]*100:.1f}%, EMA20 uzaklık <={b["cfg"][9]:.1f} ATR, hacim sürekliliği >={b["cfg"][10]:.2f}, 2-gün teyit={b["cfg"][11]}.',f'Ort getiri **{b["avg"]:.2f}%**, en kötü **{b["worst"]:.2f}%**, ort DD **{b["dd"]:.2f}%**, işlem **{b["n"]}**, pozitif dönem **{b["pos"]}/4**, PF **{b["pf"]:.2f}**.','','|Dönem|Getiri|DD|N|Win|PF|','|---|---:|---:|---:|---:|---:|']
for i,x in enumerate(b['rs'],1):lines.append(f'|{i}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|')
lines+=['','## Top 10','|Rel3|ATR uz.|VolPersist|Teyit|Avg|Worst|DD|N|Pozitif|PF|','|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|']
for x in rows[:10]:
 c=x['cfg'];lines.append(f'|{c[8]*100:.1f}%|{c[9]:.1f}|{c[10]:.2f}|{c[11]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["pos"]}/4|{x["pf"]:.2f}|')
Path('research/result_entry_v3.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_entry_v3.json').write_text(json.dumps({'best':b,'top':rows[:30]},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))