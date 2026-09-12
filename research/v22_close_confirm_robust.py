# BR-SMART v22: validate close-confirmed stop without retuning entry parameters
import json
from pathlib import Path
import v21_long_wf_diagnostics as v21

DATES=v21.DATES

def stats(rr):
    active=[x for x in rr if x['n']]
    return {
        'periods':len(rr),
        'avg':sum(x['ret'] for x in rr)/len(rr) if rr else 0,
        'worst':min((x['ret'] for x in rr),default=0),
        'pos':sum(x['ret']>0 for x in rr),
        'dd':sum(x['dd'] for x in rr)/len(rr) if rr else 0,
        'n':sum(x['n'] for x in rr),
        'win':sum(x['win']*x['n'] for x in rr)/sum(x['n'] for x in rr) if sum(x['n'] for x in rr) else 0,
        'pf_capped':sum(min(5,x['pf']) for x in active)/len(active) if active else 0,
    }

# 1) Fixed 22-day rolling OOS folds after first 4 chunks.
folds=[DATES[i:i+22] for i in range(0,len(DATES)-21,22)]
rolling={}
for name,cc in [('INTRADAY',False),('CLOSECONF',True)]:
    rr=[]
    for j in range(4,len(folds)):
        x=v21.run(folds[j],close_confirm=cc)
        rr.append({'fold':j+1,**{k:x[k] for k in ('ret','dd','n','win','pf')}})
    rolling[name]={'rows':rr,'stats':stats(rr)}

# 2) Window sensitivity: predeclared 15/22/30 days, three offsets.
windows=[]
for w in (15,22,30):
  for off in (0,5,10):
    periods=[DATES[i:i+w] for i in range(off,len(DATES)-w+1,w)]
    for name,cc in [('INTRADAY',False),('CLOSECONF',True)]:
        rr=[v21.run(p,close_confirm=cc) for p in periods]
        windows.append({'model':name,'w':w,'off':off,**stats(rr)})

# 3) Cost stress: same signals and same stop logic, no parameter changes.
costs=[]
for fee in (.001,.0015,.002,.003):
    for name,cc in [('INTRADAY',False),('CLOSECONF',True)]:
        full=v21.run(DATES,fee=fee,close_confirm=cc)
        rr=[v21.run(folds[j],fee=fee,close_confirm=cc) for j in range(4,len(folds))]
        st=stats(rr)
        costs.append({'model':name,'fee':fee,'full_ret':full['ret'],'full_dd':full['dd'],'full_pf':full['pf'],'full_n':full['n'],**{('wf_'+k):v for k,v in st.items()}})

# 4) Recovery consistency on close-confirm trades vs baseline.
full_base=v21.run(DATES,close_confirm=False)
full_cc=v21.run(DATES,close_confirm=True)

def trade_diag(x):
    tr=x['trades']; wins=[t for t in tr if t['pnl']>0]; losses=[t for t in tr if t['pnl']<0]
    def avg(a,k):return sum(t[k] for t in a)/len(a) if a else 0
    return {'n':len(tr),'avg_mfe':avg(tr,'mfe'),'avg_mae':avg(tr,'mae'),'win_mfe':avg(wins,'mfe'),'loss_mfe':avg(losses,'mfe'),'win_mae':avg(wins,'mae'),'loss_mae':avg(losses,'mae')}

diag={'INTRADAY':trade_diag(full_base),'CLOSECONF':trade_diag(full_cc)}

lines=['# BR-SMART v22 Close-Confirmed Stop Robustness',
       'v20 girişleri sabit (ADX<=35, RVOL>=1.35). Stop mantığı dışında hiçbir şey yeniden optimize edilmedi. TUPRS/savunma hariç; maliyet dahil.',
       '', '## Fixed 22-day rolling OOS',
       '|Model|Avg|Worst|Positive|DD|N|Win|PF(capped avg)|','|---|---:|---:|---:|---:|---:|---:|---:|']
for name in ('INTRADAY','CLOSECONF'):
    s=rolling[name]['stats'];lines.append(f'|{name}|{s["avg"]:.2f}%|{s["worst"]:.2f}%|{s["pos"]}/{s["periods"]}|{s["dd"]:.2f}%|{s["n"]}|{s["win"]:.1f}%|{s["pf_capped"]:.2f}|')
lines+=['','## Fold-by-fold close-confirm','|Fold|Ret|DD|N|Win|PF|','|---:|---:|---:|---:|---:|---:|']
for x in rolling['CLOSECONF']['rows']: lines.append(f'|{x["fold"]}|{x["ret"]:.2f}%|{x["dd"]:.2f}%|{x["n"]}|{x["win"]:.1f}%|{x["pf"]:.2f}|')
lines+=['','## Window sensitivity','|Model|W|Offset|Avg|Worst|Positive|N|DD|PF|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in windows:lines.append(f'|{x["model"]}|{x["w"]}|{x["off"]}|{x["avg"]:.2f}%|{x["worst"]:.2f}%|{x["pos"]}/{x["periods"]}|{x["n"]}|{x["dd"]:.2f}%|{x["pf_capped"]:.2f}|')
lines+=['','## Cost stress','|Model|One-way fee|Round-trip ~|Full Ret|DD|PF|N|WF Avg|Worst|PF|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in costs:lines.append(f'|{x["model"]}|{100*x["fee"]:.2f}%|{200*x["fee"]:.2f}%|{x["full_ret"]:.2f}%|{x["full_dd"]:.2f}%|{x["full_pf"]:.2f}|{x["full_n"]}|{x["wf_avg"]:.2f}%|{x["wf_worst"]:.2f}%|{x["wf_pf_capped"]:.2f}|')
lines+=['','## Trade diagnostics']
for name in ('INTRADAY','CLOSECONF'):
    d=diag[name];lines.append(f'{name}: N **{d["n"]}**, avg MFE **{d["avg_mfe"]:.2f}%**, avg MAE **{d["avg_mae"]:.2f}%**, winner MFE **{d["win_mfe"]:.2f}%**, loser MFE **{d["loss_mfe"]:.2f}%**, winner MAE **{d["win_mae"]:.2f}%**, loser MAE **{d["loss_mae"]:.2f}%**.')

out={'rolling':rolling,'windows':windows,'costs':costs,'diag':diag,'full':{'intraday':{k:full_base[k] for k in ('ret','dd','n','win','pf')},'closeconf':{k:full_cc[k] for k in ('ret','dd','n','win','pf')}}}
Path('research/result_v22_close_confirm.md').write_text('\n'.join(lines),encoding='utf-8')
Path('research/result_v22_close_confirm.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('\n'.join(lines))
