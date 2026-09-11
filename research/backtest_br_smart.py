# BR-SMART v2: selective institutional-style model
import json
from pathlib import Path
import backtest_indicators as bi

def smart_score(s,i,breadth):
    a=bi.data[s]
    if i<60:return None
    f=bi.feat(s,i);c=[r['c'] for r in a[:i]];close=c[-1];m=f['m']
    e20,e50=f['e20'],f['e50'];e20old=bi.b.ema(c[-55:-5],20)
    r3=close/c[-4]-1;r10=close/c[-11]-1
    # Hard gates first: no averaging weak signals into a BUY.
    if breadth<.42:return None
    if not(close>e20>e50 and e20>e20old):return None
    if r10<=0 or r3<-.005:return None
    if f['rv']<1.05 or f['cmf']<.02:return None
    if f['adx']<17 or m['trap']:return None
    if not(48<=f['rsi']<=73):return None
    # Independent dimensions only.
    trend=30*(.55+.20*min(1,max(0,(close/e20-1)/.035))+.25*min(1,max(0,f['slope']/.02)))
    strength=25*(.45*min(1,max(0,r3/.035))+.55*min(1,max(0,r10/.07)))
    momentum=20*(.60*(m['mac']>m['ms'])+.40*min(1,max(0,(f['rsi']-48)/20)))
    flow=15*(.55*min(1,max(0,(f['rv']-1)/.7))+.45*min(1,max(0,f['cmf']/.18)))
    quality=10*(.60*min(1,f['adx']/30)+.40*min(1,max(0,f['slope']/.02)))
    score=trend+strength+momentum+flow+quality
    if breadth<.50:score-=6
    return score,f

def simulate(threshold=76,maxpos=3,risk=.0035,rvmin=1.05):
    dates=bi.dates;by=bi.bysym;cash=100000.;pos={};trades=[];peak=cash;maxdd=0;cool={}
    for day in dates:
        breadth=bi.breadth_cache.get(day,0)
        for s in list(pos):
            a=bi.data[s];idx=by[s].get(day)
            if idx is None:continue
            bar=a[idx];p=pos[s];p['high']=max(p['high'],bar['h']);gain=p['high']/p['entry']-1
            # Losses cut quicker; winners get more room once trend pays.
            stop=max(p['hard'],p['high']-2.4*p['atr'] if gain>=.04 else p['hard'])
            if gain>=.05:stop=max(stop,p['entry']*1.012)
            if gain>=.09:stop=max(stop,p['high']-1.8*p['atr'],p['entry']*1.045)
            ex=None
            if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop
            else:
                z=smart_score(s,idx,breadth)
                if z is None or z[0]<58:ex=bar['o']
            if ex:
                cash+=p['qty']*ex*(1-bi.FEE);trades.append((ex/p['entry']-1-2*bi.FEE)*100);del pos[s];cool[s]=day
        slots=maxpos-len(pos)
        if slots>0 and breadth>=.42:
            cand=[]
            for s,a in bi.data.items():
                if s in pos:continue
                idx=by[s].get(day)
                if idx is None or idx<60:continue
                if s in cool and day-cool[s]<5*86400:continue
                turn,vol,j=bi.quality(s,idx)
                if turn<150_000_000 or vol<150_000 or j>=2:continue
                gap=a[idx]['o']/a[idx-1]['c']-1
                if a[idx]['o']<5 or not(-.035<=gap<=.018):continue
                z=smart_score(s,idx,breadth)
                if not z:continue
                sc,f=z
                if f['rv']<rvmin:continue
                # Avoid buying extended names; institutional-style pullback/controlled breakout zone.
                dist=(a[idx-1]['c']/f['e20']-1)/(max(f['m']['atr']/a[idx-1]['c'],.005))
                if dist>2.6:continue
                if sc>=threshold:cand.append((sc+min(4,(f['rv']-1)*4)+min(3,f['cmf']*15),s,idx,f))
            cand.sort(reverse=True)
            for sc,s,idx,f in cand[:slots]:
                price=bi.data[s][idx]['o'];atr=max(f['m']['atr'],price*.010);hard=price-max(1.55*atr,price*.016)
                riskcash=100000*risk;qty=int(min(cash/(max(1,slots)*price*(1+bi.FEE)),riskcash/max(.01,price-hard)))
                if qty<=0:continue
                cash-=qty*price*(1+bi.FEE);pos[s]={'qty':qty,'entry':price,'high':price,'atr':atr,'hard':hard};slots-=1
        eq=cash
        for s,p in pos.items():
            idx=by[s].get(day);eq+=p['qty']*(bi.data[s][idx]['c'] if idx is not None else p['entry'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        px=bi.data[s][-1]['c'];cash+=p['qty']*px*(1-bi.FEE);trades.append((px/p['entry']-1-2*bi.FEE)*100)
    gp=sum(x for x in trades if x>0);gl=-sum(x for x in trades if x<0)
    aw=gp/max(1,sum(x>0 for x in trades));al=gl/max(1,sum(x<0 for x in trades))
    return {'threshold':threshold,'maxpos':maxpos,'risk':risk,'rvmin':rvmin,'end':cash,'ret':(cash/100000-1)*100,'dd':maxdd*100,'n':len(trades),'win':100*sum(x>0 for x in trades)/len(trades) if trades else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgwin':aw,'avgloss':al}

results=[]
for t in (72,76,80):
 for p in (2,3):
  for r in (.0025,.0035):
   for rv in (1.05,1.15):results.append(simulate(t,p,r,rv))
results.sort(key=lambda x:(x['pf']>=1.2,x['ret']-.55*x['dd']+min(x['pf'],2)*.35-min(1,abs(x['n']-45)/80)),reverse=True);best=results[0]
lines=['# BR-SMART v2 Selective Backtest','Hard gate: güçlü trend + pozitif 10g güç + hacim/CMF teyidi + ADX + piyasa breadth. Momentum yalnız filtre. TUPRS/savunma hariç; lookahead yok; maliyet dahil.','',f'EN IYI: skor {best["threshold"]}, pos {best["maxpos"]}, risk %{best["risk"]*100:.2f}, RVOL {best["rvmin"]:.2f}: **{best["ret"]:.2f}%**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, PF **{best["pf"]:.2f}**, ort kazanç **{best["avgwin"]:.2f}%**, ort kayıp **{best["avgloss"]:.2f}%**.','','|Skor|Pos|Risk|RVOL|Getiri|DD|N|Win|PF|AvgW|AvgL|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results:lines.append(f'|{x["threshold"]}|{x["maxpos"]}|{x["risk"]*100:.2f}%|{x["rvmin"]:.2f}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgwin"]:.2f}%|{x["avgloss"]:.2f}%|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))