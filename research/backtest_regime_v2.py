import json, math
from pathlib import Path
from datetime import datetime, timezone
import backtest_indicators as bi

START=bi.START; FEE=bi.FEE; WINDOWS=bi.WINDOWS
ALL=['TREND','MOMENTUM','FLOW','STRENGTH']

def prev_breadth(day,steps=3):
    ds=[d for d in bi.dates if d<day]
    if not ds:return bi.breadth_cache.get(day,0)
    j=max(0,len(ds)-steps)
    return bi.breadth_cache.get(ds[j],bi.breadth_cache.get(day,0))

def regime(day,bull,side):
    br=bi.breadth_cache.get(day,0); prev=prev_breadth(day,3); delta=br-prev
    if br>=bull and delta>=-.03:return 'BULL'
    if br>=side and delta>=0:return 'SIDE'
    return 'RISKOFF'

def passes_all(f,reg,thr_bull,thr_side):
    thr=thr_bull if reg=='BULL' else thr_side
    if f['m']['pct']<thr or f['m']['trap']:return False
    if not (f['e5']>f['e10']>f['e20'] and f['slope']>0 and f['e20']>f['e50']):return False
    if not (f['imp']>=1 and f['acc']>-.004 and 48<=f['rsi']<=72):return False
    if not (f['cmf']>=0 and f['rv']>=.85 and f['m']['vp']>.02):return False
    if not (f['adx']>=15 and f['cci']>-60 and f['stoch']<97):return False
    return True

def simulate(cfg,w):
    bull,side,thr_bull,thr_side,risk_bull,risk_side,max_bull,max_side=cfg
    off0,off1=w; we=bi.END-off0*86400; ws=bi.END-off1*86400
    cash=START;pos={};tr=[];peak=START;dd=0;cool={};reg_days={'BULL':0,'SIDE':0,'RISKOFF':0}
    for day in bi.dates:
        if day<ws or day>we:continue
        reg=regime(day,bull,side);reg_days[reg]+=1
        for s in list(pos):
            i=bi.bysym[s].get(day)
            if i is None:continue
            bar=bi.data[s][i];p=pos[s];p['hi']=max(p['hi'],bar['h']);gain=p['hi']/p['en']-1;f=bi.feat(s,i);m=f['m']
            trail=.955 if reg=='BULL' else .965 if reg=='SIDE' else .98
            stop=max(p['hard'],p['hi']*trail,p['hi']-2.0*m['atr'])
            if gain>=.04:stop=max(stop,p['en']*1.006)
            if gain>=.08:stop=max(stop,p['hi']*.965,p['en']*1.03)
            xp=reason=None
            if bar['l']<=stop:xp=bar['o'] if bar['o']<stop else stop;reason='STOP'
            elif reg=='RISKOFF':xp=bar['o'];reason='REJIM-RISKOFF'
            elif m['pct']<50 or f['imp']<-4 or (gain>.03 and f['cmf']<0):xp=bar['o'];reason='ZAYIF'
            if xp:
                cash+=p['q']*xp*(1-FEE);tr.append((s,p['day'],day,(xp/p['en']-1)*100-.2,reason,reg));del pos[s];cool[s]=day
        if reg=='RISKOFF':
            slots=0
        else:
            maxpos=max_bull if reg=='BULL' else max_side;slots=maxpos-len(pos)
        if slots>0:
            ca=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<57 or (s in cool and day-cool[s]<3*86400):continue
                turn,vol,j=bi.quality(s,i)
                if turn<100_000_000 or vol<100_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.045<=gap<=.022):continue
                f=bi.feat(s,i)
                if passes_all(f,reg,thr_bull,thr_side):
                    rank=f['m']['pct']+2*f['imp']+min(6,(f['rv']-1)*5)+min(6,f['cmf']*20)+min(4,f['adx']/10)
                    ca.append((rank,s,i,f))
            ca.sort(reverse=True)
            for rank,s,i,f in ca[:slots]:
                px=bi.data[s][i]['o'];sd=max(.018,min(.032,1.8*f['m']['atr']/px));risk=risk_bull if reg=='BULL' else risk_side;rc=START*risk
                q1=math.floor(rc/max(.01,px*sd));cap=min(cash/max(1,slots),START/maxpos);q2=math.floor(cap/(px*(1+FEE)));q=max(0,min(q1,q2))
                if q:cash-=q*px*(1+FEE);pos[s]={'q':q,'en':px,'day':day,'hi':px,'hard':px*(1-sd)};slots-=1
                if slots<=0:break
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        cand=[x for x in bi.data[s] if x['t']<=we]
        if not cand:continue
        x=cand[-1];cash+=p['q']*x['c']*(1-FEE);tr.append((s,p['day'],x['t'],(x['c']/p['en']-1)*100-.2,'SON',regime(x['t'],bull,side)))
    win=sum(x[3]>0 for x in tr);gw=sum(max(0,x[3]) for x in tr);gl=-sum(min(0,x[3]) for x in tr)
    return {'ret':(cash/START-1)*100,'end':cash,'dd':dd*100,'n':len(tr),'win':100*win/len(tr) if tr else 0,'pf':gw/gl if gl else (99 if gw else 0),'details':tr,'reg_days':reg_days}

