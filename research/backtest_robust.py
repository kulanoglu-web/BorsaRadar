import json, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import backtest_month as b

START=100000.; FEE=.001
# 4 rolling 31-day windows, latest first.
WINDOWS=[(0,31),(31,62),(62,93),(93,124)]

data={};fails=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    fut={ex.submit(b.fetch,s):s for s in b.SYMS}
    for i,f in enumerate(as_completed(fut),1):
        s=fut[f]
        try:
            a=f.result()
            if len(a)>=100:data[s]=a
            else:fails.append(s)
        except Exception:fails.append(s)
        if i%100==0:print('FETCH',i,'OK',len(data),'FAIL',len(fails),flush=True)

bysym={s:{r['t']:i for i,r in enumerate(a)} for s,a in data.items()}
dates=sorted(set(r['t'] for a in data.values() for r in a)); END=max(dates)
mc={};ec={};qc={}
def M(s,i):
    k=(s,i)
    if k not in mc:mc[k]=b.method(data[s][:i])
    return mc[k]
def stack(s,i):
    k=(s,i)
    if k in ec:return ec[k]
    c=[r['c'] for r in data[s][:i]]; e5=b.ema(c[-30:],5);e10=b.ema(c[-50:],10);e20=b.ema(c[-80:],20)
    cp=[r['c'] for r in data[s][:max(1,i-3)]];ep=b.ema(cp[-80:],20);sl=e20/ep-1 if ep else 0
    ec[k]=(e5,e10,e20,sl);return ec[k]
def quality(s,i):
    k=(s,i)
    if k in qc:return qc[k]
    z=data[s][max(0,i-20):i];turn=sum(x['c']*x['v'] for x in z)/max(1,len(z));vol=sum(x['v'] for x in z)/max(1,len(z));j=sum(abs(data[s][q]['c']/data[s][q-1]['c']-1)>=.075 for q in range(max(1,i-10),i));qc[k]=(turn,vol,j);return qc[k]
def breadth(day):
    good=up=0
    for s,a in data.items():
        i=bysym[s].get(day)
        if i is None or i<30:continue
        turn,vol,j=quality(s,i)
        if turn<100_000_000:continue
        e5,e10,e20,sl=stack(s,i);good+=1;up+=a[i-1]['c']>e20 and sl>0
    return up/good if good else 0
breadth_cache={d:breadth(d) for d in dates}
fc={}
def feat(s,i):
    k=(s,i)
    if k in fc:return fc[k]
    a=data[s];m=M(s,i);m2=M(s,i-2);e5,e10,e20,sl=stack(s,i);z=a[max(0,i-20):i];cm=b.cmf(z,20);vv=a[max(0,i-21):i-1];av=sum(x['v'] for x in vv)/max(1,len(vv));rv=a[i-1]['v']/av if av else 1
    mom3=a[i-1]['c']/a[i-4]['c']-1;mom8=a[i-1]['c']/a[i-9]['c']-1;acc=mom3-mom8*3/8
    fc[k]=(m,m['pct']-m2['pct'],e5,e10,e20,sl,cm,rv,acc);return fc[k]

