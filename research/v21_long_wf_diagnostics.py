# BR-SMART v21: fixed v20 signal; long rolling validation + trade diagnostics
import json
from pathlib import Path
import backtest_br_smart as b

START=100000.; FEE=b.FEE; CFG=b.BASE; DATES=b.DATES; DPOS={d:i for i,d in enumerate(DATES)}
base_sig=b.sig

def v20_sig(s,i,day):
    z=base_sig(s,i,day)
    if not z:return None
    sc,f=z
    if f['adx']>35 or f['rv']<1.35:return None
    return z

def idx_at_or_before(s,day):
    i=DPOS.get(day,len(DATES)-1)
    for j in range(i,-1,-1):
        z=b.bi.bysym[s].get(DATES[j])
        if z is not None:return z
    return None

def run(days, fee=FEE, close_confirm=False):
    ds=[d for d in days if d in b.bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0,'trades':[]}
    last=ds[-1];cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    oldfee=b.FEE;b.FEE=fee
    try:
      for day in ds:
        for s in list(pos):
            i=b.bi.bysym[s].get(day)
            if i is None:continue
            a=b.bi.data[s];bar=a[i];p=pos[s];f=b.bi.feat(s,i);m=f['m'];p['hi']=max(p['hi'],bar['h']);p['lo']=min(p['lo'],bar['l']);p['age']+=1
            gain=p['hi']/p['en']-1;stop=p['hard']
            if gain>=CFG['be']:stop=max(stop,p['en']*1.001)
            if gain>=CFG['trail_on']:stop=max(stop,p['hi']-CFG['trail_atr']*p['atr'])
            if gain>=.08:stop=max(stop,p['en']*1.025,p['hi']-(CFG['trail_atr']-.3)*p['atr'])
            if gain>=.13:stop=max(stop,p['en']*1.07,p['hi']-(CFG['trail_atr']-.6)*p['atr'])
            ex=reason=None;wick=False
            if close_confirm:
                if bar['o']<p['hard']*.985:ex=bar['o'];reason='GAPSTOP'
                elif a[i-1]['c']<=stop:ex=bar['o'];reason='CLOSESTOP'
            else:
                if bar['l']<=stop:
                    ex=bar['o'] if bar['o']<stop else stop;reason='STOP';wick=(bar['c']>stop)
            if ex is None:
                cp=a[i-1]['c'];un=cp/p['en']-1;ok,_,_=b.allowed(day)
                if not ok and p['age']>=2 and un<.015:ex=bar['o'];reason='REGIME'
                elif p['age']>=4 and un<-.007 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=CFG['trail_on'] and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
            if ex:
                pro=p['q']*ex*(1-fee);cash+=pro;pnl=pro-p['cost'];ret=100*pnl/p['cost'];mfe=100*(p['hi']/p['en']-1);mae=100*(p['lo']/p['en']-1)
                rec3=rec5=rec10=None
                for hz,key in ((3,'r3'),(5,'r5'),(10,'r10')):
                    j=min(len(a)-1,i+hz)
                    if j>i:
                        val=100*(a[j]['c']/ex-1)
                        if hz==3:rec3=val
                        elif hz==5:rec5=val
                        else:rec10=val
                tr.append({'s':s,'day':day,'pnl':pnl,'ret':ret,'reason':reason,'age':p['age'],'mfe':mfe,'mae':mae,'wick':wick,'rec3':rec3,'rec5':rec5,'rec10':rec10})
                del pos[s];cool[s]=day
        ok,maxpos,risk=b.allowed(day);slots=maxpos-len(pos)
        if slots>0 and ok:
            ca=[]
            for s,a in b.bi.data.items():
                if s in pos:continue
                i=b.bi.bysym[s].get(day)
                if i is None or i<65 or (s in cool and day-cool[s]<4*86400):continue
                turn,vol,j=b.bi.quality(s,i)
                if turn<120_000_000 or vol<120_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.03<=gap<=.012):continue
                z=v20_sig(s,i,day)
                if z:ca.append((z[0],s,i,z[1]))
            ca.sort(reverse=True)
            for sc,s,i,f in ca[:slots]:
                px=b.bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(CFG['hard_atr']*atr,px*.012);q=int(min(cash/(max(1,slots)*px*(1+fee)),START*risk/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+fee);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'lo':px,'atr':atr,'hard':hard,'age':0,'cost':cost};slots-=1
        eq=cash
        for s,p in pos.items():
            i=b.bi.bysym[s].get(day)
            if i is None:i=idx_at_or_before(s,day)
            eq+=p['q']*(b.bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
      for s,p in list(pos.items()):
        i=idx_at_or_before(s,last);px=b.bi.data[s][i]['c'] if i is not None else p['en'];pro=p['q']*px*(1-fee);cash+=pro;pnl=pro-p['cost'];tr.append({'s':s,'day':last,'pnl':pnl,'ret':100*pnl/p['cost'],'reason':'SON','age':p['age'],'mfe':100*(p['hi']/p['en']-1),'mae':100*(p['lo']/p['en']-1),'wick':False,'rec3':None,'rec5':None,'rec10':None})
      gp=sum(x['pnl'] for x in tr if x['pnl']>0);gl=-sum(x['pnl'] for x in tr if x['pnl']<0);wins=sum(x['pnl']>0 for x in tr)
      return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*wins/len(tr) if tr else 0,'pf':gp/gl if gl else (99 if gp else 0),'trades':tr}
    finally:
      b.FEE=oldfee

