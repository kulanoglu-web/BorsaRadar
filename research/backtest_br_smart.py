# BR-SMART v3: keep entry stable, optimize exit/payoff asymmetry
import json
from pathlib import Path
import backtest_indicators as bi

def smart_score(s,i,breadth,rvmin=1.05):
    a=bi.data[s]
    if i<60:return None
    f=bi.feat(s,i);c=[r['c'] for r in a[:i]];close=c[-1];m=f['m']
    e20,e50=f['e20'],f['e50'];e20old=bi.b.ema(c[-55:-5],20)
    r3=close/c[-4]-1;r10=close/c[-11]-1
    if breadth<.42 or not(close>e20>e50 and e20>e20old):return None
    if r10<=0 or r3<-.005 or f['rv']<rvmin or f['cmf']<.02:return None
    if f['adx']<17 or m['trap'] or not(48<=f['rsi']<=73):return None
    trend=30*(.55+.20*min(1,max(0,(close/e20-1)/.035))+.25*min(1,max(0,f['slope']/.02)))
    strength=25*(.45*min(1,max(0,r3/.035))+.55*min(1,max(0,r10/.07)))
    momentum=20*(.60*(m['mac']>m['ms'])+.40*min(1,max(0,(f['rsi']-48)/20)))
    flow=15*(.55*min(1,max(0,(f['rv']-1)/.7))+.45*min(1,max(0,f['cmf']/.18)))
    quality=10*(.60*min(1,f['adx']/30)+.40*min(1,max(0,f['slope']/.02)))
    score=trend+strength+momentum+flow+quality-(6 if breadth<.50 else 0)
    return score,f

def simulate(threshold=78,maxpos=3,risk=.0025,rvmin=1.05,stopatr=1.25,trailatr=2.8,timecut=5):
    cash=100000.;pos={};trades=[];peak=cash;maxdd=0;cool={}
    for day in bi.dates:
        breadth=bi.breadth_cache.get(day,0)
        # exits
        for s in list(pos):
            a=bi.data[s];i=bi.bysym[s].get(day)
            if i is None:continue
            bar=a[i];p=pos[s];f=bi.feat(s,i);m=f['m'];p['high']=max(p['high'],bar['h']);p['age']+=1
            gain=p['high']/p['entry']-1;closeprev=a[i-1]['c'] if i>0 else p['entry']
            # Fast risk cut before thesis matures; never widen initial stop.
            stop=p['hard']
            # Once trade proves itself, switch from fixed stop to looser ATR/EMA trend trail.
            if gain>=.035: stop=max(stop,p['entry']*1.002,p['high']-trailatr*p['atr'])
            if gain>=.07: stop=max(stop,p['entry']*1.025,p['high']-(trailatr-.35)*p['atr'])
            if gain>=.12: stop=max(stop,p['entry']*1.065,p['high']-(trailatr-.65)*p['atr'])
            ex=reason=None
            if bar['l']<=stop:
                ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
            else:
                # Time stop: dead money/failed follow-through gets cut small.
                unreal=closeprev/p['entry']-1
                if p['age']>=timecut and unreal<.006 and gain<.025:
                    ex=bar['o'];reason='TIME'
                # Strong winners are held; only exit on real trend deterioration.
                elif gain>=.035:
                    if closeprev<f['e20'] and (f['cmf']<0 or m['mac']<m['ms']):
                        ex=bar['o'];reason='TREND'
                else:
                    z=smart_score(s,i,breadth,rvmin)
                    if z is None and p['age']>=3:
                        ex=bar['o'];reason='FAIL'
            if ex:
                cash+=p['qty']*ex*(1-bi.FEE);ret=(ex/p['entry']-1-2*bi.FEE)*100
                trades.append((ret,reason,p['age']));del pos[s];cool[s]=day
        # entries
        slots=maxpos-len(pos)
        if slots>0 and breadth>=.42:
            cand=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<60:continue
                if s in cool and day-cool[s]<10*86400:continue
                turn,vol,j=bi.quality(s,i)
                if turn<150_000_000 or vol<150_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.035<=gap<=.018):continue
                z=smart_score(s,i,breadth,rvmin)
                if not z:continue
                sc,f=z;dist=(a[i-1]['c']/f['e20']-1)/max(f['m']['atr']/a[i-1]['c'],.005)
                if dist>2.4:continue
                if sc>=threshold:cand.append((sc+min(4,(f['rv']-1)*4)+min(3,f['cmf']*15),s,i,f))
            cand.sort(reverse=True)
            for sc,s,i,f in cand[:slots]:
                px=bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.010);hard=px-max(stopatr*atr,px*.012)
                rc=100000*risk;qty=int(min(cash/(max(1,slots)*px*(1+bi.FEE)),rc/max(.01,px-hard)))
                if qty<=0:continue
                cash-=qty*px*(1+bi.FEE);pos[s]={'qty':qty,'entry':px,'high':px,'atr':atr,'hard':hard,'age':0};slots-=1
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['qty']*(bi.data[s][i]['c'] if i is not None else p['entry'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        px=bi.data[s][-1]['c'];cash+=p['qty']*px*(1-bi.FEE);trades.append(((px/p['entry']-1-2*bi.FEE)*100,'SON',p['age']))
    vals=[x[0] for x in trades];gp=sum(x for x in vals if x>0);gl=-sum(x for x in vals if x<0);wins=[x for x in vals if x>0];loss=[-x for x in vals if x<0]
    return {'threshold':threshold,'maxpos':maxpos,'risk':risk,'rvmin':rvmin,'stopatr':stopatr,'trailatr':trailatr,'timecut':timecut,'end':cash,'ret':(cash/100000-1)*100,'dd':maxdd*100,'n':len(vals),'win':100*len(wins)/len(vals) if vals else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgwin':sum(wins)/max(1,len(wins)),'avgloss':sum(loss)/max(1,len(loss)),'reasons':{k:sum(1 for x in trades if x[1]==k) for k in ('STOP','TIME','TREND','FAIL','SON')}}

results=[]
for t in (76,80):
 for p in (2,3):
  for st in (1.1,1.3):
   for tr in (2.6,3.0):
    for tc in (4,6):results.append(simulate(t,p,.0025,1.05,st,tr,tc))
results.sort(key=lambda x:(x['pf']>=1.1,x['ret']-.6*x['dd']+.45*min(2,x['pf'])-.15*abs(x['n']-50)/50),reverse=True);best=results[0]
lines=['# BR-SMART v3 Exit/Payoff Backtest','Giriş mantığı sabit; test odağı küçük zararı hızlı kesmek, kazananı trend bozulana kadar taşımak, 10 günlük tekrar-giriş beklemesi. TUPRS/savunma hariç, lookahead yok, maliyet dahil.','',f'EN IYI: skor {best["threshold"]}, pos {best["maxpos"]}, stop {best["stopatr"]:.1f} ATR, trail {best["trailatr"]:.1f} ATR, time {best["timecut"]}: **{best["ret"]:.2f}%**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, PF **{best["pf"]:.2f}**, ort kazanç **{best["avgwin"]:.2f}%**, ort kayıp **{best["avgloss"]:.2f}%**.','',f'Çıkışlar: {best["reasons"]}','','|Skor|Pos|StopATR|TrailATR|Time|Getiri|DD|N|Win|PF|AvgW|AvgL|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results[:16]:lines.append(f'|{x["threshold"]}|{x["maxpos"]}|{x["stopatr"]:.1f}|{x["trailatr"]:.1f}|{x["timecut"]}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgwin"]:.2f}%|{x["avgloss"]:.2f}%|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))