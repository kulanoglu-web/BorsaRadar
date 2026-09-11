# BR-SMART v7: freeze v3 entry; optimize adaptive stop/profit capture
import json
from pathlib import Path
import backtest_indicators as bi

def smart_score(s,i,breadth,rvmin=1.05):
    a=bi.data[s]
    if i<60:return None
    f=bi.feat(s,i);c=[r['c'] for r in a[:i]];close=c[-1];m=f['m'];e20,e50=f['e20'],f['e50'];e20old=bi.b.ema(c[-55:-5],20)
    r3=close/c[-4]-1;r10=close/c[-11]-1
    if breadth<.42 or not(close>e20>e50 and e20>e20old):return None
    if r10<=0 or r3<-.005 or f['rv']<rvmin or f['cmf']<.02:return None
    if f['adx']<17 or m['trap'] or not(48<=f['rsi']<=73):return None
    trend=30*(.55+.20*min(1,max(0,(close/e20-1)/.035))+.25*min(1,max(0,f['slope']/.02)))
    strength=25*(.45*min(1,max(0,r3/.035))+.55*min(1,max(0,r10/.07)))
    momentum=20*(.60*(m['mac']>m['ms'])+.40*min(1,max(0,(f['rsi']-48)/20)))
    flow=15*(.55*min(1,max(0,(f['rv']-1)/.7))+.45*min(1,max(0,f['cmf']/.18)))
    quality=10*(.60*min(1,f['adx']/30)+.40*min(1,max(0,f['slope']/.02)))
    return trend+strength+momentum+flow+quality-(6 if breadth<.50 else 0),f

def simulate(stopatr=1.0,be_at=.025,trail_start=.045,trailatr=2.8,lock1=.018,lock2=.055):
    threshold=80;maxpos=2;risk=.0025;rvmin=1.05
    cash=100000.;pos={};trades=[];peak=cash;maxdd=0;cool={}
    for day in bi.dates:
        breadth=bi.breadth_cache.get(day,0)
        for s in list(pos):
            a=bi.data[s];i=bi.bysym[s].get(day)
            if i is None:continue
            bar=a[i];p=pos[s];f=bi.feat(s,i);m=f['m'];p['high']=max(p['high'],bar['h']);p['age']+=1
            gain=p['high']/p['entry']-1;stop=p['hard']
            # Adaptive payoff: don't choke early; once proven, progressively protect profit.
            if gain>=be_at:stop=max(stop,p['entry']*1.001)
            if gain>=trail_start:stop=max(stop,p['high']-trailatr*p['atr'])
            if gain>=.075:stop=max(stop,p['entry']*(1+lock1),p['high']-(trailatr-.25)*p['atr'])
            if gain>=.12:stop=max(stop,p['entry']*(1+lock2),p['high']-(trailatr-.55)*p['atr'])
            ex=reason=None
            if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
            else:
                cp=a[i-1]['c'];unreal=cp/p['entry']-1
                # thesis failure only; no arbitrary time exit
                if p['age']>=3 and unreal<-.010 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=trail_start and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
            if ex:
                proceeds=p['qty']*ex*(1-bi.FEE);cash+=proceeds
                pnl=proceeds-p['cost'];ret=pnl/p['cost']*100
                trades.append((ret,reason,pnl,p['age']));del pos[s];cool[s]=day
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
                if dist>2.4 or sc<threshold:continue
                cand.append((sc+min(4,(f['rv']-1)*4)+min(3,f['cmf']*15),s,i,f))
            cand.sort(reverse=True)
            for sc,s,i,f in cand[:slots]:
                px=bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.010);hard=px-max(stopatr*atr,px*.010)
                rc=100000*risk;qty=int(min(cash/(max(1,slots)*px*(1+bi.FEE)),rc/max(.01,px-hard)))
                if qty<=0:continue
                cost=qty*px*(1+bi.FEE);cash-=cost;pos[s]={'qty':qty,'entry':px,'high':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['qty']*(bi.data[s][i]['c'] if i is not None else p['entry'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        px=bi.data[s][-1]['c'];proceeds=p['qty']*px*(1-bi.FEE);cash+=proceeds;pnl=proceeds-p['cost'];trades.append((pnl/p['cost']*100,'SON',pnl,p['age']))
    rets=[x[0] for x in trades];pnls=[x[2] for x in trades];wins=[x for x in rets if x>0];loss=[-x for x in rets if x<0]
    gp=sum(x for x in pnls if x>0);gl=-sum(x for x in pnls if x<0);pf=gp/gl if gl else (99 if gp else 0)
    return {'stopatr':stopatr,'be':be_at,'trailstart':trail_start,'trailatr':trailatr,'lock1':lock1,'lock2':lock2,'ret':(cash/100000-1)*100,'end':cash,'dd':maxdd*100,'n':len(rets),'win':100*len(wins)/len(rets) if rets else 0,'pf':pf,'avgwin':sum(wins)/max(1,len(wins)),'avgloss':sum(loss)/max(1,len(loss)),'hold':sum(x[3] for x in trades)/max(1,len(trades)),'reasons':{k:sum(1 for x in trades if x[1]==k) for k in ('STOP','FAIL','TREND','SON')}}

results=[]
for st in (.85,1.0,1.15):
 for be in (.02,.03):
  for ts in (.04,.05):
   for tr in (2.6,3.0,3.4):results.append(simulate(st,be,ts,tr,.018,.055))
results.sort(key=lambda x:(x['n']>=35,x['pf']>=1,x['ret']-.55*x['dd']+.5*min(2,x['pf'])),reverse=True);best=results[0]
lines=['# BR-SMART v7 Adaptive Payoff','v3 girişleri sabit. Yalnızca stop/kâr taşıma test edildi. PF gerçek TL işlem kâr/zararıyla hesaplandı. TUPRS/savunma hariç; lookahead yok; maliyet dahil.','',f'EN IYI: stop {best["stopatr"]:.2f} ATR, BE {best["be"]:.1%}, trail başlangıç {best["trailstart"]:.1%}, trail {best["trailatr"]:.1f} ATR: **{best["ret"]:.2f}%**, 100k -> **{best["end"]:.0f} TL**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, TL-PF **{best["pf"]:.2f}**, AvgW **{best["avgwin"]:.2f}%**, AvgL **{best["avgloss"]:.2f}%**, ort tutuş **{best["hold"]:.1f} gün**.','',f'Çıkışlar: {best["reasons"]}','','|Stop|BE|TrailStart|TrailATR|Getiri|DD|N|Win|TL-PF|AvgW|AvgL|Hold|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results[:18]:lines.append(f'|{x["stopatr"]:.2f}|{x["be"]:.1%}|{x["trailstart"]:.1%}|{x["trailatr"]:.1f}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgwin"]:.2f}%|{x["avgloss"]:.2f}%|{x["hold"]:.1f}|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))