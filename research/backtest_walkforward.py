import json
from pathlib import Path
import backtest_entry_v3 as e
import backtest_indicators as bi

# True rolling walk-forward: choose parameters ONLY from older windows, then test the next untouched window.
# WINDOWS are newest->oldest. Train older periods, test immediately newer period.
base=(.50,.38,74,74,.005,.0025,3,1)
configs=[]
for rel in (0,.005,.01):
 for ext in (2.5,3.0,3.5):
  for vp in (.85,1.0,1.1):
   for conf in (False,True):configs.append(base+(rel,ext,vp,conf))

def metrics(cfg, windows):
 rs=[e.simulate(cfg,w) for w in windows];active=[x for x in rs if x['n']]
 avg=sum(x['ret'] for x in rs)/len(rs);worst=min(x['ret'] for x in rs);dd=sum(x['dd'] for x in rs)/len(rs);n=sum(x['n'] for x in rs);pos=sum(x['ret']>0 for x in rs);pf=sum(min(3,x['pf']) for x in active)/len(active) if active else 0
 # Penalize inactivity and downside. Selection score is train-only.
 score=avg+.8*worst-.55*dd+.45*(pf-1)+.12*pos+min(.25,n/30)
 return score,{'avg':avg,'worst':worst,'dd':dd,'n':n,'pos':pos,'pf':pf}

# oldest indices: 3,2,1,0. First fold trains oldest 2 -> tests window 1; second trains oldest 3 -> tests newest 0.
folds=[([bi.WINDOWS[3],bi.WINDOWS[2]],bi.WINDOWS[1]),([bi.WINDOWS[3],bi.WINDOWS[2],bi.WINDOWS[1]],bi.WINDOWS[0])]
out=[]
for k,(train,test) in enumerate(folds,1):
 ranked=[]
 for cfg in configs:
  sc,m=metrics(cfg,train);ranked.append((sc,cfg,m))
 ranked.sort(reverse=True,key=lambda x:x[0]);sc,cfg,tm=ranked[0];hold=e.simulate(cfg,test)
 out.append({'fold':k,'cfg':cfg,'train':tm,'holdout':hold})

rets=[x['holdout']['ret'] for x in out];dds=[x['holdout']['dd'] for x in out];ns=[x['holdout']['n'] for x in out];wins=sum(x['holdout']['n']*x['holdout']['win']/100 for x in out);n=sum(ns)
# Aggregate PF from fold PF is only approximate; report weighted by trade count rather than claiming pooled trade PF.
pf=sum(min(5,x['holdout']['pf'])*x['holdout']['n'] for x in out)/n if n else 0
summary={'avg_holdout_return':sum(rets)/len(rets),'worst_holdout':min(rets),'avg_dd':sum(dds)/len(dds),'trades':n,'win':100*wins/n if n else 0,'weighted_pf':pf,'positive_folds':sum(x>0 for x in rets)}
lines=['# BR Walk-Forward Holdout Test','Parametre seçimi yalnızca geçmiş dönemlerde yapıldı; hemen sonraki dönem seçim sırasında görülmedi. TUPRS/savunma hariç, lookahead yok, maliyet dahil.','',f'Holdout ortalama getiri **{summary["avg_holdout_return"]:.2f}%**, en kötü **{summary["worst_holdout"]:.2f}%**, ort DD **{summary["avg_dd"]:.2f}%**, işlem **{n}**, win **{summary["win"]:.1f}%**, ağırlıklı PF **{pf:.2f}**, pozitif fold **{summary["positive_folds"]}/2**.','','|Fold|Train N|Train Avg|Seçilen Rel3|ATR uz.|VolPersist|Teyit|Holdout Getiri|DD|N|Win|PF|','|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|']
for x in out:
 c=x['cfg'];t=x['train'];h=x['holdout'];lines.append(f'|{x["fold"]}|{t["n"]}|{t["avg"]:.2f}%|{c[8]*100:.1f}%|{c[9]:.1f}|{c[10]:.2f}|{c[11]}|{h["ret"]:.2f}%|{h["dd"]:.2f}%|{h["n"]}|{h["win"]:.1f}%|{h["pf"]:.2f}|')
Path('research/result_walkforward.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_walkforward.json').write_text(json.dumps({'summary':summary,'folds':out},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))