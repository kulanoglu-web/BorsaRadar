import json, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import backtest_month as b

START=100000.0; FEE=.001; HORIZON=31

data={}; fails=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    fut={ex.submit(b.fetch,s):s for s in b.SYMS}
    for i,f in enumerate(as_completed(fut),1):
        s=fut[f]
        try:
            a=f.result()
            if len(a)>=70:data[s]=a
            else:fails.append((s,'short'))
        except Exception as e:fails.append((s,str(e)[:60]))
        if i%100==0: print('FETCH',i,'OK',len(data),'FAIL',len(fails),flush=True)

bysym={s:{r['t']:i for i,r in enumerate(a)} for s,a in data.items()}
dates=sorted(set(r['t'] for a in data.values() for r in a)); end=max(dates); start=end-HORIZON*86400
mcache={}; fcache={}; qcache={}

def M(s,idx):
    k=(s,idx)
    if k not in mcache:mcache[k]=b.method(data[s][:idx])
    return mcache[k]

def ema_stack(s,idx):
    a=data[s][:idx]; c=[r['c'] for r in a]
    e5=b.ema(c[-min(len(c),30):],5); e10=b.ema(c[-min(len(c),50):],10); e20=b.ema(c[-min(len(c),80):],20)
    c3=[r['c'] for r in data[s][:max(1,idx-3)]]
    e20prev=b.ema(c3[-min(len(c3),80):],20) if c3 else e20
    slope=0 if e20prev==0 else e20/e20prev-1
    return e5,e10,e20,slope

def quality(s,idx):
    k=(s,idx)
    if k in qcache:return qcache[k]
    a=data[s]; z=a[max(0,idx-20):idx]
    turn=sum(r['c']*r['v'] for r in z)/max(1,len(z)); vol=sum(r['v'] for r in z)/max(1,len(z)); jumps=0
    for j in range(max(1,idx-10),idx):
        if abs(a[j]['c']/a[j-1]['c']-1)>=.075:jumps+=1
    qcache[k]=(turn,vol,jumps); return qcache[k]

def breadth(day):
    good=up=0
    for s,a in data.items():
        idx=bysym[s].get(day)
        if idx is None or idx<30:continue
        turn,vol,jumps=quality(s,idx)
        if turn<100_000_000:continue
        e5,e10,e20,slope=ema_stack(s,idx)
        good+=1
        if a[idx-1]['c']>e20 and slope>0:up+=1
    return up/good if good else 0
breadth_cache={d:breadth(d) for d in dates if d>=start}
print('BREADTH',round(min(breadth_cache.values())*100,1),round(max(breadth_cache.values())*100,1),flush=True)

def features(s,idx):
    k=(s,idx)
    if k in fcache:return fcache[k]
    m=M(s,idx); m2=M(s,idx-2) if idx>=57 else m; impulse=m['pct']-m2['pct']
    e5,e10,e20,slope=ema_stack(s,idx)
    a=data[s]; z=a[max(0,idx-20):idx]
    cm=b.cmf(z,20); vols=[r['v'] for r in a[max(0,idx-21):idx-1]]; av=sum(vols)/max(1,len(vols)); rv=a[idx-1]['v']/av if av>0 else 1
    mom3=a[idx-1]['c']/a[idx-4]['c']-1 if idx>=4 else 0
    mom8=a[idx-1]['c']/a[idx-9]['c']-1 if idx>=9 else 0
    accel=mom3-(mom8*3/8)
    f={'m':m,'impulse':impulse,'e5':e5,'e10':e10,'e20':e20,'slope':slope,'cmf':cm,'rv':rv,'mom3':mom3,'accel':accel}
    fcache[k]=f; return f

