# Diagnostic only: label pre-entry features by next-5-day outcome. No trading optimization here.
import json
from pathlib import Path
import backtest_indicators as bi

rows=[]
for day in bi.dates:
    br=bi.breadth_cache.get(day,0)
    if br<.35:continue
    for s,a in bi.data.items():
        i=bi.bysym[s].get(day)
        if i is None or i<65 or i+5>=len(a):continue
        turn,vol,j=bi.quality(s,i)
        if turn<120_000_000 or vol<120_000 or j>=2:continue
        f=bi.feat(s,i);p=bi.feat(s,i-1);m=f['m'];pm=p['m'];bar=a[i-1]
        if m['trap'] or f['rv']<1.05 or f['cmf']<-.02:continue
        hist=m['mac']-m['ms'];phist=pm['mac']-pm['ms']
        if hist<=phist:return_none if False else None
        if hist<=phist:continue
        entry=a[i]['o'];future=a[i:i+5];mfe=max(x['h'] for x in future)/entry-1;mae=min(x['l'] for x in future)/entry-1;ret5=future[-1]['c']/entry-1
        rng=max(.001,bar['h']-bar['l']);cp=(bar['c']-bar['l'])/rng
        atr=max(m['atr'],bar['c']*.01);dist=(bar['c']/f['e20']-1)/max(atr/bar['c'],.006)
        rows.append({'s':s,'day':day,'rv':f['rv'],'cmf':f['cmf'],'br':br,'cp':cp,'rsi':f['rsi'],'adx':f['adx'],'slope':f['slope'],'mom3':f['mom3'],'acc':f['acc'],'histDelta':hist-phist,'dist20':dist,'mfe5':mfe,'mae5':mae,'ret5':ret5,'good':mfe>=.05 and mae>-.035})

features=['rv','cmf','br','cp','rsi','adx','slope','mom3','acc','histDelta','dist20']
def avg(rr,k):return sum(x[k] for x in rr)/len(rr) if rr else 0
g=[x for x in rows if x['good']];b=[x for x in rows if not x['good']]
sep=[]
for k in features:
    ga,ba=avg(g,k),avg(b,k);scale=max(1e-9,abs(ga)+abs(ba));sep.append((abs(ga-ba)/scale,k,ga,ba))
sep.sort(reverse=True)
summary={'n':len(rows),'good':len(g),'base_rate':len(g)/len(rows) if rows else 0,'features':[{'name':k,'good_avg':ga,'bad_avg':ba,'sep':sc} for sc,k,ga,ba in sep]}
lines=['# Entry Feature Study',f'VOL-benzeri erken adaylar: **{len(rows)}**, 5 gün içinde +%5 görüp -%3.5 altına inmeyen iyi aday: **{len(g)} ({summary["base_rate"]:.1%})**.','','|Feature|Good avg|Bad avg|Separation|','|---|---:|---:|---:|']
for sc,k,ga,ba in sep:lines.append(f'|{k}|{ga:.5f}|{ba:.5f}|{sc:.3f}|')
Path('research/result_entry_features.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_entry_features.json').write_text(json.dumps({'summary':summary,'rows':rows},ensure_ascii=False),encoding='utf-8');print('\n'.join(lines))