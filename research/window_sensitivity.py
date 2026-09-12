# Stability check for BR-SMART fixed DYNAMIC regime model across window sizes/offsets.
import json
from pathlib import Path
import backtest_br_smart as m

def pack(size,offset):
    ds=m.DATES[offset:]
    chunks=[ds[i:i+size] for i in range(0,len(ds)-size+1,size)]
    rr=[m.sim('DYNAMIC',ch) for ch in chunks]
    active=[x for x in rr if x['n']]
    return {'size':size,'offset':offset,'periods':len(rr),'avg':sum(x['ret'] for x in rr)/len(rr) if rr else 0,'worst':min((x['ret'] for x in rr),default=0),'positive':sum(x['ret']>0 for x in rr),'n':sum(x['n'] for x in rr),'dd':sum(x['dd'] for x in rr)/len(rr) if rr else 0,'pf':sum(min(5,x['pf']) for x in active)/len(active) if active else 0}
rows=[]
for size in (15,22,30):
    for off in (0,5,10):rows.append(pack(size,off))
lines=['# BR-SMART Window Sensitivity','Sabit DYNAMIC model; parametre seçimi yok. 15/22/30 işlem günlük pencereler ve üç farklı başlangıç ofseti ile sınandı.','','|Window|Offset|Periods|Avg|Worst|Positive|N|DD|PF|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'|{r["size"]}|{r["offset"]}|{r["periods"]}|{r["avg"]:.2f}%|{r["worst"]:.2f}%|{r["positive"]}/{r["periods"]}|{r["n"]}|{r["dd"]:.2f}%|{r["pf"]:.2f}|')
Path('research/result_window_sensitivity.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_window_sensitivity.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print('\n'.join(lines))