def simulate(cfg):
    thr,imp_min,rv_min,cmf_min,breadth_min,maxpos,risk_pct=cfg
    cash=START; pos={}; trades=[]; peak=START; maxdd=0; cooldown={}
    for day in dates:
        if day<start:continue
        # exits
        for s in list(pos):
            idx=bysym[s].get(day)
            if idx is None:continue
            a=data[s]; bar=a[idx]; p=pos[s]; p['high']=max(p['high'],bar['h']); gain=p['high']/p['entry']-1
            atr_now=M(s,idx)['atr']; stop=max(p['hard'],p['high']*.94,p['high']-2.2*atr_now)
            if gain>=.05:stop=max(stop,p['entry']*1.01)
            if gain>=.10:stop=max(stop,p['high']*.95,p['entry']*1.05)
            exit_price=reason=None
            if bar['l']<=stop:
                exit_price=bar['o'] if bar['o']<stop else stop; reason='STOP/KAR-KORU'
            else:
                f=features(s,idx)
                if f['m']['pct']<46 or f['impulse']<-5 or (gain>.03 and f['m']['vp']<-.05):
                    exit_price=bar['o']; reason='IMPULSE-ZAYIF'
            if exit_price:
                cash+=p['qty']*exit_price*(1-FEE); ret=(exit_price/p['entry']-1)*100-2*FEE*100
                trades.append((s,p['entry_day'],day,p['entry'],exit_price,ret,reason)); del pos[s]; cooldown[s]=day
        slots=maxpos-len(pos)
        if slots>0 and breadth_cache.get(day,0)>=breadth_min:
            cand=[]
            for s,a in data.items():
                if s in pos:continue
                idx=bysym[s].get(day)
                if idx is None or idx<57:continue
                if s in cooldown and day-cooldown[s]<3*86400:continue
                turn,vol,jumps=quality(s,idx)
                if turn<100_000_000 or vol<100_000 or jumps>=2:continue
                bar=a[idx]; prev=a[idx-1]['c']; gap=bar['o']/prev-1
                if bar['o']<5 or gap>.03 or gap<-.05:continue
                f=features(s,idx); m=f['m']
                short_stack=f['e5']>f['e10']>f['e20'] and f['slope']>0
                if m['pct']>=thr and f['impulse']>=imp_min and f['rv']>=rv_min and f['cmf']>=cmf_min and short_stack and f['accel']>-.005 and not m['trap'] and m['vp']>0:
                    rank=m['pct']+2*f['impulse']+min(6,(f['rv']-1)*4)+min(6,f['cmf']*20)+min(5,f['slope']*500)
                    cand.append((rank,s,idx,f))
            cand.sort(reverse=True)
            for rank,s,idx,f in cand[:slots]:
                price=data[s][idx]['o']; atr=f['m']['atr']; stop_dist=max(.018,min(.035,2.0*atr/price if price else .025))
                risk_cash=START*risk_pct; qty_risk=math.floor(risk_cash/max(.01,price*stop_dist)); alloc_cap=min(cash/max(1,slots),START/maxpos); qty_cap=math.floor(alloc_cap/(price*(1+FEE))); qty=max(0,min(qty_risk,qty_cap))
                if qty<=0:continue
                cash-=qty*price*(1+FEE); pos[s]={'qty':qty,'entry':price,'entry_day':day,'high':price,'hard':price*(1-stop_dist)}; slots-=1
                if slots<=0:break
        equity=cash
        for s,p in pos.items():
            idx=bysym[s].get(day); px=data[s][idx]['c'] if idx is not None else p['entry']; equity+=p['qty']*px
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    for s,p in list(pos.items()):
        bar=data[s][-1]; cash+=p['qty']*bar['c']*(1-FEE); ret=(bar['c']/p['entry']-1)*100-2*FEE*100; trades.append((s,p['entry_day'],bar['t'],p['entry'],bar['c'],ret,'DONEM-SONU'))
    wins=sum(t[5]>0 for t in trades); gw=sum(max(0,t[5]) for t in trades); gl=-sum(min(0,t[5]) for t in trades)
    return {'cfg':cfg,'end':cash,'ret':(cash/START-1)*100,'maxdd':maxdd*100,'trades':len(trades),'winrate':100*wins/len(trades) if trades else 0,'pf':gw/gl if gl>0 else 99,'details':trades}

results=[]
# compact but meaningful grid
for thr in (62,66,70):
  for imp in (2,5,8):
    for rv in (1.0,1.1,1.2):
      for cm in (0.0,.03,.06):
        for br in (.40,.45,.50):
          cfg=(thr,imp,rv,cm,br,3,.006)
          r=simulate(cfg)
          if r['trades']>=3: results.append(r)
results.sort(key=lambda r:(r['ret']-.7*r['maxdd'],r['pf'],r['ret']),reverse=True)
best=results[0] if results else simulate((62,2,1.0,0,.4,3,.006))

def D(t):return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
lines=['# BorsaRadar BR-Impulse 1 Aylık Test',f'Evren {len(b.SYMS)}, veri {len(data)}, başlangıç 100.000 TL, maliyet tek yön %0.10.','Lookahead yok; sinyal önceki kapanıştan, işlem sonraki seans. Savunma hisseleri hariç.','', '## En iyi model',f'Config: threshold {best["cfg"][0]}, impulse >= {best["cfg"][1]}, RVOL >= {best["cfg"][2]}, CMF >= {best["cfg"][3]}, breadth >= %{best["cfg"][4]*100:.0f}, maxpos {best["cfg"][5]}, risk/işlem %{best["cfg"][6]*100:.2f}.',f'**{best["end"]:.2f} TL** | getiri **%{best["ret"]:.2f}** | MaxDD **%{best["maxdd"]:.2f}** | işlem {best["trades"]} | kazanma **%{best["winrate"]:.1f}** | PF **{best["pf"]:.2f}**','', '## En iyi 10 kombinasyon','| Thr | Imp | RVOL | CMF | Breadth | Son TL | Getiri % | MaxDD % | İşlem | Win % | PF |','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in results[:10]:
    c=r['cfg']; lines.append(f'| {c[0]} | {c[1]} | {c[2]:.1f} | {c[3]:.2f} | {c[4]*100:.0f} | {r["end"]:.0f} | {r["ret"]:.2f} | {r["maxdd"]:.2f} | {r["trades"]} | {r["winrate"]:.1f} | {r["pf"]:.2f} |')
lines += ['', '## İşlemler','| Hisse | Giriş | Çıkış | Alış | Satış | Net % | Neden |','|---|---|---|---:|---:|---:|---|']
for t in best['details']:lines.append(f'| {t[0]} | {D(t[1])} | {D(t[2])} | {t[3]:.2f} | {t[4]:.2f} | {t[5]:.2f} | {t[6]} |')
Path('research/result_impulse.md').write_text('\n'.join(lines),encoding='utf-8'); Path('research/result_impulse.json').write_text(json.dumps({'best':best,'top':results[:25]},ensure_ascii=False,indent=2),encoding='utf-8'); print('\n'.join(lines),flush=True)
