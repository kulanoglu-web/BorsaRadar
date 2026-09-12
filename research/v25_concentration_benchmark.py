# BR-SMART v25: concentration, weekday, benchmark proxy diagnostics for fixed v24 D1.6
import json, math
from pathlib import Path
import v21_long_wf_diagnostics as v
import backtest_br_smart as b

START=100000.; DATES=b.DATES; CFG=b.BASE; FEE=b.FEE; DPOS={d:i for i,d in enumerate(DATES)}
DISASTER=1.6

def idx_at_or_before(s,day):
    i=DPOS.get(day,len(DATES)-1)
    for j in range(i,-1,-1):
        z=b.bi.bysym[s].get(DATES[j])
        if z is not None:return z
    return None

def run(days):
    ds=[d for d in days if d in b.bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0,'trades':[],'equity':[]}
    last=ds[-1];cash=START;pos={};tr=[];peak=START;dd=0;cool={};eqs=[]
    for day in ds:
        for s in list(pos):
            i=b.bi.bysym[s].get(day)
            if i is None:continue
            a=b.bi.data[s];bar=a[i];p=pos[s];f=b.bi.feat(s,i);m=f['m'];p['hi']=max(p['hi'],bar['h']);p['age']+=1
            gain=p['hi']/p['en']-1;normal=p['hard']
            if gain>=CFG['be']:normal=max(normal,p['en']*1.001)
            if gain>=CFG['trail_on']:normal=max(normal,p['hi']-CFG['trail_atr']*p['atr'])
            if gain>=.08:normal=max(normal,p['en']*1.025,p['hi']-(CFG['trail_atr']-.3)*p['atr'])
            if gain>=.13:normal=max(normal,p['en']*1.07,p['hi']-(CFG['trail_atr']-.6)*p['atr'])
            ex=reason=None
            disaster=min(p['en']-DISASTER*p['atr'],p['en']*.97)
            if bar['l']<=disaster:
                ex=bar['o'] if bar['o']<disaster else disaster;reason='DISASTER'
            if ex is None and a[i-1]['c']<=normal:
                ex=bar['o'];reason='CLOSESTOP'
            if ex is None:
                cp=a[i-1]['c'];un=cp/p['en']-1;ok,_,_=b.allowed(day)
                if not ok and p['age']>=2 and un<.015:ex=bar['o'];reason='REGIME'
                elif p['age']>=4 and un<-.007 and gain<.02:ex=bar['o'];reason='FAIL'
                elif gain>=CFG['trail_on'] and cp<f['e20'] and f['cmf']<0 and m['mac']<m['ms']:ex=bar['o'];reason='TREND'
            if ex:
                pro=p['q']*ex*(1-FEE);cash+=pro;pnl=pro-p['cost'];ret=100*pnl/p['cost'];tr.append({'s':s,'entry_day':p['entry_day'],'exit_day':day,'pnl':pnl,'ret':ret,'reason':reason,'age':p['age']});del pos[s];cool[s]=day
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
                z=v.v20_sig(s,i,day)
                if z:ca.append((z[0],s,i,z[1]))
            ca.sort(reverse=True)
            for sc,s,i,f in ca[:slots]:
                px=b.bi.data[s][i]['o'];atr=max(f['m']['atr'],px*.01);hard=px-max(CFG['hard_atr']*atr,px*.012);q=int(min(cash/(max(1,slots)*px*(1+FEE)),START*risk/max(.01,px-hard)))
                if q<=0:continue
                cost=q*px*(1+FEE);cash-=cost;pos[s]={'q':q,'en':px,'hi':px,'atr':atr,'hard':hard,'age':0,'cost':cost,'entry_day':day};slots-=1
        eq=cash
        for s,p in pos.items():
            i=b.bi.bysym[s].get(day)
            if i is None:i=idx_at_or_before(s,day)
            eq+=p['q']*(b.bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak);eqs.append((day,eq))
    for s,p in list(pos.items()):
        i=idx_at_or_before(s,last);px=b.bi.data[s][i]['c'] if i is not None else p['en'];pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append({'s':s,'entry_day':p['entry_day'],'exit_day':last,'pnl':pnl,'ret':100*pnl/p['cost'],'reason':'SON','age':p['age']})
    gp=sum(x['pnl'] for x in tr if x['pnl']>0);gl=-sum(x['pnl'] for x in tr if x['pnl']<0);wins=sum(x['pnl']>0 for x in tr)
    return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*wins/len(tr) if tr else 0,'pf':gp/gl if gl else (99 if gp else 0),'trades':tr,'equity':eqs}

def weekday(ts):
    import datetime as dt
    return dt.datetime.utcfromtimestamp(ts).weekday()

