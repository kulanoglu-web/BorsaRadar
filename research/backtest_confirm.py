import json, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import backtest_month as b

START=100000.; FEE=.001; HORIZON=31
data={}; fails=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    fut={ex.submit(b.fetch,s):s for s in b.SYMS}
    for i,f in enumerate(as_completed(fut),1):
        s=fut[f]
        try:
            a=f.result()
            if len(a)>=70:data[s]=a
            else:fails.append(s)
        except Exception:fails.append(s)
        if i%100==0:print('FETCH',i,'OK',len(data),'FAIL',len(fails),flush=True)

bysym={s:{r['t']:i for i,r in enumerate(a)} for s,a in data.items()}; dates=sorted(set(r['t'] for a in data.values() for r in a)); end=max(dates); start=end-HORIZON*86400
mc={}; ec={}
def M(s,i):
    k=(s,i)
    if k not in mc:mc[k]=b.method(data[s][:i])
    return mc[k]
def stack(s,i):
    k=(s,i)
    if k in ec:return ec[k]
    c=[r['c'] for r in data[s][:i]]; e5=b.ema(c[-30:],5);e10=b.ema(c[-50:],10);e20=b.ema(c[-80:],20)
    cp=[r['c'] for r in data[s][:max(1,i-3)]]; ep=b.ema(cp[-80:],20); sl=e20/ep-1 if ep else 0
    ec[k]=(e5,e10,e20,sl);return ec[k]
def quality(s,i):
    z=data[s][max(0,i-20):i]; turn=sum(x['c']*x['v'] for x in z)/max(1,len(z)); vol=sum(x['v'] for x in z)/max(1,len(z)); jumps=sum(abs(data[s][j]['c']/data[s][j-1]['c']-1)>=.075 for j in range(max(1,i-10),i));return turn,vol,jumps
