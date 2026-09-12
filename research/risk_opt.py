# BR-SMART v17: fixed v16 entries/exits, optimize only regime risk allocation on development folds
import json
from pathlib import Path
import backtest_br_smart as m

chunks=[m.DATES[i:i+22] for i in range(0,len(m.DATES)-21,22)]
dev=chunks[:6];hold=chunks[6:]
base_allowed=m.allowed
base_cfg=m.BASE

configs=[]
for sr in (.0018,.0022,.0026):
    for rr in (.0008,.0011,.0013):
        for sp in (1,2):
            configs.append({'strong_risk':sr,'recovery_risk':rr,'strong_pos':sp})

def run_cfg(c,days):
    def alloc(day):
        br,d,strong,recovery,weak=m.state(day)
        ok=(strong or recovery) and not weak
        return ok,(c['strong_pos'] if strong else 1),(c['strong_risk'] if strong else c['recovery_risk'])
    m.allowed=alloc
    try:return m.sim(days,base_cfg)
    finally:m.allowed=base_allowed

rows=[]
for c in configs:
    rr=[run_cfg(c,ch) for ch in dev];act=[x for x in rr if x['n']]
    avg=sum(x['ret'] for x in rr)/len(rr);worst=min(x['ret'] for x in rr);dd=sum(x['dd'] for x in rr)/len(rr);pf=sum(min(5,x['pf']) for x in act)/len(act) if act else 0;n=sum(x['n'] for x in rr);pos=sum(x['ret']>0 for x in rr)
    score=avg+.7*worst-.5*dd+.28*(pf-1)+.08*pos-(.25 if n<14 else 0)
    rows.append({'cfg':c,'avg':avg,'worst':worst,'dd':dd,'pf':pf,'n':n,'pos':pos,'score':score})
best=max(rows,key=lambda x:x['score']);hr=[run_cfg(best['cfg'],ch) for ch in hold];ha=[x for x in hr if x['n']];full=run_cfg(best['cfg'],m.DATES);basefull=run_cfg({'strong_risk':.0022,'recovery_risk':.0013,'strong_pos':2},m.DATES)
summary={'best':best,'hold_avg':sum(x['ret'] for x in hr)/len(hr),'hold_worst':min(x['ret'] for x in hr),'hold_pos':sum(x['ret']>0 for x in hr),'hold_n':sum(x['n'] for x in hr),'hold_dd':sum(x['dd'] for x in hr)/len(hr),'hold_pf':sum(min(5,x['pf']) for x in ha)/len(ha) if ha else 0,'full':full,'base_full':basefull}
lines=['# BR-SMART v17 Risk Allocation OOS','v16 giriş ve çıkış motoru sabit. Yalnız STRONG/RECOVERY rejimlerinde pozisyon sayısı ve işlem başı risk ilk 6 geliştirme döneminde seçildi; son 5 dönem untouched holdout. 18 kaba kombinasyon.','','|Strong risk|Recovery risk|Strong pos|Dev Avg|Worst|DD|N|PF|Pos|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in sorted(rows,key=lambda x:x['score'],reverse=True)[:8]:
    c=r['cfg'];lines.append(f'|{100*c["strong_risk"]:.2f}%|{100*c["recovery_risk"]:.2f}%|{c["strong_pos"]}|{r["avg"]:.2f}%|{r["worst"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["pf"]:.2f}|{r["pos"]}/6|')
c=best['cfg'];lines+=['',f'Seçilen: **STRONG risk %{100*c["strong_risk"]:.2f}, RECOVERY risk %{100*c["recovery_risk"]:.2f}, STRONG max pozisyon {c["strong_pos"]}**',f'Holdout: ort **{summary["hold_avg"]:.2f}%**, worst **{summary["hold_worst"]:.2f}%**, + **{summary["hold_pos"]}/{len(hr)}**, N **{summary["hold_n"]}**, DD **{summary["hold_dd"]:.2f}%**, PF **{summary["hold_pf"]:.2f}**.',f'Tüm veri: **{full["ret"]:.2f}%**, DD **{full["dd"]:.2f}%**, PF **{full["pf"]:.2f}**, N **{full["n"]}**. Baz: **{basefull["ret"]:.2f}%**, DD **{basefull["dd"]:.2f}%**, PF **{basefull["pf"]:.2f}**.','','|Holdout|Ret|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---:|']
for i,r in enumerate(hr,1):lines.append(f'|{i}|{r["ret"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["win"]:.1f}%|{r["pf"]:.2f}|')
Path('research/result_risk_opt.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_risk_opt.json').write_text(json.dumps({'rows':rows,'summary':summary,'holdout':hr},indent=2),encoding='utf-8');print('\n'.join(lines))