def proxy_benchmark(days):
    ds=[d for d in days if d in b.bi.breadth_cache]
    if not ds:return 0
    rets=[]
    for s,a in b.bi.data.items():
        i0=idx_at_or_before(s,ds[0]);i1=idx_at_or_before(s,ds[-1])
        if i0 is None or i1 is None or i1<=i0:continue
        c0=a[i0]['c'];c1=a[i1]['c']
        if c0 and c1 and c0>0:rets.append(c1/c0-1)
    rets=sorted(rets)
    if not rets:return 0
    # Winsorize 2.5% tails to avoid tiny/illiquid extreme distortions.
    lo=rets[max(0,int(len(rets)*.025)-1)];hi=rets[min(len(rets)-1,int(len(rets)*.975))]
    rr=[min(hi,max(lo,x)) for x in rets]
    return 100*sum(rr)/len(rr)

r=run(DATES);tr=r['trades']
by={}
for x in tr:
    z=by.setdefault(x['s'],{'n':0,'pnl':0,'wins':0,'losses':0})
    z['n']+=1;z['pnl']+=x['pnl'];z['wins']+=x['pnl']>0;z['losses']+=x['pnl']<0
rows=sorted([{'s':s,**z} for s,z in by.items()],key=lambda x:x['pnl'],reverse=True)
total=sum(x['pnl'] for x in tr);pos_total=sum(max(0,x['pnl']) for x in tr)
for x in rows:x['share_total']=100*x['pnl']/total if total else 0;x['share_positive']=100*max(0,x['pnl'])/pos_total if pos_total else 0

top1=rows[0]['share_positive'] if rows else 0;top3=sum(x['share_positive'] for x in rows[:3]);top5=sum(x['share_positive'] for x in rows[:5])
wd={i:{'n':0,'pnl':0,'wins':0} for i in range(5)}
for x in tr:
    w=weekday(x['entry_day']);
    if w in wd:wd[w]['n']+=1;wd[w]['pnl']+=x['pnl'];wd[w]['wins']+=x['pnl']>0

folds=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)][4:]
fold_diag=[]
for k,ch in enumerate(folds,5):
    rr=run(ch);bench=proxy_benchmark(ch);fold_diag.append({'fold':k,'model':rr['ret'],'bench_proxy':bench,'alpha':rr['ret']-bench,'dd':rr['dd'],'n':rr['n']})
bench_full=proxy_benchmark(DATES);alpha_full=r['ret']-bench_full

lines=['# BR-SMART v25 Concentration + Weekday + Benchmark Proxy','v24 D1.6 sabit; yeni parametre seçilmedi. TUPRS/savunma hariç. Benchmark olarak eşit-ağırlıklı, likit evren kapanış-kapanış proxy kullanıldı; XU100 değil.','',f'Full model: **{r["ret"]:.2f}%**, DD **{r["dd"]:.2f}%**, PF **{r["pf"]:.2f}**, N **{r["n"]}**. Proxy benchmark **{bench_full:.2f}%**, relatif fark **{alpha_full:.2f} puan**.','','## Stock concentration','|Hisse|N|PnL TL|Kazanç|Kayıp|Pozitif PnL payı|','|---|---:|---:|---:|---:|---:|']
for x in rows:lines.append(f'|{x["s"]}|{x["n"]}|{x["pnl"]:.0f}|{x["wins"]}|{x["losses"]}|{x["share_positive"]:.1f}%|')
lines+=['',f'Top1 pozitif PnL payı **{top1:.1f}%**, Top3 **{top3:.1f}%**, Top5 **{top5:.1f}%**.','','## Entry weekday','|Gün|N|PnL TL|Win rate|','|---|---:|---:|---:|']
names=['Pzt','Sal','Çar','Per','Cum']
for i in range(5):
    z=wd[i];lines.append(f'|{names[i]}|{z["n"]}|{z["pnl"]:.0f}|{(100*z["wins"]/z["n"] if z["n"] else 0):.1f}%|')
lines+=['','## 22g fixed OOS vs proxy','|Fold|Model|Proxy|Relatif|DD|N|','|---:|---:|---:|---:|---:|---:|']
for x in fold_diag:lines.append(f'|{x["fold"]}|{x["model"]:.2f}%|{x["bench_proxy"]:.2f}%|{x["alpha"]:.2f} puan|{x["dd"]:.2f}%|{x["n"]}|')
Path('research/result_v25_concentration_benchmark.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v25_concentration_benchmark.json').write_text(json.dumps({'full':{k:r[k] for k in ('ret','dd','n','win','pf')},'benchmark_proxy':bench_full,'alpha_full':alpha_full,'stocks':rows,'top1':top1,'top3':top3,'top5':top5,'weekday':wd,'folds':fold_diag},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))
