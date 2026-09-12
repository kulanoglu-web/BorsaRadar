# BR-SMART v20: local plateau + window/cost validation around v19 winner
import json
from pathlib import Path
import backtest_br_smart as b
base_sig=b.sig
BASE_FEE=b.FEE
CFG=b.BASE

def make_sig(adxmax,rvmin):
    def wrapped(s,i,day):
        z=base_sig(s,i,day)
        if not z:return None
        sc,f=z
        if f['adx']>adxmax or f['rv']<rvmin:return None
        return z
    return wrapped

chunks=[b.DATES[i:i+22] for i in range(0,len(b.DATES)-21,22)];dev=chunks[:6];hold=chunks[6:]
rows=[]
for adx in (33,34,35):
  for rv in (1.30,1.35,1.40):
    b.sig=make_sig(adx,rv)
    dr=[b.sim(ch,CFG) for ch in dev];da=[x for x in dr if x['n']]
    row={'adx':adx,'rv':rv,'dev_avg':sum(x['ret'] for x in dr)/len(dr),'dev_worst':min(x['ret'] for x in dr),'dev_dd':sum(x['dd'] for x in dr)/len(dr),'dev_n':sum(x['n'] for x in dr),'dev_pf':sum(min(5,x['pf']) for x in da)/len(da) if da else 0,'dev_pos':sum(x['ret']>0 for x in dr)}
    row['select']=row['dev_avg']+.35*row['dev_worst']-.25*row['dev_dd']+.05*min(2,row['dev_pf'])+0.02*row['dev_pos']-(.12 if row['dev_n']<10 else 0)
    rows.append(row)
rows.sort(key=lambda x:x['select'],reverse=True);best=rows[0]
# untouched holdout only after development selection
b.sig=make_sig(best['adx'],best['rv'])
hr=[b.sim(ch,CFG) for ch in hold];ha=[x for x in hr if x['n']]
best['hold_avg']=sum(x['ret'] for x in hr)/len(hr);best['hold_worst']=min(x['ret'] for x in hr);best['hold_dd']=sum(x['dd'] for x in hr)/len(hr);best['hold_n']=sum(x['n'] for x in hr);best['hold_pf']=sum(min(5,x['pf']) for x in ha)/len(ha) if ha else 0;best['hold_pos']=sum(x['ret']>0 for x in hr)
# Neighbor holdouts are reported for robustness, not selection.
for r in rows:
    b.sig=make_sig(r['adx'],r['rv']);hh=[b.sim(ch,CFG) for ch in hold];aa=[x for x in hh if x['n']];r['hold_avg']=sum(x['ret'] for x in hh)/len(hh);r['hold_worst']=min(x['ret'] for x in hh);r['hold_pf']=sum(min(5,x['pf']) for x in aa)/len(aa) if aa else 0;r['hold_n']=sum(x['n'] for x in hh)
# Window sensitivity for selected fixed model.
b.sig=make_sig(best['adx'],best['rv']);wins=[]
for w in (15,22,30):
  for off in (0,5,10):
    ps=[b.DATES[i:i+w] for i in range(off,len(b.DATES)-w+1,w)];rr=[b.sim(ch,CFG) for ch in ps];aa=[x for x in rr if x['n']]
    wins.append({'w':w,'off':off,'periods':len(rr),'avg':sum(x['ret'] for x in rr)/len(rr) if rr else 0,'worst':min((x['ret'] for x in rr),default=0),'pos':sum(x['ret']>0 for x in rr),'n':sum(x['n'] for x in rr),'dd':sum(x['dd'] for x in rr)/len(rr) if rr else 0,'pf':sum(min(5,x['pf']) for x in aa)/len(aa) if aa else 0})
# Cost stress. Same selected signals; fee only changes execution friction.
costs=[]
for fee in (.001,.0015,.002,.003):
    b.FEE=fee
    full=b.sim(b.DATES,CFG);hh=[b.sim(ch,CFG) for ch in hold];aa=[x for x in hh if x['n']]
    costs.append({'fee':fee,'full_ret':full['ret'],'full_dd':full['dd'],'full_pf':full['pf'],'n':full['n'],'hold_avg':sum(x['ret'] for x in hh)/len(hh),'hold_worst':min(x['ret'] for x in hh),'hold_pf':sum(min(5,x['pf']) for x in aa)/len(aa) if aa else 0})
b.FEE=BASE_FEE;b.sig=base_sig
lines=['# BR-SMART v20 Entry Plateau + Robustness',f'v19 çevresinde yalnız geliştirme döneminde 3x3 ADX/RVOL platosu tarandı. Seçilen: **ADX <= {best["adx"]}, RVOL >= {best["rv"]:.2f}**. Son 5 dönem seçime katılmadı.','','|ADXmax|RVOLmin|Dev Avg|Worst|DD|N|PF|+|Hold Avg|Worst|N|PF|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'|{r["adx"]}|{r["rv"]:.2f}|{r["dev_avg"]:.2f}%|{r["dev_worst"]:.2f}%|{r["dev_dd"]:.2f}%|{r["dev_n"]}|{r["dev_pf"]:.2f}|{r["dev_pos"]}/6|{r["hold_avg"]:.2f}%|{r["hold_worst"]:.2f}%|{r["hold_n"]}|{r["hold_pf"]:.2f}|')
lines+=['',f'Seçilen untouched holdout: **{best["hold_avg"]:.2f}%**, worst **{best["hold_worst"]:.2f}%**, DD **{best["hold_dd"]:.2f}%**, N **{best["hold_n"]}**, PF **{best["hold_pf"]:.2f}**, + **{best["hold_pos"]}/5**.','','## Window sensitivity','|W|Offset|Avg|Worst|+|N|DD|PF|','|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in wins:lines.append(f'|{x["w"]}|{x["off"]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["pos"]}/{x["periods"]}|{x["n"]}|{x["dd"]:.2f}%|{x["pf"]:.2f}|')
lines+=['','## Cost stress','|One-way fee|Round-trip ~|Full Ret|DD|PF|N|Hold Avg|Worst|Hold PF|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in costs:lines.append(f'|{100*x["fee"]:.2f}%|{200*x["fee"]:.2f}%|{x["full_ret"]:.2f}%|{x["full_dd"]:.2f}%|{x["full_pf"]:.2f}|{x["n"]}|{x["hold_avg"]:.2f}%|{x["hold_worst"]:.2f}%|{x["hold_pf"]:.2f}|')
Path('research/result_entry_plateau.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_entry_plateau.json').write_text(json.dumps({'best':best,'grid':rows,'windows':wins,'costs':costs},indent=2),encoding='utf-8');print('\n'.join(lines))
