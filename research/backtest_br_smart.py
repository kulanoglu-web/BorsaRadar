# BR-SMART: simplified independent-factor model
# Reuses cached/fetched BIST feature engine; no lookahead.
import json
from pathlib import Path
import backtest_indicators as bi

# Independent votes: trend 30, relative strength 25, momentum 20, flow 15, quality 10.
def smart_score(s, i, breadth):
    a=bi.DATA[s]
    if i < 55: return None
    x=a[:i]  # yesterday and earlier only
    f=bi.features(x)
    c=[r['c'] for r in x]
    close=c[-1]
    e20=bi.ema(c[-50:],20); e50=bi.ema(c[-100:],50)
    # Trend: structure + EMA20 slope
    e20old=bi.ema(c[-55:-5],20) if len(c)>=55 else e20
    trend=30*(0.55*(close>e20>e50)+0.25*(e20>e20old)+0.20*min(1,max(0,(close/e20-1)/.04)))
    # Relative strength: 3d and 10d stock return versus cross-sectional market median supplied below
    r3=close/c[-4]-1 if len(c)>4 else 0; r10=close/c[-11]-1 if len(c)>11 else 0
    rel=25*(0.55*min(1,max(0,(r3+0.01)/.04))+0.45*min(1,max(0,(r10+0.02)/.08)))
    # Momentum: MACD direction + RSI healthy zone, avoid duplicate oscillator voting
    rr=bi.rsi(c); mom=20*(0.55*(f['mac']>f['ms'])+0.45*(48<=rr<=72))
    # Flow: CMF and persistent relative volume
    flow=15*(0.60*min(1,max(0,(f['cmf']+.05)/.20))+0.40*min(1,max(0,(f['rv']-.7)/.8)))
    # Quality: ADX/trend efficiency, penalize traps/exhaustion
    q=10*(0.55*min(1,max(0,f['adx']/30))+0.45*min(1,max(0,(f['eff']+.05)/.35)))
    score=trend+rel+mom+flow+q
    if f['trap'] or rr>78: score-=25
    # Market regime: breadth is prior-close breadth. No fresh longs in weak tape.
    if breadth < .38: return None
    if breadth < .48: score-=8
    return score,f

def simulate(threshold=70,maxpos=3,risk=.005):
    dates=bi.DATES; by=bi.BY; cash=100000.; pos={}; trades=[]; peak=cash; maxdd=0
    for day in dates:
        # prior-close breadth
        eligible=up=0
        for s,a in bi.DATA.items():
            idx=by[s].get(day)
            if idx is None or idx<55: continue
            c=[r['c'] for r in a[:idx]]; eligible+=1
            if c[-1]>bi.ema(c[-50:],20): up+=1
        breadth=up/eligible if eligible else 0
        # exits first: ATR risk + trend failure/profit guard
        for s in list(pos):
            a=bi.DATA[s]; idx=by[s].get(day)
            if idx is None: continue
            bar=a[idx]; p=pos[s]; p['high']=max(p['high'],bar['h']); gain=p['high']/p['entry']-1
            stop=max(p['hard'],p['high']-2.2*p['atr'])
            if gain>=.06: stop=max(stop,p['entry']*1.01)
            if gain>=.10: stop=max(stop,p['high']-.0-p['atr']*1.6,p['entry']*1.045)
            ex=None
            if bar['l']<=stop: ex=min(bar['o'],stop) if bar['o']<stop else stop
            else:
                sc=smart_score(s,idx,breadth)
                if sc is None or sc[0]<52: ex=bar['o']
            if ex:
                cash+=p['qty']*ex*(1-bi.FEE); trades.append((ex/p['entry']-1-2*bi.FEE)*100); del pos[s]
        slots=maxpos-len(pos)
        if slots>0 and breadth>=.38:
            cand=[]
            for s,a in bi.DATA.items():
                if s in pos: continue
                idx=by[s].get(day)
                if idx is None: continue
                z=smart_score(s,idx,breadth)
                if z and z[0]>=threshold:
                    sc,f=z; cand.append((sc,s,idx,f))
            cand.sort(reverse=True)
            for sc,s,idx,f in cand[:slots]:
                price=bi.DATA[s][idx]['o']; atr=max(f['atr'],price*.012); hard=price-2.2*atr
                riskcash=cash*risk; qty=int(min(cash/(max(1,slots)*price*(1+bi.FEE)),riskcash/max(.01,price-hard)))
                if qty<=0: continue
                cash-=qty*price*(1+bi.FEE);pos[s]={'qty':qty,'entry':price,'high':price,'atr':atr,'hard':hard};slots-=1
        eq=cash
        for s,p in pos.items():
            idx=by[s].get(day);eq+=p['qty']*(bi.DATA[s][idx]['c'] if idx is not None else p['entry'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)
    for s,p in pos.items():
        px=bi.DATA[s][-1]['c'];cash+=p['qty']*px*(1-bi.FEE);trades.append((px/p['entry']-1-2*bi.FEE)*100)
    gp=sum(x for x in trades if x>0);gl=-sum(x for x in trades if x<0)
    return {'threshold':threshold,'maxpos':maxpos,'risk':risk,'end':cash,'ret':(cash/100000-1)*100,'dd':maxdd*100,'n':len(trades),'win':100*sum(x>0 for x in trades)/len(trades) if trades else 0,'pf':gp/gl if gl else (99 if gp else 0)}

results=[]
for t in (66,70,74,78):
 for p in (2,3,4):
  for r in (.0035,.005): results.append(simulate(t,p,r))
results.sort(key=lambda x:(x['ret']-.65*x['dd']+min(x['pf'],3)*.2),reverse=True)
best=results[0]
lines=['# BR-SMART Backtest','Bağımsız faktörler: trend %30 + relatif güç %25 + momentum %20 + para akışı %15 + kalite %10. Zayıf piyasa rejiminde yeni AL yok. TUPRS/savunma hariç, lookahead yok, maliyet dahil.','',f'EN IYI: skor {best["threshold"]}, pozisyon {best["maxpos"]}, risk %{best["risk"]*100:.2f}: **{best["ret"]:.2f}%**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, PF **{best["pf"]:.2f}**.','','|Skor|Pos|Risk|Getiri|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results: lines.append(f'|{x["threshold"]}|{x["maxpos"]}|{x["risk"]*100:.2f}%|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))