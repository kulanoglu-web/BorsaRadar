import json
from pathlib import Path
import v35_v30_earlybreak_hybrid as v35

DATES=v35.DATES
BASE_FEE=v35.FEE
VARIANT=('C intraday-stop+guard',False,True)

def folds(n):
    return [DATES[i:i+n] for i in range(0,len(DATES)-n+1,n)]

def stats(xs):
    return {
        'avg':sum(x['ret'] for x in xs)/len(xs) if xs else 0,
        'worst':min((x['ret'] for x in xs),default=0),
        'best':max((x['ret'] for x in xs),default=0),
        'pos':sum(x['ret']>0 for x in xs),
        'nfold':len(xs),
        'avgdd':sum(x['dd'] for x in xs)/len(xs) if xs else 0,
        'maxdd':max((x['dd'] for x in xs),default=0),
        'trades':sum(x['n'] for x in xs),
    }

rows=[]
for fee in (0.001,0.002,0.003):
    v35.FEE=fee
    full=v35.run(DATES,False,True)
    for win in (44,66):
        rr=[v35.run(ch,False,True) for ch in folds(win)]
        st=stats(rr)
        rows.append({'fee':fee,'window':win,'full':full,'folds':rr,'stats':st})

# restore
v35.FEE=BASE_FEE

# Robustness grade: no optimization, fixed v35-C logic.
base44=next(r for r in rows if r['fee']==.001 and r['window']==44)
base66=next(r for r in rows if r['fee']==.001 and r['window']==66)
stress44=next(r for r in rows if r['fee']==.003 and r['window']==44)
stress66=next(r for r in rows if r['fee']==.003 and r['window']==66)
robust=(base44['stats']['avg']>0 and base66['stats']['avg']>0 and stress44['full']['ret']>0 and stress66['full']['ret']>0)

def pct(x):return f'{x:.2f}%'
lines=['# v36 V35 Hybrid Stress Test',
       'Sabit model: **V30 seçim + EarlyBreak giriş + intraday ATR/trailing stop + kâr koruma**. Bu testte parametre seçimi yapılmadı; yalnız pencere ve işlem maliyeti değiştirildi.',
       'TUPRS + savunma hisseleri hariç. Sinyal kapanışta, giriş ertesi açılışta; stop mevcut pozisyonun önceden bilinen trailing seviyesine göre uygulanır.','',
       '|Maliyet (tek yön)|Pencere|Full getiri|Full DD|PF|Win|İşlem|Fold ort|En kötü fold|Pozitif fold|Ort DD|En yüksek fold DD|',
       '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    f=r['full'];s=r['stats']
    lines.append(f"|{r['fee']*100:.2f}%|{r['window']} gün|{f['ret']:.2f}%|{f['dd']:.2f}%|{f['pf']:.2f}|{f['win']:.1f}%|{f['n']}|{s['avg']:.2f}%|{s['worst']:.2f}%|{s['pos']}/{s['nfold']}|{s['avgdd']:.2f}%|{s['maxdd']:.2f}%|")
lines+=['',f"## Sonuç\nRobustluk kontrolü: **{'GEÇTİ' if robust else 'GEÇMEDİ'}**.",
        '44/66 günlük pencerelerde ortalama getiri, en kötü dönem ve maliyet stresine birlikte bakıldı. Tek bir yıllık toplam getiriye göre karar verilmedi.']
Path('research/result_v36_v35_stress.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_v36_v35_stress.json').write_text(json.dumps({'rows':rows,'robust':robust},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines))
