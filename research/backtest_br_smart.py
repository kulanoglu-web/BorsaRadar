# BR-SMART v4: early impulse / reversal entry; no 10-day-positive requirement
import json
from pathlib import Path
import backtest_indicators as bi

def smart_score(s,i,breadth,rvmin=.90):
    a=bi.data[s]
    if i<60:return None
    f=bi.feat(s,i); c=[r['c'] for r in a[:i]]; close=c[-1]; m=f['m']
    e20,e50=f['e20'],f['e50']; e5=bi.b.ema(c,5); e10=bi.b.ema(c,10)
    e5old=bi.b.ema(c[:-2],5); e10old=bi.b.ema(c[:-2],10)
    # Early impulse: acceleration matters, not being positive for 10 days.
    r1=close/c[-2]-1; r3=close/c[-4]-1; prev3=c[-2]/c[-5]-1
    accel=r3-prev3
    mac_up=m['mac']>m['ms']
    ema_turn=e5>e10 and (e5>e5old or e10>e10old)
    flow_turn=f['cmf']>-.02 and f['rv']>=rvmin
    if breadth<.38 or m['trap']: return None
    if not ema_turn: return None
    if not (mac_up or accel>.004): return None
    if not flow_turn: return None
    if f['rsi']>75 or f['rsi']<42: return None
    # Avoid chasing already-extended moves; allow fresh recovery around EMA20/EMA50.
    atrpct=max(m['atr']/close,.006)
    dist20=(close/e20-1)/atrpct
    if dist20>2.3: return None
    trend=24*(.45*(close>e20)+.30*(e20>e50)+.25*ema_turn)
    impulse=30*(.35*mac_up+.30*min(1,max(0,(accel+.004)/.025))+.20*min(1,max(0,(r1+.005)/.025))+.15*min(1,max(0,f['mom3']/3)))
    flow=22*(.55*min(1,max(0,(f['rv']-.8)/.9))+.45*min(1,max(0,(f['cmf']+.03)/.18)))
    quality=14*(.55*min(1,f['adx']/28)+.45*min(1,max(0,(f['slope']+.004)/.022)))
    regime=10*min(1,max(0,(breadth-.38)/.22))
    score=trend+impulse+flow+quality+regime
    return score,f,{'r1':r1,'r3':r3,'accel':accel,'dist20':dist20}

def simulate(threshold=68,maxpos=2,risk=.0025,rvmin=.90,stopatr=1.1,trailatr=2.6):
    cash=100000.;pos={};trades=[];peak=cash;maxdd=0;cool={}
    for day in bi.dates:
        breadth=bi.breadth_cache.get(day,0)
        for s in list(pos):
            a=bi.data[s];i=bi.bysym[s].get(day)
            if i is None:continue
            bar=a[i];p=pos[s];f=bi.feat(s,i);m=f['m'];p['high']=max(p['high'],bar['h']);p['age']+=1
            gain=p['high']/p['entry']-1; stop=p['hard']
            if gain>=.035:stop=max(stop,p['entry']*1.002,p['high']-trailatr*p['atr'])
            if gain>=.07:stop=max(stop,p['entry']*1.025,p['high']-(trailatr-.35)*p['atr'])
            if gain>=.12:stop=max(stop,p['entry']*1.065,p['high']-(trailatr-.65)*p['atr'])
            ex=reason=None
            if bar['l']<=stop: ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
            else:
                closeprev=a[i-1]['c']; unreal=closeprev/p['entry']-1
                # Failed impulse is cut; winners are allowed to run.
                if p['age']>=4 and unreal<-.004 and gain<.02: ex=bar['o'];reason='FAIL'
                elif gain>=.035 and closeprev<f['e20'] and (f['cmf']<0 or m['mac']<m['ms']): ex=bar['o'];reason='TREND'
            if ex:
                cash+=p['qty']*ex*(1-bi.FEE);trades.append(((ex/p['entry']-1-2*bi.FEE)*100,reason));del pos[s];cool[s]=day
        slots=maxpos-len(pos)
        if slots>0 and breadth>=.38:
            cand=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<60:continue
                if s in cool and day-cool[s]<5*86400:continue
                turn,vol,j=bi.quality(s,i)
                if turn<120_000_000 or vol<120_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.035<=gap<=.022):continue
                z=smart_score(s,i,breadth,rvmin)
                if not z:continue
                sc,f,x=z
                if sc>=threshold:cand.append((sc+min(4,max(0,x['accel'])*120)+min(3,max(0,f['cmf'])*15),s,i,f))
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
        px=bi.data[s][-1]['c'];cash+=p['qty']*px*(1-bi.FEE);trades.append(((px/p['entry']-1-2*bi.FEE)*100,'SON'))
    vals=[x[0] for x in trades];gp=sum(x for x in vals if x>0);gl=-sum(x for x in vals if x<0);wins=[x for x in vals if x>0];loss=[-x for x in vals if x<0]
    return {'threshold':threshold,'maxpos':maxpos,'rvmin':rvmin,'ret':(cash/100000-1)*100,'end':cash,'dd':maxdd*100,'n':len(vals),'win':100*len(wins)/len(vals) if vals else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgwin':sum(wins)/max(1,len(wins)),'avgloss':sum(loss)/max(1,len(loss)),'reasons':{k:sum(1 for x in trades if x[1]==k) for k in ('STOP','FAIL','TREND','SON')}}

results=[]
for t in (62,66,70,74):
 for p in (2,3):
  for rv in (.85,.95,1.05): results.append(simulate(t,p,.0025,rv,1.1,2.6))
results.sort(key=lambda x:(x['pf']>=1.1,x['ret']-.6*x['dd']+.45*min(2,x['pf'])-.12*abs(x['n']-55)/55),reverse=True);best=results[0]
lines=['# BR-SMART v4 Early Impulse Backtest','10 gün pozitif şartı YOK. Giriş: erken EMA dönüşü + MACD/ivme hızlanması + para akışı + piyasa rejimi; aşırı uzamış hareket kovalanmaz. TUPRS/savunma hariç, lookahead yok, maliyet dahil.','',f'EN IYI: skor {best["threshold"]}, pos {best["maxpos"]}, RVOL {best["rvmin"]:.2f}: **{best["ret"]:.2f}%**, 100k -> **{best["end"]:.0f} TL**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, PF **{best["pf"]:.2f}**, ort kazanç **{best["avgwin"]:.2f}%**, ort kayıp **{best["avgloss"]:.2f}%**.','',f'Çıkışlar: {best["reasons"]}','','|Skor|Pos|RVOL|Getiri|DD|N|Win|PF|AvgW|AvgL|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results[:16]:lines.append(f'|{x["threshold"]}|{x["maxpos"]}|{x["rvmin"]:.2f}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgwin"]:.2f}%|{x["avgloss"]:.2f}%|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))