# Transaction-cost stress for fixed BR-SMART v15 DYNAMIC. No parameter fitting.
import json
from pathlib import Path
import backtest_br_smart as m

rows=[]
chunks=[m.DATES[i:i+22] for i in range(0,len(m.DATES)-21,22)]
hold=chunks[6:]
base_fee=m.FEE
for fee in (.001,.0015,.002,.003):
    m.FEE=fee
    full=m.sim('DYNAMIC',m.DATES)
    hr=[m.sim('DYNAMIC',ch) for ch in hold]
    active=[x for x in hr if x['n']]
    rows.append({
        'fee_side':fee,
        'round_trip_pct':fee*200,
        'full_ret':full['ret'],'full_dd':full['dd'],'full_pf':full['pf'],'full_n':full['n'],
        'hold_avg':sum(x['ret'] for x in hr)/len(hr) if hr else 0,
        'hold_worst':min((x['ret'] for x in hr),default=0),
        'hold_pos':sum(x['ret']>0 for x in hr),'hold_n':sum(x['n'] for x in hr),
        'hold_dd':sum(x['dd'] for x in hr)/len(hr) if hr else 0,
        'hold_pf':sum(min(5,x['pf']) for x in active)/len(active) if active else 0
    })
m.FEE=base_fee
lines=['# BR-SMART DYNAMIC Cost Stress','Sabit v15 DYNAMIC sinyalleri; yalnız işlem maliyeti artırıldı. Ücret her alımda ve satımda ayrı uygulanır. TUPRS/savunma hariç.','', '|Tek yön maliyet|Yakl. round-trip|Full Ret|Full DD|Full PF|Full N|Hold Avg|Hold Worst|Hold +|Hold N|Hold DD|Hold PF|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'|{r["fee_side"]*100:.2f}%|{r["round_trip_pct"]:.2f}%|{r["full_ret"]:.2f}%|{r["full_dd"]:.2f}%|{r["full_pf"]:.2f}|{r["full_n"]}|{r["hold_avg"]:.2f}%|{r["hold_worst"]:.2f}%|{r["hold_pos"]}/{len(hold)}|{r["hold_n"]}|{r["hold_dd"]:.2f}%|{r["hold_pf"]:.2f}|')
Path('research/result_cost_stress.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_cost_stress.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('\n'.join(lines))
