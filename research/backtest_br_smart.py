# BR-SMART v8: early-entry family diagnostic; v3-style payoff kept stable
import json, math
from pathlib import Path
import backtest_indicators as bi

START=100000.; MAXPOS=2; RISK=.0025

def stats20(a,i):
    z=a[max(0,i-20):i]; closes=[x['c'] for x in z]; highs=[x['h'] for x in z]; lows=[x['l'] for x in z]
    mean=sum(closes)/max(1,len(closes)); var=sum((x-mean)**2 for x in closes)/max(1,len(closes)); sd=var**.5
    bw=sd/mean if mean else 0
    return bw,max(highs),min(lows)

def entry_signal(s,i,breadth,mode):
    if i<65:return None
    a=bi.data[s];f=bi.feat(s,i);p=bi.feat(s,i-1);m=f['m'];pm=p['m'];c=[x['c'] for x in a[:i]];close=c[-1]
    if breadth<.40 or m['trap'] or not(44<=f['rsi']<=74):return None
    turn,vol,j=bi.quality(s,i)
    if turn<120_000_000 or vol<120_000 or j>=2:return None
    bw,h20,l20=stats20(a,i); bwprev=stats20(a,i-5)[0] if i>=70 else bw
    hist=m['mac']-m['ms']; phist=pm['mac']-pm['ms']; mac_turn=hist>phist
    volburst=f['rv']>=1.15 and f['cmf']>=0
    squeeze=bw<.055 and bw<=bwprev*.92
    breakout=close>=h20*.985
    ema_reclaim=close>f['e20'] and c[-2]<=p['e20']*1.01 and f['slope']>-.004
    accel=f['mom3']>p['mom3']+.003 or f['acc']>0
    trend=f['e20']>f['e50'] or f['slope']>0
    if mode=='VOL': ok=volburst and mac_turn and trend
    elif mode=='SQUEEZE': ok=squeeze and (breakout or ema_reclaim) and mac_turn
    elif mode=='RECLAIM': ok=ema_reclaim and accel and f['cmf']>=-.01
    elif mode=='BREAK': ok=breakout and volburst and accel
    else: ok=(volburst+mac_turn+squeeze+ema_reclaim+accel)>=3 and trend
    if not ok:return None
    atr=max(m['atr'],close*.01); ext=(close/f['e20']-1)/max(atr/close,.006)
    if ext>2.4:return None
    score=30*trend+20*mac_turn+18*volburst+16*accel+10*ema_reclaim+8*squeeze+8*breakout+min(6,max(0,(breadth-.4)*30))
    return score,f,{'bw':bw,'volburst':volburst,'squeeze':squeeze,'breakout':breakout,'reclaim':ema_reclaim}

def simulate(mode,threshold):
    cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in bi.dates:
        breadth=bi.breadth_cache.get(day,0)
        for s in list(pos):
            i=bi.bysym[s].get(day)
            if i is None:continue
            a=bi.data[s];bar=a[i];p=pos[s];f=bi.feat(s,i);m=f['m'];p['hi']=max(p['hi'],bar['h']);p['age']+=1;gain=p['hi']/p['en']-1
            stop=p['hard']
            if gain>=.035:stop=max(stop,p['en']*1.002,p['hi']-2.6*p['atr'])
            if gain>=.07:stop=max(stop,p['en']*1.025,p['hi']-2.25*p['atr'])
            if gain>=.12:stop=max(stop,p['en']*1.065,p['hi']-1.95*p['atr'])
            ex=reason=None
            if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
            else:
                cp=a[i-1]['c'];unreal=cp/p['en']-1
                if p['age']>=4 and unreal<-.006 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=.035 and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
            if ex:
                proceeds=p['q']*ex*(1-bi.FEE);cash+=proceeds;pnl=proceeds-p['cost'];tr.append((pnl,100*pnl/p['cost'],reason,p['age']));del pos[s];cool[s]=day
        slots=MAXPOS-len(pos)
        if slots>0 and breadth>=.40:
            ca=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<65 or (s in cool and day-cool[s]<5*86400):continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.035<=gap<=.02):continue
                z=entry_signal(s,i,breadth,mode)
                if not z:continue
                sc,f,x=z
                if sc>=threshold:ca.append((sc+min(5,max(0,f['rv']-1)*3)+min(3,max(0,f['cmf'])*15),s,i,f))
            ca.sort(reverse=True)
            for sc,s,i,f in ca[:slots]:
                px=bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(1.1*atr,px*.012);rc=START*RISK
                q=int(min(cash/(max(1,slots)*px*(1+bi.FEE)),rc/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+bi.FEE);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        px=bi.data[s][-1]['c'];pro=p['q']*px*(1-bi.FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],'SON',p['age']))
    gp=sum(x[0] for x in tr if x[0]>0);gl=-sum(x[0] for x in tr if x[0]<0);rets=[x[1] for x in tr];wins=[x for x in rets if x>0];loss=[-x for x in rets if x<0]
    return {'mode':mode,'th':threshold,'ret':(cash/START-1)*100,'end':cash,'dd':dd*100,'n':len(tr),'win':100*len(wins)/len(rets) if rets else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgw':sum(wins)/max(1,len(wins)),'avgl':sum(loss)/max(1,len(loss)),'hold':sum(x[3] for x in tr)/max(1,len(tr)),'reasons':{k:sum(1 for x in tr if x[2]==k) for k in ('STOP','FAIL','TREND','SON')}}

rows=[]
for mode in ('VOL','SQUEEZE','RECLAIM','BREAK','COMBO'):
 for th in (48,56,64,72): rows.append(simulate(mode,th))
rows.sort(key=lambda x:(x['n']>=25,x['pf']>=1,x['ret']-.55*x['dd']+.5*min(2,x['pf'])-.15*abs(x['n']-55)/55),reverse=True);best=rows[0]
lines=['# BR-SMART v8 Early Entry Diagnostic','Beş giriş ailesi ayrı test edildi: hacim patlaması, volatilite sıkışması, EMA geri kazanımı, kırılım ve kombine erken-sinyal. TUPRS/savunma hariç; lookahead yok; maliyet dahil; PF TL bazlı.','',f'EN IYI: **{best["mode"]}**, eşik {best["th"]}: **{best["ret"]:.2f}%**, 100k -> **{best["end"]:.0f} TL**, DD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, TL-PF **{best["pf"]:.2f}**, AvgW **{best["avgw"]:.2f}%**, AvgL **{best["avgl"]:.2f}%**, Hold **{best["hold"]:.1f}**.','',f'Çıkışlar: {best["reasons"]}','','|Mode|Th|Getiri|DD|N|Win|TL-PF|AvgW|AvgL|Hold|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in rows:lines.append(f'|{x["mode"]}|{x["th"]}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgw"]:.2f}%|{x["avgl"]:.2f}%|{x["hold"]:.1f}|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':rows},indent=2),encoding='utf-8');print('\n'.join(lines))