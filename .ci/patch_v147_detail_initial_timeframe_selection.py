from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# The fast detail preview renders the current 3-month preview, so the highlighted
# timeframe must be 3 ay (index 8), not 1 gun (index 5). Clicked timeframes are
# subsequently rendered by renderStockDetail using x.equals(frame).
old='Button tb=button(x,i==5?Color.rgb(25,105,210):Color.rgb(49,55,63));'
new='Button tb=button(x,i==8?Color.rgb(25,105,210):Color.rgb(49,55,63));'
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('v147 fast timeframe selection anchor missing')
# Guard against reintroducing the misleading hard-coded 1-day highlight.
a=s.find('private void renderFastTechnicalDetail')
b=s.find('private void renderStockDetail',a)
q=s[a:b]
if 'i==5?Color.rgb(25,105,210)' in q: raise SystemExit('v147 stale 1-day highlight remains')
if 'i==8?Color.rgb(25,105,210)' not in q: raise SystemExit('v147 3-month highlight missing')
p.write_text(s,encoding='utf-8')
print('v147 initial preview selection matches 3 ay')
