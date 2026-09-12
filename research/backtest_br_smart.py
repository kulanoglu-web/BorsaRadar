# BR-SMART v15: fixed regime OOS matrix; no score threshold tuning
import json
from pathlib import Path
import backtest_indicators as bi
START=100000.;FEE=bi.FEE;DATES=bi.dates;DPOS={d:i for i,d in enumerate(DATES)}

def state(day):
    i=DPOS.get(day,0);br=bi.breadth_cache.get(day,0);prev=[bi.breadth_cache.get(DATES[j],br) for j in range(max(0,i-3),i)];avg=sum(prev)/len(prev) if prev else br;d=br-avg
    return br,d,br>=.54,(br>=.44 and d>=.025),(br<.44 or (br<.52 and d<-.035))
def allowed(mode,day):
    br,d,strong,recovery,weak=state(day)
    if mode=='BASE':return br>=.42,2,.0022
    if mode=='STRONG':return strong,2,.0022
    if mode=='RECOVERY':return recovery,1,.0015
    return ((strong or recovery) and not weak),(2 if strong else 1),(.0022 if strong else .0013)
def idx_at_or_before(s,day):
    i=DPOS.get(day,len(DATES)-1)
    for j in range(i,-1,-1):
        z=bi.bysym[s].get(DATES[j])
        if z is not None:return z
    return None
def sig(s,i,day,mode):
    ok,_,_=allowed(mode,day)
    if i<65 or not ok:return None
    br,bd,strong,recovery,weak=state(day);a=bi.data[s];f=bi.feat(s,i);p=bi.feat(s,i-1);m=f['m'];pm=p['m'];bar=a[i-1];rng=max(.001,bar['h']-bar['l']);cp=(bar['c']-bar['l'])/rng
    if m['trap'] or f['rv']<1.20 or f['cmf']<-.02 or cp<.50 or not(45<=f['rsi']<=70) or not(16<=f['adx']<=38):return None
    dh=(m['mac']-m['ms'])-(pm['mac']-pm['ms'])
    if dh<=0:return None
    close=bar['c'];atr=max(m['atr'],close*.01);dist=(close/f['e20']-1)/max(atr/close,.006)
    if not(-.25<=dist<=1.8):return None
    dhn=max(0,min(1,dh/max(close*.006,.01)));rvn=max(0,min(1,(f['rv']-1)/1.1));accn=max(0,min(1,(f['acc']+.005)/.05));adxq=max(0,1-abs(f['adx']-27)/15);extq=max(0,1-max(0,dist-.6)/1.4)
    return 38*dhn+22*rvn+16*accn+12*adxq+8*extq+4*max(0,min(1,(bd+.02)/.10)),f

def sim(mode,days):
    ds=[d for d in days if d in bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0}
    last=ds[-1];cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in ds:
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
                cp=a[i-1]['c'];un=cp/p['en']-1;ok,_,_=allowed(mode,day)
                if not ok and p['age']>=2 and un<.015:ex=bar['o'];reason='REGIME'
                elif p['age']>=4 and un<-.007 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=.05 and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
            if ex:
                pro=p['q']*ex*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],reason));del pos[s];cool[s]=day
        ok,maxpos,risk=allowed(mode,day);slots=maxpos-len(pos)
        if slots>0 and ok:
            ca=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<65 or (s in cool and day-cool[s]<4*86400):continue
                turn,vol,j=bi.quality(s,i)
                if turn<120_000_000 or vol<120_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.03<=gap<=.012):continue
                z=sig(s,i,day,mode)
                if z:ca.append((z[0],s,i,z[1]))
            ca.sort(reverse=True)
            for sc,s,i,f in ca[:slots]:
                px=bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(1.15*atr,px*.012);q=int(min(cash/(max(1,slots)*px*(1+FEE)),START*risk/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+FEE);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day)
            if i is None:i=idx_at_or_before(s,day)
            eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        i=idx_at_or_before(s,last);px=bi.data[s][i]['c'] if i is not None else p['en'];pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],'SON'))
    peak=max(peak,cash);dd=max(dd,(peak-cash)/peak)
    gp=sum(x[0] for x in tr if x[0]>0);gl=-sum(x[0] for x in tr if x[0]<0);rets=[x[1] for x in tr];wins=[x for x in rets if x>0]
    return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*len(wins)/len(rets) if rets else 0,'pf':gp/gl if gl else (99 if gp else 0)}

chunks=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for mode in ('BASE','STRONG','RECOVERY','DYNAMIC'):
    dr=[sim(mode,ch) for ch in dev];hr=[sim(mode,ch) for ch in hold];ha=[x for x in hr if x['n']]
    rows.append({'mode':mode,'dev_avg':sum(x['ret'] for x in dr)/len(dr),'dev_n':sum(x['n'] for x in dr),'hold_avg':sum(x['ret'] for x in hr)/len(hr),'hold_worst':min(x['ret'] for x in hr),'hold_pos':sum(x['ret']>0 for x in hr),'hold_n':sum(x['n'] for x in hr),'hold_dd':sum(x['dd'] for x in hr)/len(hr),'hold_pf':sum(min(5,x['pf']) for x in ha)/len(ha) if ha else 0,'full':sim(mode,DATES)})
lines=['# BR-SMART v15 Fixed Regime OOS Matrix','Dört rejim yaklaşımı aynı sabit giriş motoruyla karşılaştırıldı. Son 5 dönem kronolojik holdout olarak raporlanır. Bu turda kalite skoru eşiği yok; v14teki eşik seçiminin kötüleştiği doğrulandı. Terminal muhasebe düzeltmesi aktif. TUPRS/savunma hariç, maliyet dahil.','','|Mode|Dev Avg|Dev N|Hold Avg|Worst|Positive|Hold N|DD|PF|Full Ret|Full DD|Full PF|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'|{r["mode"]}|{r["dev_avg"]:.2f}%|{r["dev_n"]}|{r["hold_avg"]:.2f}%|{r["hold_worst"]:.2f}%|{r["hold_pos"]}/{len(hold)}|{r["hold_n"]}|{r["hold_dd"]:.2f}%|{r["hold_pf"]:.2f}|{r["full"]["ret"]:.2f}%|{r["full"]["dd"]:.2f}%|{r["full"]["pf"]:.2f}|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'rows':rows},indent=2),encoding='utf-8');print('\n'.join(lines))