import json, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import backtest_month as b

START=100000.0
FEE=0.001
HORIZON=31

# Fetch once, then reuse all methods/features across parameter grids.
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
mcache={}; qcache={}

def M(s,idx):
    k=(s,idx)
    if k not in mcache:mcache[k]=b.method(data[s][:idx])
    return mcache[k]

def quality(s,idx):
    k=(s,idx)
    if k in qcache:return qcache[k]
    a=data[s]; z=a[max(0,idx-20):idx]
    avg_turn=sum(r['c']*r['v'] for r in z)/max(1,len(z))
    avg_vol=sum(r['v'] for r in z)/max(1,len(z))
    jumps=0
    for j in range(max(1,idx-10),idx):
        if abs(a[j]['c']/a[j-1]['c']-1)>=.085:jumps+=1
    qcache[k]=(avg_turn,avg_vol,jumps)
    return qcache[k]

def breadth(day):
    good=up=0
    for s,a in data.items():
        idx=bysym[s].get(day)
        if idx is None or idx<55:continue
        avg_turn,avg_vol,jumps=quality(s,idx)
        if avg_turn<20_000_000:continue
        good+=1
        if M(s,idx)['trend']:up+=1
    return up/good if good else 0

breadth_cache={d:breadth(d) for d in dates if d>=start}

def simulate(entry_thr,min_turn,breadth_min,maxpos,base_stop=.025,trail=.06,cooldown_days=3):
    cash=START; pos={}; trades=[]; peak=START; maxdd=0; cooldown={}
    for day in dates:
        if day<start:continue
        # exits
        for s in list(pos):
            idx=bysym[s].get(day)
            if idx is None:continue
            a=data[s]; bar=a[idx]; p=pos[s]; p['high']=max(p['high'],bar['h']); gain=p['high']/p['entry']-1
            atr_now=M(s,idx)['atr'] if idx>=55 else p['atr']; stop=max(p['hard'],p['high']*(1-trail),p['high']-2.2*atr_now)
            if gain>=.06:stop=max(stop,p['entry']*1.012)
            if gain>=.12:stop=max(stop,p['high']*.945,p['entry']*1.06)
            exit_price=reason=None
            if bar['l']<=stop:
                exit_price=bar['o'] if bar['o']<stop else stop; reason='STOP/KAR-KORU'
            elif idx>=55:
                m=M(s,idx)
                if m['pct']<44 or (gain>.04 and (m['vp']<-.08 or m['mac']<m['ms'])):
                    exit_price=bar['o']; reason='METOD-ZAYIFLADI'
            if exit_price:
                cash+=p['qty']*exit_price*(1-FEE); ret=(exit_price/p['entry']-1)*100-2*FEE*100
                trades.append((s,p['entry_day'],day,p['entry'],exit_price,ret,reason)); del pos[s]; cooldown[s]=day
        # entries only in healthy breadth
        slots=maxpos-len(pos)
        if slots>0 and breadth_cache.get(day,0)>=breadth_min:
            cand=[]
            for s,a in data.items():
                if s in pos:continue
                idx=bysym[s].get(day)
                if idx is None or idx<55:continue
                if s in cooldown and day-cooldown[s] < cooldown_days*86400:continue
                m=M(s,idx); avg_turn,avg_vol,jumps=quality(s,idx); bar=a[idx]; prev=a[idx-1]['c']; gap=bar['o']/prev-1
                if avg_turn<min_turn or avg_vol<100_000 or jumps>=2:continue
                if bar['o']<5 or gap>.045 or gap<-.06:continue
                if m['pct']>=entry_thr and not m['trap'] and m['trend'] and m['vp']>-.02:
                    # rank quality-adjusted: method strength + liquidity, penalize chase gap
                    rank=m['pct']+min(5,math.log10(max(1,avg_turn/10_000_000))*2)-max(0,gap)*50
                    cand.append((rank,s,idx,m))
            cand.sort(reverse=True)
            for rank,s,idx,m in cand[:slots]:
                price=data[s][idx]['o']; allocation=min(cash/max(1,slots),START/maxpos); qty=math.floor(allocation/(price*(1+FEE)))
                if qty<=0:continue
                cash-=qty*price*(1+FEE); pos[s]={'qty':qty,'entry':price,'entry_day':day,'high':price,'atr':m['atr'],'hard':price*(1-base_stop)}; slots-=1
                if slots<=0:break
        equity=cash
        for s,p in pos.items():
            idx=bysym[s].get(day); px=data[s][idx]['c'] if idx is not None else p['entry']; equity+=p['qty']*px
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    for s,p in list(pos.items()):
        bar=data[s][-1]; cash+=p['qty']*bar['c']*(1-FEE); ret=(bar['c']/p['entry']-1)*100-2*FEE*100; trades.append((s,p['entry_day'],bar['t'],p['entry'],bar['c'],ret,'DONEM-SONU'))
    wins=sum(t[5]>0 for t in trades)
    grosswins=sum(max(0,t[5]) for t in trades); grossloss=-sum(min(0,t[5]) for t in trades)
    return {'thr':entry_thr,'turnover':min_turn,'breadth':breadth_min,'maxpos':maxpos,'stop':base_stop,'trail':trail,'end':cash,'ret':(cash/START-1)*100,'maxdd':maxdd*100,'trades':len(trades),'winrate':100*wins/len(trades) if trades else 0,'pf':grosswins/grossloss if grossloss>0 else 99,'details':trades}

