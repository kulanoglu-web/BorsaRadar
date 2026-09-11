# BR-SMART v10: volume-led early entry with rolling holdout selection
import json
from pathlib import Path
import backtest_indicators as bi
START=100000.;FEE=bi.FEE

def sig(s,i,day,cfg):
    rvmin,cmfmin,brmin,cpmin,adxmax,distmax=cfg
    if i<65:return None
    a=bi.data[s];br=bi.breadth_cache.get(day,0)
    if br<brmin:return None
    f=bi.feat(s,i);p=bi.feat(s,i-1);m=f['m'];pm=p['m'];bar=a[i-1];rng=max(.001,bar['h']-bar['l']);cp=(bar['c']-bar['l'])/rng
    if m['trap'] or f['rv']<rvmin or f['cmf']<cmfmin or cp<cpmin:return None
    if not(45<=f['rsi']<=72) or f['adx']<14 or f['adx']>adxmax:return None
    hist=m['mac']-m['ms'];phist=pm['mac']-pm['ms'];dh=hist-phist
    if dh<=0:return None
    close=bar['c'];atr=max(m['atr'],close*.01);dist=(close/f['e20']-1)/max(atr/close,.006)
    if close<f['e20']*.985 or dist>distmax:return None
    score=32*min(1,f['rv']/1.8)+22*min(1,max(0,(f['cmf']+.02)/.18))+25*min(1,max(0,dh/(close*.006)))+11*min(1,cp)+10*min(1,max(0,(br-.35)/.25))
    return score,f

def sim(cfg,days):
    ds=[d for d in days if d in bi.breadth_cache]
    if not ds:return {'ret':0,'dd':0,'n':0,'win':0,'pf':0,'avgw':0,'avgl':0}
    dayset=set(ds);last=ds[-1];cash=START;pos={};tr=[];peak=START;dd=0;cool={}
    for day in ds:
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
                pro=p['q']*ex*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],reason));del pos[s];cool[s]=day
        slots=2-len(pos)
        if slots>0 and br>=cfg[2]:
            ca=[]
            for s,a in bi.data.items():
                if s in pos:continue
                i=bi.bysym[s].get(day)
                if i is None or i<65 or (s in cool and day-cool[s]<5*86400):continue
                turn,vol,j=bi.quality(s,i)
                if turn<120_000_000 or vol<120_000 or j>=2:continue
                gap=a[i]['o']/a[i-1]['c']-1
                if a[i]['o']<5 or not(-.03<=gap<=.015):continue
                z=sig(s,i,day,cfg)
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
    # close only at the window end, never at full-data end
    for s,p in list(pos.items()):
        i=bi.bysym[s].get(last)
        if i is None:continue
        px=bi.data[s][i]['c'];pro=p['q']*px*(1-FEE);cash+=pro;pnl=pro-p['cost'];tr.append((pnl,100*pnl/p['cost'],'SON'))
    gp=sum(x[0] for x in tr if x[0]>0);gl=-sum(x[0] for x in tr if x[0]<0);rets=[x[1] for x in tr];wins=[x for x in rets if x>0];loss=[-x for x in rets if x<0]
    return {'ret':(cash/START-1)*100,'dd':dd*100,'n':len(tr),'win':100*len(wins)/len(rets) if rets else 0,'pf':gp/gl if gl else (99 if gp else 0),'avgw':sum(wins)/max(1,len(wins)),'avgl':sum(loss)/max(1,len(loss))}

# compact config family around v9 winner + feature-study hint: lower ADX/less extension, stronger acceleration.
configs=[]
for rv in (1.2,1.35):
 for cmf in (0,.02):
  for br in (.42,.46):
   for cp in (.50,.58):
    for adxmax in (36,44,99):
     for distmax in (1.7,2.2):configs.append((rv,cmf,br,cp,adxmax,distmax))

dates=bi.dates
# chronological 31-calendar-day-ish chunks using index blocks of 22 trading days
chunks=[dates[i:i+22] for i in range(0,len(dates)-21,22)]
folds=[]
for k in range(4,len(chunks)):
    train=[d for ch in chunks[:k] for d in ch];test=chunks[k]
    def score(cfg):
        r=sim(cfg,train);return (r['n']>=25,r['pf']>=1,r['ret']-.55*r['dd']+.45*min(2,r['pf'])-.08*abs(r['n']-60)/60)
    best=max(configs,key=score);h=sim(best,test);folds.append({'fold':len(folds)+1,'train_chunks':k,'cfg':best,'holdout':h})
rets=[x['holdout']['ret'] for x in folds];n=sum(x['holdout']['n'] for x in folds);gpfs=[x['holdout']['pf'] for x in folds if x['holdout']['n']]
summary={'folds':len(folds),'avg':sum(rets)/len(rets) if rets else 0,'worst':min(rets) if rets else 0,'positive':sum(x>0 for x in rets),'trades':n,'avgdd':sum(x['holdout']['dd'] for x in folds)/len(folds) if folds else 0,'avgpf':sum(min(5,x) for x in gpfs)/len(gpfs) if gpfs else 0}
lines=['# BR-SMART v10 Rolling Holdout','Her foldta parametre yalnız daha eski dönemlerden seçildi; sonraki 22 işlem günü dokunulmamış holdout. TUPRS/savunma hariç; maliyet dahil; pencere sonunda pozisyonlar o günün kapanışıyla kapatılır.','',f'Holdout ortalama **{summary["avg"]:.2f}%**, en kötü **{summary["worst"]:.2f}%**, pozitif **{summary["positive"]}/{summary["folds"]}**, toplam işlem **{summary["trades"]}**, ort DD **{summary["avgdd"]:.2f}%**, ort fold PF **{summary["avgpf"]:.2f}**.','','|Fold|Train|RV|CMF|Br|CP|ADXmax|DistMax|Ret|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in folds:
 c=x['cfg'];h=x['holdout'];lines.append(f'|{x["fold"]}|{x["train_chunks"]}|{c[0]:.2f}|{c[1]:.2f}|{c[2]:.2f}|{c[3]:.2f}|{c[4]}|{c[5]:.1f}|{h["ret"]:.2f}%|{h["dd"]:.2f}%|{h["n"]}|{h["win"]:.1f}%|{h["pf"]:.2f}|')
Path('research/result_br_smart.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_br_smart.json').write_text(json.dumps({'summary':summary,'folds':folds},indent=2),encoding='utf-8');print('\n'.join(lines))