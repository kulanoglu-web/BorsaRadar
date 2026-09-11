# BR-SMART v9: refine the only near-breakeven v8 family (volume lead)
import json
from pathlib import Path
import backtest_indicators as bi
START=100000.;FEE=bi.FEE

def sig(s,i,day,rvmin,cmfmin,breadthmin,closeposmin,persist):
    if i<65:return None
    a=bi.data[s];br=bi.breadth_cache.get(day,0)
    if br<breadthmin:return None
    f=bi.feat(s,i);p=bi.feat(s,i-1);m=f['m'];pm=p['m'];bar=a[i-1];rng=max(.001,bar['h']-bar['l']);closepos=(bar['c']-bar['l'])/rng
    if m['trap'] or f['rv']<rvmin or f['cmf']<cmfmin or closepos<closeposmin:return None
    if not(45<=f['rsi']<=72) or f['adx']<14:return None
    hist=m['mac']-m['ms'];phist=pm['mac']-pm['ms']
    if hist<=phist:return None
    c=[x['c'] for x in a[:i]];close=c[-1];atr=max(m['atr'],close*.01)
    if close<f['e20']*.985:return None
    if (close/f['e20']-1)/max(atr/close,.006)>2.2:return None
    if persist:
        # Require accumulation rather than a single-day volume spike.
        z=a[max(0,i-4):i];avprev=sum(x['v'] for x in a[max(0,i-24):max(0,i-4)])/max(1,len(a[max(0,i-24):max(0,i-4)]))
        strong=sum(x['v']>=avprev*.9 for x in z)>=3 if avprev else True
        if not strong:return None
    score=35*min(1,f['rv']/1.8)+25*min(1,max(0,(f['cmf']+.02)/.18))+20*min(1,max(0,(hist-phist)/(close*.006)))+10*min(1,closepos)+10*min(1,max(0,(br-.35)/.25))
    return score,f

def sim(rvmin,cmfmin,breadthmin,closeposmin,persist):
    cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in bi.dates:
        br=bi.breadth_cache.get(day,0)
        for s in list(pos):
            i=bi.bysym[s].get(day)
            if i is None:continue
            a=bi.data[s];bar=a[i];p=pos[s];f=bi.feat(s,i);m=f['m'];p['hi']=max(p['hi'],bar['h']);p['age']+=1;gain=p['hi']/p['en']-1;stop=p['hard']
            if gain>=.035:stop=max(stop,p['en']*1.002,p['hi']-2.6*p['atr'])
            if gain>=.07:stop=max(stop,p['en']*1.025,p['hi']-2.25*p['atr'])
            if gain>=.12:stop=max(stop,p['en']*1.065,p['hi']-1.95*p['atr'])
            ex=reason=None
            if bar['l']<=stop:ex=bar['o'] if bar['o']<stop else stop;reason='STOP'
            else:
                cp=a[i-1]['c'];un=cp/p['en']-1
                if p['age']>=4 and un<-.006 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=.035 and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
            if ex:
                pro=p['q']*ex*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],reason,p['age']));del pos[s];cool[s]=day
        slots=2-len(pos)
        if slots>0 and br>=breadthmin:
            ca=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<65 or (s in cool and day-cool[s]<5*86400):continue
                turn,vol,j=bi.quality(s,i)
                if turn<120_000_000 or vol<120_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.03<=gap<=.015):continue
                z=sig(s,i,day,rvmin,cmfmin,breadthmin,closeposmin,persist)
                if z:ca.append((z[0],s,i,z[1]))
            ca.sort(reverse=True)
            for sc,s,i,f in ca[:slots]:
                px=bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(1.1*atr,px*.012);q=int(min(cash/(max(1,slots)*px*(1+FEE)),START*.0025/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+FEE);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        px=bi.data[s][-1]['c'];pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],'SON',p['age']))
    gp=sum(x[0] for x in tr if x[0]>0);gl=-sum(x[0] for x in tr if x[0]<0);rets=[x[1] for x in tr];wins=[x for x in rets if x>0];loss=[-x for x in rets if x<0]
    return {'rv':rvmin,'cmf':cmfmin,'br':breadthmin,'cp':closeposmin,'persist':persist,'ret':(cash/START-1)*100,'end':cash,'dd':dd*100,'n':len(tr),'win':100*len(wins)/len(rets) if rets else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgw':sum(wins)/max(1,len(wins)),'avgl':sum(loss)/max(1,len(loss)),'reasons':{k:sum(1 for x in tr if x[2]==k) for k in ('STOP','FAIL','TREND','SON')}}

rows=[]
for rv in (1.05,1.2,1.35):
 for cmf in (0,.025):
  for br in (.40,.46):
   for cp in (.55,.68):
    for pe in (False,True):rows.append(sim(rv,cmf,br,cp,pe))
rows.sort(key=lambda x:(x['n']>=25,x['pf']>=1,x['ret']-.55*x['dd']+.55*min(2,x['pf'])-.12*abs(x['n']-55)/55),reverse=True);best=rows[0]
lines=['# BR-SMART v9 Volume Quality Grid','v8de en iyi aile VOL idi. v9 sadece bunu rafine eder: RVOL, CMF, piyasa genişliği, mum kapanış kalitesi ve hacim devamlılığı. TUPRS/savunma hariç; lookahead yok; maliyet dahil; TL-PF.','',f'EN IYI: RVOL {best["rv"]:.2f}, CMF {best["cmf"]:.3f}, breadth {best["br"]:.2f}, closepos {best["cp"]:.2f}, persist {best["persist"]}: **{best["ret"]:.2f}%**, 100k -> **{best["end"]:.0f} TL**, DD **{best["dd"]:.2f}%**, N **{best["n"]}**, win **{best["win"]:.1f}%**, TL-PF **{best["pf"]:.2f}**, AvgW **{best["avgw"]:.2f}%**, AvgL **{best["avgl"]:.2f}%**.','',f'Çıkışlar: {best["reasons"]}','','|RV|CMF|Br|ClosePos|Persist|Ret|DD|N|Win|PF|AvgW|AvgL|','|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|']
for x in rows[:24]:lines.append(f'|{x["rv"]:.2f}|{x["cmf"]:.3f}|{x["br"]:.2f}|{x["cp"]:.2f}|{x["persist"]}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgw"]:.2f}%|{x["avgl"]:.2f}%|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':rows},indent=2),encoding='utf-8');print('\n'.join(lines))