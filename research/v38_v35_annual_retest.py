import json
from pathlib import Path
import backtest_indicators as bi
import v35_v30_earlybreak_hybrid as v35

DATES = bi.dates
if not DATES:
    raise SystemExit('No dates')

# Fixed model: V35-C only, no parameter retuning.
base_fee = bi.FEE
rows=[]
for fee in [0.001,0.002,0.003]:
    bi.FEE=fee
    full=v35.run(DATES, False, True)
    # rolling windows: 44,66,88 trading days with 11-day step
    for win in [44,66,88]:
        windows=[]
        for i in range(0,max(0,len(DATES)-win+1),11):
            r=v35.run(DATES[i:i+win],False,True)
            windows.append(r)
        active=[r for r in windows if r['n']>0]
        rows.append({
            'fee':fee,'win':win,'full_ret':full['ret'],'full_dd':full['dd'],'pf':full['pf'],'winrate':full['win'],'n':full['n'],
            'windows':len(windows),'active':len(active),
            'active_avg':sum(r['ret'] for r in active)/len(active) if active else 0,
            'active_median':sorted([r['ret'] for r in active])[len(active)//2] if active else 0,
            'worst':min([r['ret'] for r in active]) if active else 0,
            'positive':sum(r['ret']>0 for r in active),
            'max_window_dd':max([r['dd'] for r in active]) if active else 0,
        })
bi.FEE=base_fee

lines=['# V35 Hybrid Annual Revalidation',f'Date range: {v35.dt(DATES[0])} -> {v35.dt(DATES[-1])}',
       'Fixed V35-C model; no parameter tuning. TUPRS + existing defense exclusions remain.',
       '', '|Fee|Window|Full ret|Full DD|PF|Win|Trades|Active/All|Active avg|Worst active|Positive active|Max window DD|',
       '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    lines.append(f"|{r['fee']*100:.2f}%|{r['win']}d|{r['full_ret']:.2f}%|{r['full_dd']:.2f}%|{r['pf']:.2f}|{r['winrate']:.1f}%|{r['n']}|{r['active']}/{r['windows']}|{r['active_avg']:.2f}%|{r['worst']:.2f}%|{r['positive']}/{r['active']}|{r['max_window_dd']:.2f}%|")

normal=[r for r in rows if r['fee']==0.001]
stress=[r for r in rows if r['fee']==0.003]
pass_normal=all((r['active']==0 or (r['positive']/r['active']>=0.60 and r['active_avg']>0 and r['worst']>-10)) for r in normal)
pass_stress=all((r['active']==0 or (r['active_avg']>0 and r['worst']>-12)) for r in stress)
lines += ['', f"Verdict: **{'PASS' if pass_normal and pass_stress else 'FAIL'}**", 'This is historical simulation, not a profit guarantee.']

Path('research/result_v38_v35_annual_retest.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_v38_v35_annual_retest.json').write_text(json.dumps({'rows':rows,'pass':pass_normal and pass_stress},ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines))
