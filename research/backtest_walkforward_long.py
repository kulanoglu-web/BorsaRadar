import json
from pathlib import Path
import backtest_entry_v3 as e
import backtest_indicators as bi

# Extended rolling walk-forward across all available 6-month history.
# 31-day calendar windows, oldest -> newest. Each fold trains ONLY on older windows.
DAY=86400
span=int((bi.END-min(bi.dates))/DAY)
windows=[]
start=0
while start+31<=span:
    windows.append((start,start+31));start+=31
windows=list(reversed(windows)) # oldest -> newest
base=(.50,.38,74,74,.005,.0025,3,1)
configs=[base+(rel,ext,vp,conf) for rel in (0,.005,.01) for ext in (2.5,3.0,3.5) for vp in (.85,1.0,1.1) for conf in (False,True)]

def train_score(cfg,ws):
    rs=[e.simulate(cfg,w) for w in ws];active=[x for x in rs if x['n']]
    avg=sum(x['ret'] for x in rs)/len(rs);worst=min(x['ret'] for x in rs);dd=sum(x['dd'] for x in rs)/len(rs);n=sum(x['n'] for x in rs);pf=sum(min(3,x['pf']) for x in active)/len(active) if active else 0
    return avg+.8*worst-.55*dd+.45*(pf-1)+min(.3,n/35)

folds=[]
# Need at least 2 older windows; then roll one untouched month at a time.
for idx in range(2,len(windows)):
    train=windows[:idx];test=windows[idx]
    best=max(configs,key=lambda c:train_score(c,train));h=e.simulate(best,test)
    folds.append({'fold':len(folds)+1,'train_windows':len(train),'cfg':best,'holdout':h})
rets=[x['holdout']['ret'] for x in folds];n=sum(x['holdout']['n'] for x in folds);wins=sum(x['holdout']['n']*x['holdout']['win']/100 for x in folds)
pf=sum(min(5,x['holdout']['pf'])*x['holdout']['n'] for x in folds)/n if n else 0
summary={'months':len(windows),'folds':len(folds),'avg':sum(rets)/len(rets) if rets else 0,'worst':min(rets) if rets else 0,'avgdd':sum(x['holdout']['dd'] for x in folds)/len(folds) if folds else 0,'trades':n,'win':100*wins/n if n else 0,'weighted_pf':pf,'positive':sum(x>0 for x in rets)}
lines=['# BR Extended Walk-Forward',f'Kullanılabilir 6 aylık veri, {len(windows)} adet 31-gün pencere, {len(folds)} rolling holdout. Parametre her foldta yalnız geçmişten seçildi. TUPRS/savunma hariç.','',f'Ort holdout **{summary["avg"]:.2f}%**, en kötü **{summary["worst"]:.2f}%**, ort DD **{summary["avgdd"]:.2f}%**, işlem **{n}**, win **{summary["win"]:.1f}%**, ağırlıklı PF **{pf:.2f}**, pozitif **{summary["positive"]}/{len(folds)}**.','','|Fold|Train ay|Rel3|ATR|VolPersist|Teyit|Getiri|DD|N|Win|PF|','|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|']
for x in folds:
 c=x['cfg'];h=x['holdout'];lines.append(f'|{x["fold"]}|{x["train_windows"]}|{c[8]*100:.1f}%|{c[9]:.1f}|{c[10]:.2f}|{c[11]}|{h["ret"]:.2f}%|{h["dd"]:.2f}%|{h["n"]}|{h["win"]:.1f}%|{h["pf"]:.2f}|')
Path('research/result_walkforward_long.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_walkforward_long.json').write_text(json.dumps({'summary':summary,'folds':folds},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))