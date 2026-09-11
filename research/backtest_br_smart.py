# BR-SMART: simplified independent-factor model
import json
from pathlib import Path
import backtest_indicators as bi

def smart_score(s,i,breadth):
    a=bi.data[s]
    if i<57:return None
    f=bi.feat(s,i); c=[r['c'] for r in a[:i]]; close=c[-1]
    e20,e50=f['e20'],f['e50'];e20old=bi.b.ema(c[-55:-5],20) if len(c)>=55 else e20
    trend=30*(.55*(close>e20>e50)+.25*(e20>e20old)+.20*min(1,max(0,(close/e20-1)/.04)))
    r3=close/c[-4]-1;r10=close/c[-11]-1
    rel=25*(.55*min(1,max(0,(r3+.01)/.04))+.45*min(1,max(0,(r10+.02)/.08)))
    rr=f['rsi'];m=f['m'];mom=20*(.55*(m['mac']>m['ms'])+.45*(48<=rr<=72))
    flow=15*(.60*min(1,max(0,(f['cmf']+.05)/.20))+.40*min(1,max(0,(f['rv']-.7)/.8)))
    quality=10*(.55*min(1,max(0,f['adx']/30))+.45*min(1,max(0,(f['slope']+.005)/.025)))
    score=trend+rel+mom+flow+quality
    if m['trap'] or rr>78:score-=25
    if breadth<.38:return None
    if breadth<.48:score-=8
    return score,f

def simulate(threshold=70,maxpos=3,risk=.005):
    dates=bi.dates;by=bi.bysym;cash=100000.;pos={};trades=[];peak=cash;maxdd=0
    for day in dates:
        breadth=bi.breadth_cache.get(day,0)
        for s in list(pos):
            a=bi.data[s];idx=by[s].get(day)
            if idx is None:continue
            bar=a[idx];p=pos[s];p['high']=max(p['high'],bar['h']);gain=p['high']/p['entry']-1
            stop=max(p['hard'],p['high']-2.2*p['atr'])
            if gain>=.06:stop=max(stop,p['entry']*1.01)
            if gain>=.10:stop=max(stop,p['high']-p['atr']*1.6,p['entry']*1.045)
            ex=None
            if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop
            else:
                z=smart_score(s,idx,breadth)
                if z is None or z[0]<52:ex=bar['o']
            if ex:
                cash+=p['qty']*ex*(1-bi.FEE);trades.append((ex/p['entry']-1-2*bi.FEE)*100);del pos[s]
        slots=maxpos-len(pos)
        if slots>0 and breadth>=.38:
            cand=[]
            for s,a in bi.data.items():
                if s in pos:continue
                idx=by[s].get(day)
                if idx is None or idx<57:continue
                turn,vol,j=bi.quality(s,idx)
                if turn<100_000_000 or vol<100_000 or j>=2:continue
                gap=a[idx]['o']/a[idx-1]['c']-1
                if a[idx]['o']<5 or not(-.05<=gap<=.025):continue
                z=smart_score(s,idx,breadth)
                if z and z[0]>=threshold:cand.append((z[0],s,idx,z[1]))
            cand.sort(reverse=True)
            for sc,s,idx,f in cand[:slots]:
                price=bi.data[s][idx]['o'];atr=max(f['m']['atr'],price*.012);hard=price-2.2*atr
                riskcash=cash*risk;qty=int(min(cash/(max(1,slots)*price*(1+bi.FEE)),riskcash/max(.01,price-hard)))
                if qty<=0:continue
                cash-=qty*price*(1+bi.FEE);pos[s]={'qty':qty,'entry':price,'high':price,'atr':atr,'hard':hard};slots-=1
        eq=cash
        for s,p in pos.items():
            idx=by[s].get(day);eq+=p['qty']*(bi.data[s][idx]['c'] if idx is not None else p['entry'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        px=bi.data[s][-1]['c'];cash+=p['qty']*px*(1-bi.FEE);trades.append((px/p['entry']-1-2*bi.FEE)*100)
    gp=sum(x for x in trades if x>0);gl=-sum(x for x in trades if x<0)
    return {'threshold':threshold,'maxpos':maxpos,'risk':risk,'end':cash,'ret':(cash/100000-1)*100,'dd':maxdd*100,'n':len(trades),'win':100*sum(x>0 for x in trades)/len(trades) if trades else 0,'pf':gp/gl if gl else (99 if gp else 0)}

results=[]
for t in (66,70,74,78):
 for p in (2,3,4):
  for r in (.0035,.005):results.append(simulate(t,p,r))
results.sort(key=lambda x:(x['ret']-.65*x['dd']+min(x['pf'],3)*.2),reverse=True);best=results[0]
lines=['# BR-SMART Backtest','Trend %30 + relatif güç %25 + momentum %20 + para akışı %15 + kalite %10. Zayıf rejimde AL yok. TUPRS/savunma hariç, lookahead yok, maliyet dahil.','',f'EN IYI: skor {best["threshold"]}, pozisyon {best["maxpos"]}, risk %{best["risk"]*100:.2f}: **{best["ret"]:.2f}%**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, PF **{best["pf"]:.2f}**.','','|Skor|Pos|Risk|Getiri|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results:lines.append(f'|{x["threshold"]}|{x["maxpos"]}|{x["risk"]*100:.2f}%|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))