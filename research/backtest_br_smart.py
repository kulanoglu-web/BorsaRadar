# BR-SMART v6: v3-style core + soft relative strength + soft RR sizing
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
        r2=c[-1]/c[-3]-1; r5=c[-1]/c[-6]-1; r15=c[-1]/c[-16]-1
        vals.append((s,.50*r2+.35*r5+.15*r15))
    vals.sort(key=lambda x:x[1]); n=max(1,len(vals)-1)
    out={s:k/n for k,(s,_) in enumerate(vals)}; _rank_cache[day]=out
    return out

def setup(s,i,day,breadth,rvmin=1.0,rsweight=10):
    a=bi.data[s]
    if i<60:return None
    f=bi.feat(s,i); prev=bi.feat(s,i-1); c=[r['c'] for r in a[:i]]; close=c[-1];m=f['m'];pm=prev['m']
    e20,e50=f['e20'],f['e50'];e20old=bi.b.ema(c[-55:-5],20)
    # No fixed N-day positive rule. Core quality gates only.
    if breadth<.42 or m['trap']:return None
    if not(close>e20 and e20>=e20old and (e20>e50 or f['slope']>0)):return None
    if f['rv']<rvmin or f['cmf']<0 or f['adx']<16:return None
    if not(45<=f['rsi']<=74):return None
    atr=max(m['atr'],close*.010);dist=(close/e20-1)/max(atr/close,.006)
    if dist>2.6:return None
    rs=market_rank(day).get(s,.5)
    hist=m['mac']-m['ms'];phist=pm['mac']-pm['ms']
    impulse=max(-1,min(1,(hist-phist)/(close*.005)))
    momturn=max(-1,min(1,(f['mom3']-prev['mom3'])/1.5))
    highs=[r['h'] for r in a[max(0,i-20):i]];lows=[r['l'] for r in a[max(0,i-20):i]]
    h20=max(highs);l20=min(lows);risk=max(1.1*atr,close*.012)
    target=h20 if close<h20*.995 else close+max(2.0*atr,.40*(h20-l20))
    rr=max(.25,(target-close)/risk)
    trend=34*(.45*(close>e20)+.35*(e20>e50)+.20*min(1,max(0,f['slope']/.018)))
    flow=20*(.55*min(1,max(0,(f['rv']-.85)/.8))+.45*min(1,max(0,f['cmf']/.18)))
    momentum=20*(.50*(m['mac']>m['ms'])+.30*max(0,impulse)+.20*max(0,momturn))
    quality=16*(.60*min(1,f['adx']/30)+.40*min(1,max(0,(74-f['rsi'])/20)))
    relbonus=rsweight*max(-.35,min(.65,rs-.50))
    score=trend+flow+momentum+quality+relbonus
    return score,f,{'rs':rs,'rr':rr,'imp':impulse,'momturn':momturn}