def avg(xs,k):return sum(x[k] for x in xs)/len(xs) if xs else 0

# Expanding walk-forward: fixed v20 signal, no re-tuning. Use non-overlapping 22-day folds after first 4 folds.
folds=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)]
wf=[]
for j in range(4,len(folds)):
    r=run(folds[j]);wf.append({'fold':j+1,'ret':r['ret'],'dd':r['dd'],'n':r['n'],'win':r['win'],'pf':r['pf']})

base=run(DATES);cc=run(DATES,close_confirm=True)
trs=base['trades'];stops=[x for x in trs if x['reason']=='STOP'];wicks=[x for x in stops if x['wick']]
los=[x for x in trs if x['pnl']<0];wins=[x for x in trs if x['pnl']>0]
recovered5=[x for x in stops if x['rec5'] is not None and x['rec5']>2]
recovered10=[x for x in stops if x['rec10'] is not None and x['rec10']>3]
summary={
 'full':{k:base[k] for k in ('ret','dd','n','win','pf')},
 'wf':wf,
 'wf_avg':avg(wf,'ret'),'wf_worst':min((x['ret'] for x in wf),default=0),'wf_pos':sum(x['ret']>0 for x in wf),'wf_pf':avg([x for x in wf if x['n']],'pf'),
 'diag':{'avg_mfe':avg(trs,'mfe'),'avg_mae':avg(trs,'mae'),'win_mfe':avg(wins,'mfe'),'loss_mfe':avg(los,'mfe'),'win_mae':avg(wins,'mae'),'loss_mae':avg(los,'mae'),'stops':len(stops),'wick_stops':len(wicks),'wick_pct':100*len(wicks)/len(stops) if stops else 0,'stop_recover5':len(recovered5),'stop_recover10':len(recovered10)},
 'close_confirm':{k:cc[k] for k in ('ret','dd','n','win','pf')}
}
lines=['# BR-SMART v21 Long WF + Trade Diagnostics','v20 sabit: ADX<=35, RVOL>=1.35. Parametre yeniden seçilmedi. TUPRS/savunma hariç; maliyet dahil.','',f'Full: **{base["ret"]:.2f}%**, DD **{base["dd"]:.2f}%**, N **{base["n"]}**, win **{base["win"]:.1f}%**, PF **{base["pf"]:.2f}**.',f'Rolling 22g fixed-OOS: avg **{summary["wf_avg"]:.2f}%**, worst **{summary["wf_worst"]:.2f}%**, pozitif **{summary["wf_pos"]}/{len(wf)}**, avg PF **{summary["wf_pf"]:.2f}**.','','|Fold|Ret|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---:|']
for x in wf:lines.append(f'|{x["fold"]}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|')
d=summary['diag'];lines+=['','## Trade diagnostics',f'Avg MFE **{d["avg_mfe"]:.2f}%**, Avg MAE **{d["avg_mae"]:.2f}%**. Kazanan MFE **{d["win_mfe"]:.2f}%**, kaybeden MFE **{d["loss_mfe"]:.2f}%**. Kazanan MAE **{d["win_mae"]:.2f}%**, kaybeden MAE **{d["loss_mae"]:.2f}%**.',f'STOP **{d["stops"]}**, wick-only stop **{d["wick_stops"]} ({d["wick_pct"]:.1f}%)**. Stop sonrası +%2/5g toparlayan **{d["stop_recover5"]}**, +%3/10g toparlayan **{d["stop_recover10"]}**.',f'Close-confirmed alternatif: **{cc["ret"]:.2f}%**, DD **{cc["dd"]:.2f}%**, PF **{cc["pf"]:.2f}**, N **{cc["n"]}**.']
Path('research/result_v21_long_wf.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v21_long_wf.json').write_text(json.dumps({'summary':summary,'trades':trs},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))