# Stage 1: discover entry-quality gates.
results=[]
for thr in (72,76,80):
    for turn in (20_000_000,50_000_000,100_000_000):
        for br in (.45,.50,.55):
            for mp in (3,5):
                r=simulate(thr,turn,br,mp)
                results.append(r)
                print('GRID',thr,turn,br,mp,'RET',round(r['ret'],2),'DD',round(r['maxdd'],2),'N',r['trades'],flush=True)
results.sort(key=lambda r:(r['ret']-.65*r['maxdd'],r['ret']),reverse=True)
best_gate=results[0]

# Stage 2: tune risk only after quality gate is fixed.
risk=[]
for st in (.02,.025,.03,.035):
    for tr in (.04,.05,.06,.07):
        r=simulate(best_gate['thr'],best_gate['turnover'],best_gate['breadth'],best_gate['maxpos'],st,tr)
        risk.append(r)
risk.sort(key=lambda r:(r['ret']-.65*r['maxdd'],r['ret']),reverse=True)
best=risk[0]

def D(t):return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
lines=['# BorsaRadar QualityGate 1-Aylık Gerçekçi Portföy Testi',f'BIST evreni {len(b.SYMS)}; veri alınan {len(data)}; 100.000 TL; tek yön maliyet %0.10.','Sinyal yalnız önceki kapanışa kadar olan veriyle hesaplanır; işlem sonraki seans fiyatıyla yapılır. Savunma hisseleri hariç.','', '## Eski model karşılaştırması','Önceki geniş test: 81.819 TL / -%18,18 / MaxDD %20,19. Bu çalışma BR-QualityGate + piyasa genişliği + likidite + gap/chase + cooldown filtrelerini sınar.','', '## En iyi giriş filtresi',f"Skor eşiği %{best_gate['thr']}; min günlük ortalama işlem tutarı {best_gate['turnover']/1e6:.0f} mn TL; piyasa genişliği >= %{best_gate['breadth']*100:.0f}; aynı anda {best_gate['maxpos']} pozisyon.",'', '## Risk parametreleri','| Stop % | Trail % | Son TL | Getiri % | MaxDD % | İşlem | Kazanma % | PF |','|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in risk:lines.append(f"| {r['stop']*100:.1f} | {r['trail']*100:.1f} | {r['end']:.2f} | {r['ret']:.2f} | {r['maxdd']:.2f} | {r['trades']} | {r['winrate']:.1f} | {r['pf']:.2f} |")
lines += ['', '## Seçilen model',f"**{best['end']:.2f} TL** | getiri **%{best['ret']:.2f}** | MaxDD **%{best['maxdd']:.2f}** | işlem {best['trades']} | kazanma **%{best['winrate']:.1f}** | PF **{best['pf']:.2f}**",'', '## İşlemler','| Hisse | Giriş | Çıkış | Alış | Satış | Net % | Neden |','|---|---|---|---:|---:|---:|---|']
for t in best['details']:lines.append(f'| {t[0]} | {D(t[1])} | {D(t[2])} | {t[3]:.2f} | {t[4]:.2f} | {t[5]:.2f} | {t[6]} |')
Path('research/result_quality.md').write_text('\n'.join(lines),encoding='utf-8'); Path('research/result_quality.json').write_text(json.dumps({'best_gate':best_gate,'best':best,'risk':risk,'top_gates':results[:10]},ensure_ascii=False,indent=2),encoding='utf-8'); print('\n'.join(lines),flush=True)
