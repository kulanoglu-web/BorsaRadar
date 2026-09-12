# BR-SMART v19: coarse entry-gate optimization with untouched holdout
import json
from pathlib import Path
import backtest_br_smart as b

base_sig=b.sig

def gate_sig(name):
    def wrapped(s,i,day,mode):
        z=base_sig(s,i,day,mode)
        if not z:return None
        sc,f=z;a=b.bi.data[s];bar=a[i-1];m=f['m'];pm=b.bi.feat(s,i-1)['m'];dh=(m['mac']-m['ms'])-(pm['mac']-pm['ms']);atr=max(m['atr'],bar['c']*.01)
        adx=f['adx'];dist=(bar['c']/f['e20']-1)/max(atr/bar['c'],.006);har=dh/max(atr,.01)
        if name=='ADX34' and adx>34:return None
        if name=='ADX32' and adx>32:return None
        if name=='HATR03' and har<.03:return None
        if name=='HATR05' and har<.05:return None
        if name=='ADX34_H03' and (adx>34 or har<.03):return None
        if name=='ADX34_RV135' and (adx>34 or f['rv']<1.35):return None
        if name=='ADX34_DIST15' and (adx>34 or dist>1.5):return None
        if name=='ADX34_RSI66' and (adx>34 or f['rsi']>66):return None
        if name=='ADX34_CP55':
            rng=max(.001,bar['h']-bar['l']);cp=(bar['c']-bar['l'])/rng
            if adx>34 or cp<.55:return None
        return z
    return wrapped

models=['BASE','ADX34','ADX32','HATR03','HATR05','ADX34_H03','ADX34_RV135','ADX34_DIST15','ADX34_RSI66','ADX34_CP55']
chunks=[b.DATES[i:i+22] for i in range(0,len(b.DATES)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for name in models:
    b.sig=base_sig if name=='BASE' else gate_sig(name)
    dr=[b.sim('DYNAMIC',ch) for ch in dev];hr=[b.sim('DYNAMIC',ch) for ch in hold];ha=[x for x in hr if x['n']];da=[x for x in dr if x['n']]
    row={'model':name,'dev_avg':sum(x['ret'] for x in dr)/len(dr),'dev_worst':min(x['ret'] for x in dr),'dev_dd':sum(x['dd'] for x in dr)/len(dr),'dev_n':sum(x['n'] for x in dr),'dev_pf':sum(min(5,x['pf']) for x in da)/len(da) if da else 0,'dev_pos':sum(x['ret']>0 for x in dr),'hold_avg':sum(x['ret'] for x in hr)/len(hr),'hold_worst':min(x['ret'] for x in hr),'hold_dd':sum(x['dd'] for x in hr)/len(hr),'hold_n':sum(x['n'] for x in hr),'hold_pf':sum(min(5,x['pf']) for x in ha)/len(ha) if ha else 0,'hold_pos':sum(x['ret']>0 for x in hr)}
    # selection score only development data; prefer repeatability and enough trades
    row['select']=row['dev_avg']+.25*row['dev_worst']-.20*row['dev_dd']+.03*min(2,row['dev_pf'])-(.10 if row['dev_n']<10 else 0)
    rows.append(row)
b.sig=base_sig
rows.sort(key=lambda x:x['select'],reverse=True);best=rows[0]
lines=['# BR-SMART v19 Entry Gate OOS','DYNAMIC rejim ve v16 çıkışlar sabit. Sadece kaba, açıklanabilir erken-giriş kapıları ilk 6 geliştirme döneminde karşılaştırıldı; son 5 dönem seçime katılmadı.','','|Model|Dev Avg|Worst|DD|N|PF|+|Hold Avg|Worst|DD|N|PF|+|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'|{r["model"]}|{r["dev_avg"]:.2f}%|{r["dev_worst"]:.2f}%|{r["dev_dd"]:.2f}%|{r["dev_n"]}|{r["dev_pf"]:.2f}|{r["dev_pos"]}/6|{r["hold_avg"]:.2f}%|{r["hold_worst"]:.2f}%|{r["hold_dd"]:.2f}%|{r["hold_n"]}|{r["hold_pf"]:.2f}|{r["hold_pos"]}/5|')
lines+=['',f'Development-only seçim: **{best["model"]}**. Untouched holdout ort **{best["hold_avg"]:.2f}%**, worst **{best["hold_worst"]:.2f}%**, PF **{best["hold_pf"]:.2f}**, N **{best["hold_n"]}**.']
Path('research/result_entry_gate_opt.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_entry_gate_opt.json').write_text(json.dumps({'best':best,'rows':rows},indent=2),encoding='utf-8');print('\n'.join(lines))
