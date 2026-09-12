# BR-SMART v12: fixed ignition + breadth acceleration regime overlay
import json
from pathlib import Path
import backtest_indicators as bi
START=100000.;FEE=bi.FEE
DATES=bi.dates;DPOS={d:i for i,d in enumerate(DATES)}

def br_state(day):
    i=DPOS.get(day,0);br=bi.breadth_cache.get(day,0)
    prev=[bi.breadth_cache.get(DATES[j],br) for j in range(max(0,i-3),i)]
    avg=sum(prev)/len(prev) if prev else br
    delta=br-avg
    # Strong: broad participation. Recovery: breadth is improving fast enough.
    strong=br>=.54; recovery=br>=.44 and delta>=.025
    weak=br<.44 or (br<.52 and delta<-.035)
    return br,delta,strong,recovery,weak

def signal(s,i,day):
    if i<65:return None
    br,bd,strong,recovery,weak=br_state(day)
    if weak or not(strong or recovery):return None
    a=bi.data[s];f=bi.feat(s,i);p=bi.feat(s,i-1);m=f['m'];pm=p['m'];bar=a[i-1]
    rng=max(.001,bar['h']-bar['l']);cp=(bar['c']-bar['l'])/rng
    if m['trap'] or f['rv']<1.20 or f['cmf']<-.02 or cp<.50:return None
    if not(45<=f['rsi']<=70) or not(16<=f['adx']<=38):return None
    hist=m['mac']-m['ms'];phist=pm['mac']-pm['ms'];dh=hist-phist
    if dh<=0:return None
    close=bar['c'];atr=max(m['atr'],close*.01);dist=(close/f['e20']-1)/max(atr/close,.006)
    if dist<-.25 or dist>1.8:return None
    accel=max(-.02,min(.08,f['acc']));dhn=max(0,min(1,dh/max(close*.006,.01)));rvn=max(0,min(1,(f['rv']-1)/1.1));accn=max(0,min(1,(accel+.005)/.05));adxq=max(0,1-abs(f['adx']-27)/15);extq=max(0,1-max(0,dist-.6)/1.4)
    score=36*dhn+20*rvn+16*accn+10*adxq+8*extq+10*max(0,min(1,(bd+.02)/.10))
    return score,f,{'strong':strong,'recovery':recovery,'bd':bd}

def sim(days):
    ds=[d for d in days if d in bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0,'avgw':0,'avgl':0,'stop':0}
    last=ds[-1];cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in ds:
        br,bd,strong,recovery,weak=br_state(day)
        for s in list(pos):
            i=bi.bysym[s].get(day)
            if i is None:continue
            a=bi.data[s];bar=a[i];p=pos[s];f=bi.feat(s,i);m=f['m'];p['hi']=max(p['hi'],bar['h']);p['age']+=1;gain=p['hi']/p['en']-1;stop=p['hard']
            if gain>=.03:stop=max(stop,p['en']*1.001)
            if gain>=.05:stop=max(stop,p['hi']-2.8*p['atr'])
            if gain>=.08:stop=max(stop,p['en']*1.025,p['hi']-2.4*p['atr'])
            if gain>=.13:stop=max(stop,p['en']*1.07,p['hi']-2.0*p['atr'])
            ex=reason=None
            if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
            else:
                cp=a[i-1]['c'];un=cp/p['en']-1
                if weak and p['age']>=2 and un<.015:ex=bar['o'];reason='REGIME'
                elif p['age']>=4 and un<-.007 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=.05 and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
            if ex:
                pro=p['q']*ex*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],reason,p['age']));del pos[s];cool[s]=day
        maxpos=2 if strong else 1
        slots=maxpos-len(pos)
        if slots>0 and not weak and (strong or recovery):
            ca=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<65 or (s in cool and day-cool[s]<4*86400):continue
                turn,vol,j=bi.quality(s,i)
                if turn<120_000_000 or vol<120_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.03<=gap<=.012):continue
                z=signal(s,i,day)
                if z:ca.append((z[0],s,i,z[1],z[2]))
            ca.sort(reverse=True)
            for sc,s,i,f,x in ca[:slots]:
                px=bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(1.15*atr,px*.012);risk=.0022 if strong else .0013
                q=int(min(cash/(max(1,slots)*px*(1+FEE)),START*risk/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+FEE);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        i=bi.bysym[s].get(last)
        if i is None:continue
        px=bi.data[s][i]['c'];pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],'SON',p['age']))
    gp=sum(x[0] for x in tr if x[0]>0);gl=-sum(x[0] for x in tr if x[0]<0);rets=[x[1] for x in tr];wins=[x for x in rets if x>0];loss=[-x for x in rets if x<0]
    return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*len(wins)/len(rets) if rets else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgw':sum(wins)/max(1,len(wins)),'avgl':sum(loss)/max(1,len(loss)),'stop':sum(x[2]=='STOP' for x in tr),'regime':sum(x[2]=='REGIME' for x in tr)}

chunks=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)]
rows=[sim(ch) for ch in chunks];active=[r for r in rows if r['n']]
summary={'chunks':len(rows),'avg':sum(r['ret'] for r in rows)/len(rows),'worst':min(r['ret'] for r in rows),'positive':sum(r['ret']>0 for r in rows),'trades':sum(r['n'] for r in rows),'avgdd':sum(r['dd'] for r in rows)/len(rows),'avgpf':sum(min(5,r['pf']) for r in active)/len(active) if active else 0,'full':sim(DATES)}
lines=['# BR-SMART v12 Regime Acceleration','v11 sabit giriş motoruna piyasa genişliği ivmesi eklendi. Güçlü breadthte 2 pozisyon, iyileşen fakat tam güçlü olmayan breadthte 1 küçük pozisyon; bozulan rejimde yeni giriş yok. Parametre optimizasyonu yok.','',f'Ort dönem **{summary["avg"]:.2f}%**, en kötü **{summary["worst"]:.2f}%**, pozitif **{summary["positive"]}/{summary["chunks"]}**, işlem **{summary["trades"]}**, ort DD **{summary["avgdd"]:.2f}%**, ort PF **{summary["avgpf"]:.2f}**. Tüm veri **{summary["full"]["ret"]:.2f}%**, DD **{summary["full"]["dd"]:.2f}%**, PF **{summary["full"]["pf"]:.2f}**.','','|Dönem|Ret|DD|N|Win|PF|AvgW|AvgL|Stop|Regime|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for i,r in enumerate(rows,1):lines.append(f'|{i}|{r["ret"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["win"]:.1f}%|{r["pf"]:.2f}|{r["avgw"]:.2f}%|{r["avgl"]:.2f}%|{r["stop"]}|{r["regime"]}|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2),encoding='utf-8');print('\n'.join(lines))