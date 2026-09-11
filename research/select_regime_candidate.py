from pathlib import Path
import json
import backtest_regime_v2 as r

# Prefer practical candidates: enough trades, PF>1, bounded worst period, at least 3 active periods.
def active_periods(x): return sum(1 for z in x['rs'] if z['n']>0)

def choose():
    tiers=[
        lambda x: x['n']>=12 and active_periods(x)>=3 and x['pf']>1 and x['worst']>=-1.5,
        lambda x: x['n']>=10 and active_periods(x)>=3 and x['pf']>1 and x['worst']>=-2.0,
        lambda x: x['n']>=8 and active_periods(x)>=2 and x['pf']>1 and x['worst']>=-2.0,
    ]
    for i,f in enumerate(tiers,1):
        xs=[x for x in r.rows if f(x)]
        if xs:
            xs.sort(key=lambda x:(x['avg']-.55*x['avgdd']+.35*(x['pf']-1)+.08*x['n'],x['avg']),reverse=True)
            return i,xs[0],xs[:15]
    xs=sorted(r.rows,key=lambda x:(x['n']>=8,x['pf'],x['avg']-.5*x['avgdd']),reverse=True)
    return 9,xs[0],xs[:15]

tier,best,top=choose();c=best['cfg']
lines=['# BR-Regime Pratik Aday Seçimi',f'Tier {tier}. Amaç: az işlemli aşırı seçici modeli değil, yeterli işlem + PF>1 + kontrollü drawdown dengesini seçmek.','',f'ADAY: bull>={c[0]:.2f}, side>={c[1]:.2f}, bull skor>={c[2]}, side skor>={c[3]}, risk %{c[4]*100:.2f}/%{c[5]*100:.2f}, maxpos {c[6]}/{c[7]}.',f'Ort getiri **%{best["avg"]:.2f}**, en kötü **%{best["worst"]:.2f}**, ort DD **%{best["avgdd"]:.2f}**, işlem **{best["n"]}**, aktif dönem **{active_periods(best)}/4**, pozitif **{best["pos"]}/4**, PF **{best["pf"]:.2f}**.','', '## Dönemler','|Dönem|Getiri|DD|N|Win|PF|','|---|---:|---:|---:|---:|---:|']
for i,z in enumerate(best['rs'],1): lines.append(f'|{i}|{z["ret"]:.2f}%|{z["dd"]:.2f}%|{z["n"]}|{z["win"]:.1f}%|{z["pf"]:.2f}|')
lines+=['','## Alternatifler','|Bull|Side|TB|TS|Risk B/S|Pos B/S|Avg|Worst|DD|N|Aktif|PF|','|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|']
for x in top:
    c=x['cfg'];lines.append(f'|{c[0]:.2f}|{c[1]:.2f}|{c[2]}|{c[3]}|{c[4]*100:.2f}/{c[5]*100:.2f}%|{c[6]}/{c[7]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["avgdd"]:.2f}%|{x["n"]}|{active_periods(x)}/4|{x["pf"]:.2f}|')
Path('research/result_regime_candidate.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_regime_candidate.json').write_text(json.dumps({'tier':tier,'best':best,'top':top},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines),flush=True)