def simulate(cfg,w):
    thr,imp,rvmin,brmin,maxpos,risk=cfg;off0,off1=w;w_end=END-off0*86400;w_start=END-off1*86400
    cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in dates:
        if day<w_start or day>w_end:continue
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
                cash+=p['q']*xp*(1-FEE);tr.append((s,p['day'],day,(xp/p['en']-1)*100-.2,reason));del pos[s];cool[s]=day
        slots=maxpos-len(pos)
        if slots>0 and breadth_cache.get(day,0)>=brmin:
            cand=[]
            for s,a in data.items():
                if s in pos:continue
                i=bysym[s].get(day)
                if i is None or i<57 or (s in cool and day-cool[s]<3*86400):continue
                turn,vol,j=quality(s,i)
                if turn<100_000_000 or vol<100_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.05<=gap<=.025):continue
                m,im,e5,e10,e20,sl,cm,rv,acc=feat(s,i)
                if m['pct']>=thr and im>=imp and rv>=rvmin and cm>=0 and e5>e10>e20 and sl>0 and acc>-.004 and not m['trap'] and m['vp']>.02:
                    rank=m['pct']+2*im+min(5,(rv-1)*4)+min(5,cm*20);cand.append((rank,s,i,m))
            cand.sort(reverse=True)
            for rank,s,i,m in cand[:slots]:
                px=data[s][i]['o'];sd=max(.018,min(.032,1.8*m['atr']/px));rc=START*risk;q1=math.floor(rc/max(.01,px*sd));cap=min(cash/max(1,slots),START/maxpos);q2=math.floor(cap/(px*(1+FEE)));q=max(0,min(q1,q2))
                if q:cash-=q*px*(1+FEE);pos[s]={'q':q,'en':px,'day':day,'hi':px,'hard':px*(1-sd)};slots-=1
                if slots<=0:break
        eq=cash
        for s,p in pos.items():
            i=bysym[s].get(day);eq+=p['q']*(data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        # close at last bar at/before window end
        cand=[x for x in data[s] if x['t']<=w_end]
        if not cand:continue
        x=cand[-1];cash+=p['q']*x['c']*(1-FEE);tr.append((s,p['day'],x['t'],(x['c']/p['en']-1)*100-.2,'SON'))
    win=sum(x[3]>0 for x in tr);gw=sum(max(0,x[3]) for x in tr);gl=-sum(min(0,x[3]) for x in tr)
    return {'ret':(cash/START-1)*100,'end':cash,'dd':dd*100,'n':len(tr),'win':100*win/len(tr) if tr else 0,'pf':gw/gl if gl else 99,'details':tr}

configs=[]
for thr in (68,70,72,74):
 for imp in (0,2,4):
  for rv in (1.0,1.1,1.2):
   for br in (.45,.50,.55):
    for mp in (3,5):configs.append((thr,imp,rv,br,mp,.005))

rows=[]
for k,cfg in enumerate(configs,1):
    rs=[simulate(cfg,w) for w in WINDOWS]; rets=[r['ret'] for r in rs];dds=[r['dd'] for r in rs];ns=[r['n'] for r in rs];pfs=[r['pf'] for r in rs]
    # favor consistency, PF>1, enough trades; punish one-period overfit
    avg=sum(rets)/4;worst=min(rets);avgdd=sum(dds)/4;totaln=sum(ns);pos=sum(x>0 for x in rets);pf=sum(min(3,x) for x in pfs)/4
    score=avg+0.45*worst-0.45*avgdd+0.35*(pf-1)+0.12*pos + min(0.5,totaln/80)
    rows.append({'cfg':cfg,'rs':rs,'avg':avg,'worst':worst,'avgdd':avgdd,'n':totaln,'pos':pos,'pf':pf,'score':score})
    if k%50==0:print('GRID',k,'/',len(configs),flush=True)
rows.sort(key=lambda x:x['score'],reverse=True);best=rows[0]

def D(t):return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
lines=['# BR-Confirm Genişletilmiş 4-Dönem Testi',f'Evren {len(b.SYMS)}, veri {len(data)}, 4 x 31 günlük dönem. Lookahead yok, maliyet tek yön %0.10.','',f'EN İYİ config: threshold {best["cfg"][0]}, impulse {best["cfg"][1]}, RVOL {best["cfg"][2]}, breadth %{best["cfg"][3]*100:.0f}, maxpos {best["cfg"][4]}, risk/işlem %{best["cfg"][5]*100:.2f}.',f'Ortalama getiri **%{best["avg"]:.2f}**, en kötü dönem **%{best["worst"]:.2f}**, ort. MaxDD **%{best["avgdd"]:.2f}**, toplam işlem **{best["n"]}**, pozitif dönem **{best["pos"]}/4**, ort. PF **{best["pf"]:.2f}**.','', '## Dönem sonuçları','|Dönem|Son TL|Getiri|MaxDD|İşlem|Win|PF|','|---|---:|---:|---:|---:|---:|---:|']
for i,r in enumerate(best['rs'],1):lines.append(f'|{i}|{r["end"]:.0f}|{r["ret"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["win"]:.1f}%|{r["pf"]:.2f}|')
lines+=['','## En iyi 15 config','|Thr|Imp|RVOL|Breadth|Pos|Avg %|Worst %|AvgDD %|N|Pozitif|PF|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in rows[:15]:
 c=x['cfg'];lines.append(f'|{c[0]}|{c[1]}|{c[2]:.1f}|{c[3]*100:.0f}|{c[4]}|{x["avg"]:.2f}|{x["worst"]:.2f}|{x["avgdd"]:.2f}|{x["n"]}|{x["pos"]}/4|{x["pf"]:.2f}|')
Path('research/result_robust.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_robust.json').write_text(json.dumps({'best':best,'top':rows[:30]},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines),flush=True)
