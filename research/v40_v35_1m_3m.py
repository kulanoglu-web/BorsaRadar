import json
from pathlib import Path
import backtest_indicators as bi
import v35_v30_earlybreak_hybrid as v35

DATES=bi.dates
rows=[]
for fee in [0.001,0.002,0.003]:
    old_bi=bi.FEE; old_v35=v35.FEE
    bi.FEE=fee; v35.FEE=fee
    for name,win,step in [('1AY',22,5),('3AY',66,11)]:
        tests=[]
        for i in range(0,max(0,len(DATES)-win+1),step):
            r=v35.run(DATES[i:i+win],False,True)
            tests.append(r)
        active=[r for r in tests if r['n']>0]
        vals=[r['ret'] for r in active]
        rows.append({
            'fee':fee,'name':name,'win':win,'all':len(tests),'active':len(active),
            'avg':sum(vals)/len(vals) if vals else 0,
            'median':sorted(vals)[len(vals)//2] if vals else 0,
            'worst':min(vals) if vals else 0,'best':max(vals) if vals else 0,
            'positive':sum(x>0 for x in vals),
            'avgdd':sum(r['dd'] for r in active)/len(active) if active else 0,
            'maxdd':max((r['dd'] for r in active),default=0),
            'trades':sum(r['n'] for r in active),
            'avgtrades':sum(r['n'] for r in active)/len(active) if active else 0,
        })
    bi.FEE=old_bi; v35.FEE=old_v35

lines=['# V40 V35 1 Ay / 3 Ay Rolling Test','Sabit V35-C: V30 seçim + EarlyBreak zamanlama + low-breach/ertesi açılış çıkış + kâr koruma. Parametre optimizasyonu yok.','',
'|Maliyet|Dönem|Aktif/Toplam|Ort getiri|Medyan|En kötü|En iyi|Pozitif|Ort DD|Max DD|Ort işlem|',
'|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    lines.append(f"|{r['fee']*100:.2f}%|{r['name']}|{r['active']}/{r['all']}|{r['avg']:.2f}%|{r['median']:.2f}%|{r['worst']:.2f}%|{r['best']:.2f}%|{r['positive']}/{r['active']}|{r['avgdd']:.2f}%|{r['maxdd']:.2f}%|{r['avgtrades']:.1f}|")
base=[r for r in rows if r['fee']==.001]
stress=[r for r in rows if r['fee']==.003]
ok=all(r['active']>0 and r['positive']/r['active']>=.6 and r['avg']>0 for r in base) and all(r['avg']>0 and r['worst']>-12 for r in stress)
lines+=['',f"Karar: **{'GEÇTİ' if ok else 'GEÇMEDİ'}**",'Not: Low breach gün içi emir değildir; günlük barın dip seviyesi görüldükten sonra ertesi açılışta çıkış varsayılır.']
Path('research/result_v40_v35_1m_3m.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_v40_v35_1m_3m.json').write_text(json.dumps({'rows':rows,'pass':ok},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines))