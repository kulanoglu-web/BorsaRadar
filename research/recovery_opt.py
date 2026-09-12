# BR-SMART v18: fixed STRONG engine; test whether/when RECOVERY trades add value
import json
from pathlib import Path
import backtest_br_smart as m
chunks=[m.DATES[i:i+22] for i in range(0,len(m.DATES)-21,22)];dev=chunks[:6];hold=chunks[6:]
base_allowed=m.allowed;base_sig=m.sig
cfgs=[
 {'name':'STRONG_ONLY','recovery':False,'bd':.025,'score':0},
 {'name':'REC_ALL','recovery':True,'bd':.025,'score':0},
 {'name':'REC_SCORE45','recovery':True,'bd':.025,'score':45},
 {'name':'REC_SCORE55','recovery':True,'bd':.025,'score':55},
 {'name':'REC_FAST','recovery':True,'bd':.040,'score':0},
 {'name':'REC_FAST45','recovery':True,'bd':.040,'score':45},
]

def run(c,days):
    def alloc(day):
        br,d,strong,recovery,weak=m.state(day)
        rec=c['recovery'] and br>=.44 and d>=c['bd']
        ok=(strong or rec) and not weak
        return ok,(2 if strong else 1),(.0022 if strong else .0013)
    def sigx(s,i,day):
        z=base_sig(s,i,day)
        if not z:return None
        br,d,strong,recovery,weak=m.state(day)
        if not strong and z[0]<c['score']:return None
        return z
    m.allowed=alloc;m.sig=sigx
    try:return m.sim(days,m.BASE)
    finally:m.allowed=base_allowed;m.sig=base_sig

rows=[]
for c in cfgs:
    dr=[run(c,ch) for ch in dev];act=[x for x in dr if x['n']]
    avg=sum(x['ret'] for x in dr)/len(dr);worst=min(x['ret'] for x in dr);dd=sum(x['dd'] for x in dr)/len(dr);pf=sum(min(5,x['pf']) for x in act)/len(act) if act else 0;n=sum(x['n'] for x in dr);pos=sum(x['ret']>0 for x in dr)
    score=avg+.7*worst-.45*dd+.28*(pf-1)+.08*pos-(.25 if n<12 else 0)
    rows.append({'cfg':c,'avg':avg,'worst':worst,'dd':dd,'pf':pf,'n':n,'pos':pos,'score':score})
best=max(rows,key=lambda x:x['score']);hr=[run(best['cfg'],ch) for ch in hold];ha=[x for x in hr if x['n']];full=run(best['cfg'],m.DATES)
lines=['# BR-SMART v18 Recovery Gate OOS','STRONG girişleri sabit tutuldu. RECOVERY rejiminin kapatılması veya daha seçici açılması ilk 6 geliştirme döneminde karşılaştırıldı; son 5 dönem untouched holdout.','','|Model|Dev Avg|Worst|DD|N|PF|Pos|','|---|---:|---:|---:|---:|---:|---:|']
for r in sorted(rows,key=lambda x:x['score'],reverse=True):lines.append(f'|{r["cfg"]["name"]}|{r["avg"]:.2f}%|{r["worst"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["pf"]:.2f}|{r["pos"]}/6|')
ha_pf=sum(min(5,x['pf']) for x in ha)/len(ha) if ha else 0
lines+=['',f'Seçilen: **{best["cfg"]["name"]}**',f'Holdout: ort **{sum(x["ret"] for x in hr)/len(hr):.2f}%**, worst **{min(x["ret"] for x in hr):.2f}%**, + **{sum(x["ret"]>0 for x in hr)}/{len(hr)}**, N **{sum(x["n"] for x in hr)}**, DD **{sum(x["dd"] for x in hr)/len(hr):.2f}%**, PF **{ha_pf:.2f}**.',f'Tüm veri: **{full["ret"]:.2f}%**, DD **{full["dd"]:.2f}%**, PF **{full["pf"]:.2f}**, N **{full["n"]}**.','','|Holdout|Ret|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---:|']
for i,r in enumerate(hr,1):lines.append(f'|{i}|{r["ret"]:.2f}%|{r["dd"]:.2f}%|{r["n"]}|{r["win"]:.1f}%|{r["pf"]:.2f}|')
Path('research/result_recovery_opt.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_recovery_opt.json').write_text(json.dumps({'rows':rows,'best':best,'holdout':hr,'full':full},indent=2),encoding='utf-8');print('\n'.join(lines))