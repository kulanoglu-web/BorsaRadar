# BR-SMART v5: v3 exit engine + true relative strength + fresh impulse + reward/risk
import json
from pathlib import Path
import backtest_indicators as bi

_rank_cache={}
def market_rank(day):
    if day in _rank_cache:return _rank_cache[day]
    vals=[]
    for s,a in bi.data.items():
        i=bi.bysym[s].get(day)
        if i is None or i<25:continue
        c=[r['c'] for r in a[:i]]
        if len(c)<21:continue
        r3=c[-1]/c[-4]-1
        r5=c[-1]/c[-6]-1
        r20=c[-1]/c[-21]-1
        vals.append((s,.45*r3+.35*r5+.20*r20))
    vals.sort(key=lambda x:x[1])
    n=max(1,len(vals)-1)
    out={s:k/n for k,(s,_) in enumerate(vals)}
    _rank_cache[day]=out
    return out

def smart_score(s,i,day,breadth,rvmin=1.0,rsmin=.70,rrmin=1.6,stopatr=1.1):
    a=bi.data[s]
    if i<60:return None
    f=bi.feat(s,i); prev=bi.feat(s,i-1); c=[r['c'] for r in a[:i]]; close=c[-1]; m=f['m']; pm=prev['m']
    e20,e50=f['e20'],f['e50'];e20old=bi.b.ema(c[-55:-5],20)
    # No fixed '10 days positive' rule. Use market-relative rank instead.
    rs=market_rank(day).get(s,0)
    hist=m['mac']-m['ms']; phist=pm['mac']-pm['ms']
    fresh_impulse=(hist>phist and hist>-.002*close) or (f['mom3']>prev['mom3']+.12)
    trend_ok=close>e20 and e20>=e20old and (e20>e50 or f['slope']>0)
    flow_ok=f['rv']>=rvmin and f['cmf']>=0
    if breadth<.40 or m['trap'] or not trend_ok or not fresh_impulse or not flow_ok:return None
    if rs<rsmin or not(45<=f['rsi']<=73):return None
    atr=max(m['atr'],close*.010)
    # Structure-based expected target: prior 20d high; on breakout project part of prior range.
    highs=[r['h'] for r in a[max(0,i-20):i]];lows=[r['l'] for r in a[max(0,i-20):i]]
    h20=max(highs);l20=min(lows);risk=max(stopatr*atr,close*.012)
    target=h20
    if close>=h20*.995:target=close+max(2.0*atr,.45*(h20-l20))
    rr=max(0,target-close)/risk
    if rr<rrmin:return None
    dist=(close/e20-1)/max(atr/close,.006)
    if dist>2.5:return None
    trend=28*(.45*(close>e20)+.30*(e20>e50)+.25*min(1,max(0,f['slope']/.018)))
    rel=27*min(1,max(0,(rs-.50)/.40))
    impulse=20*(.55*min(1,max(0,(hist-phist)/(close*.006)))+.45*min(1,max(0,(f['mom3']-prev['mom3']+.2)/1.8)))
    flow=15*(.55*min(1,max(0,(f['rv']-.85)/.7))+.45*min(1,max(0,f['cmf']/.16)))
    quality=10*(.55*min(1,f['adx']/30)+.45*min(1,max(0,(rr-1.4)/1.6)))
    return trend+rel+impulse+flow+quality,f,{'rs':rs,'rr':rr,'hist':hist,'phist':phist}