def simulate(threshold=76,maxpos=2,base_risk=.0025,rvmin=1.0,rsweight=10,trailatr=2.6):
    cash=100000.;pos={};trades=[];peak=cash;maxdd=0;cool={}
    for day in bi.dates:
        breadth=bi.breadth_cache.get(day,0)
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
                cp=a[i-1]['c'];unreal=cp/p['entry']-1
                if p['age']>=5 and unreal<.006 and gain<.025:ex=bar['o'];reason='TIME'
                elif gain>=.035 and cp<f['e20'] and (f['cmf']<0 or m['mac']<m['ms']):ex=bar['o'];reason='TREND'
                elif p['age']>=3 and unreal<-.008:ex=bar['o'];reason='FAIL'
            if ex:
                cash+=p['qty']*ex*(1-bi.FEE);trades.append(((ex/p['entry']-1-2*bi.FEE)*100,reason,p['rr']));del pos[s];cool[s]=day
        slots=maxpos-len(pos)
        if slots>0 and breadth>=.42:
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
                z=setup(s,i,day,breadth,rvmin,rsweight)
                if not z:continue
                sc,f,x=z
                # RS and RR rank candidates, but neither is a hard gate.
                rank=sc+5*(x['rs']-.5)+min(3,max(-1,x['rr']-1.2))+1.5*max(0,x['imp'])
                if sc>=threshold:cand.append((rank,s,i,f,x))
            cand.sort(reverse=True)
            for rank,s,i,f,x in cand[:slots]:
                px=bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.010);hard=px-max(1.1*atr,px*.012)
                # RR controls size softly: weak structure gets smaller size, never blocks trade.
                size_mult=max(.65,min(1.15,.65+.22*x['rr']))
                riskcash=100000*base_risk*size_mult
                qty=int(min(cash/(max(1,slots)*px*(1+bi.FEE)),riskcash/max(.01,px-hard)))
                if qty<=0:continue
                cash-=qty*px*(1+bi.FEE);pos[s]={'qty':qty,'entry':px,'high':px,'atr':atr,'hard':hard,'age':0,'rr':x['rr']};slots-=1
        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['qty']*(bi.data[s][i]['c'] if i is not None else p['entry'])
        peak=max(peak,eq);maxdd=max(maxdd,(peak-eq)/peak)
    for s,p in list(pos.items()):
        px=bi.data[s][-1]['c'];cash+=p['qty']*px*(1-bi.FEE);trades.append(((px/p['entry']-1-2*bi.FEE)*100,'SON',p['rr']))
    vals=[x[0] for x in trades];gp=sum(x for x in vals if x>0);gl=-sum(x for x in vals if x<0);wins=[x for x in vals if x>0];loss=[-x for x in vals if x<0]
    return {'threshold':threshold,'maxpos':maxpos,'rvmin':rvmin,'rsweight':rsweight,'ret':(cash/100000-1)*100,'end':cash,'dd':maxdd*100,'n':len(vals),'win':100*len(wins)/len(vals) if vals else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgwin':sum(wins)/max(1,len(wins)),'avgloss':sum(loss)/max(1,len(loss)),'reasons':{k:sum(1 for x in trades if x[1]==k) for k in ('STOP','TIME','TREND','FAIL','SON')}}

results=[]
for t in (72,76,80):
 for p in (2,3):
  for rv in (.95,1.05):
   for rw in (6,10,14):results.append(simulate(t,p,.0025,rv,rw,2.6))
# penalize inactivity so a one-trade model cannot win
results.sort(key=lambda x:(x['n']>=25,x['pf']>=1.0,x['ret']-.60*x['dd']+.40*min(2,x['pf'])-.18*abs(x['n']-55)/55),reverse=True);best=results[0]
lines=['# BR-SMART v6 Soft RS + Soft RR','10 gün pozitif şartı YOK. Relatif güç artık kapı değil sıralama/puan katkısı; RR işlem engellemez, pozisyon büyüklüğünü ayarlar. v3 tarzı kar-koru çıkış motoru korunur. TUPRS/savunma hariç; lookahead yok; maliyet dahil.','',f'EN IYI: skor {best["threshold"]}, pos {best["maxpos"]}, RVOL {best["rvmin"]:.2f}, RS ağırlık {best["rsweight"]}: **{best["ret"]:.2f}%**, 100k -> **{best["end"]:.0f} TL**, MaxDD **{best["dd"]:.2f}%**, {best["n"]} işlem, win **{best["win"]:.1f}%**, PF **{best["pf"]:.2f}**, ort kazanç **{best["avgwin"]:.2f}%**, ort kayıp **{best["avgloss"]:.2f}%**.','',f'Çıkışlar: {best["reasons"]}','','|Skor|Pos|RVOL|RSw|Getiri|DD|N|Win|PF|AvgW|AvgL|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in results[:18]:lines.append(f'|{x["threshold"]}|{x["maxpos"]}|{x["rvmin"]:.2f}|{x["rsweight"]}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|{x["avgwin"]:.2f}%|{x["avgloss"]:.2f}%|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'best':best,'all':results},indent=2),encoding='utf-8');print('\n'.join(lines))