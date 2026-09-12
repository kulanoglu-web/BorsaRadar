import json
from pathlib import Path
import v35_v30_earlybreak_hybrid as v35

DATES=v35.DATES
BASE_FEE=v35.FEE

def windows(length,step=11):
    return [DATES[i:i+length] for i in range(0,len(DATES)-length+1,step)]

def summarize(rr):
    active=[x for x in rr if x['n']>0]
    return {
      'windows':len(rr),'active':len(active),
      'avg_all':sum(x['ret'] for x in rr)/len(rr) if rr else 0,
      'avg_active':sum(x['ret'] for x in active)/len(active) if active else 0,
      'median_active':sorted([x['ret'] for x in active])[len(active)//2] if active else 0,
      'worst_active':min((x['ret'] for x in active),default=0),
      'positive_active':sum(x['ret']>0 for x in active),
      'zero':sum(x['n']==0 for x in rr),
      'avg_dd':sum(x['dd'] for x in active)/len(active) if active else 0,
      'max_dd':max((x['dd'] for x in active),default=0),
      'trades':sum(x['n'] for x in rr),
    }

rows=[]
for fee in (.001,.002,.003):
    v35.FEE=fee
    for length in (44,66):
        rr=[v35.run(w,False,True) for w in windows(length)]
        rows.append({'fee':fee,'length':length,'stats':summarize(rr),'folds':rr})
v35.FEE=BASE_FEE

# Require meaningful activity and repeatability at normal cost, and survival at 0.30% cost.
norm=[r for r in rows if r['fee']==.001]
stress=[r for r in rows if r['fee']==.003]
def pass_row(r,strict=True):
    s=r['stats']; active=max(1,s['active']); pos=s['positive_active']/active
    if strict:
        return s['active']>=4 and pos>=.60 and s['avg_active']>0 and s['worst_active']>-10
    return s['avg_active']>0 and s['worst_active']>-12
robust=all(pass_row(r,True) for r in norm) and all(pass_row(r,False) for r in stress)

lines=['# v37 V35 Rolling Stability','Sabit V35-C modelini 44 ve 66 işlem günlük **kayan pencerelerde** (11 gün adım) tekrar test eder. Böylece önceki disjoint fold testindeki boş dönemlerin sonucu gizlemesi azaltılır.','',
'|Maliyet|Pencere|Toplam pencere|Aktif pencere|Sıfır işlem|Aktif ort|Aktif medyan|En kötü aktif|Pozitif aktif|Ort DD|Max DD|Toplam işlem|',
'|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    s=r['stats']
    lines.append(f"|{100*r['fee']:.2f}%|{r['length']}g|{s['windows']}|{s['active']}|{s['zero']}|{s['avg_active']:.2f}%|{s['median_active']:.2f}%|{s['worst_active']:.2f}%|{s['positive_active']}/{s['active']}|{s['avg_dd']:.2f}%|{s['max_dd']:.2f}%|{s['trades']}|")
lines+=['',f"## Karar\nRolling-stability: **{'GEÇTİ' if robust else 'GEÇMEDİ'}**.",
'Geçme kuralı normal maliyette aktif pencerelerin en az %60’ının pozitif olması, aktif ortalamanın pozitif kalması ve en kötü aktif pencerenin -%10’dan kötü olmamasıdır. %0,30 maliyet stresinde ortalama pozitif ve en kötü pencere -%12 üzerinde kalmalıdır.']
Path('research/result_v37_v35_rolling_stability.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_v37_v35_rolling_stability.json').write_text(json.dumps({'rows':rows,'robust':robust},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines))