configs=[]
for bull in (.50,.55,.60):
 for side in (.38,.42,.46):
  if side>=bull:continue
  for tb in (70,72,74):
   for ts in (74,76,78):
    for rb,rs in ((.005,.003),(.006,.003),(.005,.0025)):
     for mb,ms in ((5,2),(4,2),(3,1)):
      configs.append((bull,side,tb,ts,rb,rs,mb,ms))

rows=[]
for k,cfg in enumerate(configs,1):
    rs=[simulate(cfg,w) for w in WINDOWS];rets=[r['ret'] for r in rs];dds=[r['dd'] for r in rs];active=[r for r in rs if r['n']>0]
    avg=sum(rets)/4;worst=min(rets);avgdd=sum(dds)/4;n=sum(r['n'] for r in rs);pos=sum(x>0 for x in rets);pf=sum(min(3,r['pf']) for r in active)/len(active) if active else 0
    score=avg+.7*worst-.55*avgdd+.5*(pf-1)+.18*pos+min(.5,n/60)
    rows.append({'cfg':cfg,'rs':rs,'avg':avg,'worst':worst,'avgdd':avgdd,'n':n,'pos':pos,'pf':pf,'score':score})
    if k%100==0:print('GRID',k,'/',len(configs),flush=True)
rows.sort(key=lambda x:x['score'],reverse=True);best=rows[0]
lines=['# BR-Regime v2 Dinamik Rejim Testi',f'Config sayısı {len(configs)}, evren {len(bi.syms)}, veri {len(bi.data)}, 4 x 31 gün. TUPRS ve savunma hariç. Lookahead yok, tek yön maliyet %0.10.','',f'EN İYİ: bull>={best["cfg"][0]:.2f}, side>={best["cfg"][1]:.2f}, bull skor>={best["cfg"][2]}, side skor>={best["cfg"][3]}, bull risk %{best["cfg"][4]*100:.2f}, side risk %{best["cfg"][5]*100:.2f}, maxpos {best["cfg"][6]}/{best["cfg"][7]}.',f'Ort getiri **%{best["avg"]:.2f}**, en kötü **%{best["worst"]:.2f}**, ort DD **%{best["avgdd"]:.2f}**, toplam işlem **{best["n"]}**, pozitif dönem **{best["pos"]}/4**, PF **{best["pf"]:.2f}**.','', '## Dönemler','|Dönem|Getiri|DD|N|Win|PF|Bull gün|Side gün|RiskOff|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for i,r in enumerate(best['rs'],1):
    g=r['reg_days'];lines.append(f'|{i}|{r["ret"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["win"]:.1f}%|{r["pf"]:.2f}|{g["BULL"]}|{g["SIDE"]}|{g["RISKOFF"]}|')
lines+=['','## Top 15','|Bull|Side|TB|TS|RB|RS|Pos|Avg|Worst|DD|N|Pozitif|PF|','|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|']
for x in rows[:15]:
 c=x['cfg'];lines.append(f'|{c[0]:.2f}|{c[1]:.2f}|{c[2]}|{c[3]}|{c[4]*100:.2f}%|{c[5]*100:.2f}%|{c[6]}/{c[7]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["avgdd"]:.2f}%|{x["n"]}|{x["pos"]}/4|{x["pf"]:.2f}|')
Path('research/result_regime_v2.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_regime_v2.json').write_text(json.dumps({'best':best,'top':rows[:40]},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines),flush=True)