def simulate(threshold=74,maxpos=2,risk=.0025,rvmin=1.0,rsmin=.70,rrmin=1.6,stopatr=1.1,trailatr=2.6):
    cash=100000.;pos={};trades=[];peak=cash;maxdd=0;cool={}
    for day in bi.dates:
        breadth=bi.breadth_cache.get(day,0)
        # v3-style exits: cut losers, let proven winners breathe.
        for s in list(pos):
            a=bi.data[s];i=bi.bysym[s].get(day)
            if i is None:continue
            bar=a[i];p=pos[s];f=bi.feat(s,i);m=f['m'];p['high']=max(p['high'],bar['h']);p['age']+=1
            gain=p['high']/p['entry']-1;stop=p['hard']
            if gain>=.035:stop=max(stop,p['entry']*1.002,p['high']-trailatr*p['atr'])
            if gain>=.07:stop=max(stop,p['entry']*1.025,p['high']-(trailatr-.35)*p['atr'])
            if gain>=.12:stop=max(stop,p['entry']*1.065,p['high']-(trailatr-.65)*p['atr'])
            ex=reason=None
            if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
            else:
                closeprev=a[i-1]['c'];unreal=closeprev/p['entry']-1
                if p['age']>=5 and unreal<.006 and gain<.025:ex=bar['o'];reason='TIME'
                elif gain>=.035 and closeprev<f['e20'] and (f['cmf']<0 or m['mac']<m['ms']):ex=bar['o'];reason='TREND'
                elif p['age']>=3 and unreal<-.006:ex=bar['o'];reason='FAIL'
            if ex:
                cash+=p['qty']*ex*(1-bi.FEE);trades.append(((ex/p['entry']-1-2*bi.FEE)*100,reason));del pos[s];cool[s]=day
        slots=maxpos-len(pos)
        if slots>0 and breadth>=.40:
            cand=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<60:continue
                if s in cool and day-cool[s]<7*86400:continue
                turn,vol,j=bi.quality(s,i)
                if turn<150_000_000 or vol<150_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.035<=gap<=.020):continue
                z=smart_score(s,i,day,breadth,rvmin,rsmin,rrmin,stopatr)
                if not z:continue
                sc,f,x=z
                if sc>=threshold:cand.append((sc+6*x['rs']+min(4,x['rr']),s,i,f,x))
            cand.sort(reverse=True)
            for sc,s,i,f,x in cand[:slots]:
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
    return {'threshold':threshold,'maxpos':maxpos,'rvmin':rvmin,'rsmin':rsmin,'rrmin':rrmin,'ret':(cash/100000-1)*100,'end':cash,'dd':maxdd*100,'n':len(vals),'win':100*len(wins)/len(vals) if vals else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgwin':sum(wins)/max(1,len(wins)),'avgloss':sum(loss)/max(1,len(loss)),'reasons':{k:sum(1 for x in trades if x[1]==k) for k in ('STOP','TIME','TREND','FAIL','SON')}}

results=[]
for t in (70,74,78):
 for rs in (.65,.70,.75,.80):
  for rr in (1.4,1.7,2.0):
   results.append(simulate(t,2,.0025,1.0,rs,rr,1.1,2.6))
results.sort(key=lambda x:(x['pf']>=1.1,x['ret']-.60*x['dd']+.45*min(2,x['pf'])-.12*abs(x['n']-50)/50),reverse=True);best=results[0]
lines=['# BR-SMART v5 Relative Strength + Impulse + RR','10 gün pozitif şartı YOK. v3 çıkış motoru korundu. Giriş: BIST evrenine göre gerçek relatif güç yüzdeliği + yeni oluşan ivme + hacim/CMF + yapısal ödül/risk. TUPRS/savunma hariç, lookahead yok, maliyet dahil.','',f'EN IYI: skor {best["threshold"]}, RS>={best["rsmin"]:.0%}, RR>={best["rrmin"]:.1f}: **{best["ret"]:.2f}%**, 100k -> **{best["end"]:.0f} TL**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, PF **{best["pf"]:.2f}**, ort kazanç **{best["avgwin"]:.2f}%**, ort kayıp **{best["avgloss"]:.2f}%**.','',f'Çıkışlar: {best["reasons"]}','','|Skor|RS|RR|Getiri|DD|N|Win|PF|AvgW|AvgL|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results[:18]:lines.append(f'|{x["threshold"]}|{x["rsmin"]:.0%}|{x["rrmin"]:.1f}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgwin"]:.2f}%|{x["avgloss"]:.2f}%|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))