def market_day(day):
    vals=[]
    for s,a in data.items():
        i=bysym[s].get(day)
        if i is not None and i>=5: vals.append(a[i-1]['c']/a[i-4]['c']-1)
    vals.sort();return vals[len(vals)//2] if vals else 0
market={d:market_day(d) for d in dates if d>=start}
def breadth(day):
    good=up=0
    for s,a in data.items():
        i=bysym[s].get(day)
        if i is None or i<30:continue
        turn,vol,j=quality(s,i)
        if turn<100_000_000:continue
        e5,e10,e20,sl=stack(s,i);good+=1;up+=a[i-1]['c']>e20 and sl>0
    return up/good if good else 0
breadth_cache={d:breadth(d) for d in dates if d>=start}

def feat(s,i):
    a=data[s];m=M(s,i);m2=M(s,i-2);e5,e10,e20,sl=stack(s,i);z=a[max(0,i-20):i];cm=b.cmf(z,20);av=sum(x['v'] for x in a[max(0,i-21):i-1])/max(1,len(a[max(0,i-21):i-1]));rv=a[i-1]['v']/av if av else 1
    r1=a[i-1]['c']/a[i-2]['c']-1;r2=a[i-2]['c']/a[i-3]['c']-1;r3=a[i-3]['c']/a[i-4]['c']-1;mom3=a[i-1]['c']/a[i-4]['c']-1;mom8=a[i-1]['c']/a[i-9]['c']-1;acc=mom3-mom8*3/8;rel=mom3-market.get(a[i]['t'],0)
    # confirmation: recent move is persistent, not one-day spike
    confirm=(r1>-.012 and r2>-.018 and sum(x>0 for x in (r1,r2,r3))>=2)
    return m,m['pct']-m2['pct'],e5,e10,e20,sl,cm,rv,acc,rel,confirm

def sim(cfg):
    thr,imp,rvmin,cmmin,brmin,relmin,confirm,maxpos,risk=cfg;cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in dates:
        if day<start:continue
        for s in list(pos):
            i=bysym[s].get(day)
            if i is None:continue
            bar=data[s][i];p=pos[s];p['hi']=max(p['hi'],bar['h']);gain=p['hi']/p['en']-1;m,im,*_=feat(s,i);stop=max(p['hard'],p['hi']*.945,p['hi']-2.0*m['atr'])
            if gain>=.045:stop=max(stop,p['en']*1.008)
            if gain>=.08:stop=max(stop,p['hi']*.96,p['en']*1.035)
            xp=reason=None
            if bar['l']<=stop:xp=bar['o'] if bar['o']<stop else stop;reason='STOP'
            elif m['pct']<48 or im<-5:xp=bar['o'];reason='ZAYIF'
            if xp:
                cash+=p['q']*xp*(1-FEE);tr.append((s,p['day'],day,p['en'],xp,(xp/p['en']-1)*100-.2,reason));del pos[s];cool[s]=day
        slots=maxpos-len(pos)
        if slots>0 and breadth_cache.get(day,0)>=brmin:
            ca=[]
            for s,a in data.items():
                if s in pos:continue
                i=bysym[s].get(day)
                if i is None or i<57 or (s in cool and day-cool[s]<3*86400):continue
                turn,vol,j=quality(s,i)
                if turn<100_000_000 or vol<100_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.05<=gap<=.025):continue
                m,im,e5,e10,e20,sl,cm,rv,acc,rel,conf=feat(s,i)
                if m['pct']>=thr and im>=imp and rv>=rvmin and cm>=cmmin and e5>e10>e20 and sl>0 and acc>-.004 and rel>=relmin and (conf or not confirm) and not m['trap'] and m['vp']>.02:
                    rank=m['pct']+2*im+min(8,rel*100)+min(5,(rv-1)*4)+min(5,cm*20);ca.append((rank,s,i,m))
            ca.sort(reverse=True)
            for rank,s,i,m in ca[:slots]:
                px=data[s][i]['o'];sd=max(.018,min(.032,1.8*m['atr']/px));rc=START*risk;q1=math.floor(rc/max(.01,px*sd));cap=min(cash/max(1,slots),START/maxpos);q2=math.floor(cap/(px*(1+FEE)));q=max(0,min(q1,q2))
                if q:cash-=q*px*(1+FEE);pos[s]={'q':q,'en':px,'day':day,'hi':px,'hard':px*(1-sd)};slots-=1
                if slots<=0:break
        eq=cash
        for s,p in pos.items():
            i=bysym[s].get(day);eq+=p['q']*(data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        x=data[s][-1];cash+=p['q']*x['c']*(1-FEE);tr.append((s,p['day'],x['t'],p['en'],x['c'],(x['c']/p['en']-1)*100-.2,'SON'))
    win=sum(x[5]>0 for x in tr);gw=sum(max(0,x[5]) for x in tr);gl=-sum(min(0,x[5]) for x in tr)
    return {'cfg':cfg,'end':cash,'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*win/len(tr) if tr else 0,'pf':gw/gl if gl else 99,'details':tr}

R=[]
for thr in (66,70,74):
 for imp in (2,5):
  for rv in (1.1,1.2,1.35):
   for br in (.45,.50,.55):
    for rel in (0,.005,.01,.015):
     for conf in (False,True):
      r=sim((thr,imp,rv,.0,br,rel,conf,3,.005))
      if r['n']>=5:R.append(r)
R.sort(key=lambda x:(x['ret']-.6*x['dd'] + min(1.5,max(-1,x['pf']-1)),x['ret']),reverse=True);best=R[0]
def D(t):return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
lines=['# BR-Confirm 1 Aylık Test',f'Evren {len(b.SYMS)}, veri {len(data)}. Lookahead yok, sonraki seans giriş.','',f'EN İYİ: **{best["end"]:.2f} TL** | **%{best["ret"]:.2f}** | MaxDD **%{best["dd"]:.2f}** | işlem {best["n"]} | win **%{best["win"]:.1f}** | PF **{best["pf"]:.2f}**',f'Config: {best["cfg"]}','', '## Top 12','|Thr|Imp|RV|Breadth|Rel3|Teyit|Son TL|Getiri|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|']
for r in R[:12]:
 c=r['cfg'];lines.append(f'|{c[0]}|{c[1]}|{c[2]}|{c[4]*100:.0f}|{c[5]*100:.1f}%|{c[6]}|{r["end"]:.0f}|{r["ret"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["win"]:.1f}%|{r["pf"]:.2f}|')
lines+=['','## İşlemler','|Hisse|Giriş|Çıkış|Net %|Neden|','|---|---|---|---:|---|']
for x in best['details']:lines.append(f'|{x[0]}|{D(x[1])}|{D(x[2])}|{x[5]:.2f}|{x[6]}|')
Path('research/result_confirm.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_confirm.json').write_text(json.dumps({'best':best,'top':R[:30]},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines),flush=True)