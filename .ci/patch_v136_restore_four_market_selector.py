from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
# Remove any stale selector render in showRadar, then insert exactly one directly below shell/header.
q=q.replace('content.addView(radarMarketSelector(false));spacer(8);','')
# shell call may be dynamic after v134; insert after first shell(...) statement in showRadar.
pos=q.find('shell(')
if pos<0: raise SystemExit('showRadar shell missing')
semi=q.find(';',pos)
if semi<0: raise SystemExit('showRadar shell terminator missing')
q=q[:semi+1]+'\n        content.addView(radarMarketSelector(false));spacer(8);'+q[semi+1:]
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
# Verify selector itself still contains all four markets and showRadar renders it exactly once.
s=p.read_text(encoding='utf-8')
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
b=s.find('\n    private ',a+20)
sel=s[a:b]
a2=s.find('private void showRadar()');b2=s.find('\n    private ',a2+20);rad=s[a2:b2]
checks={
 'selector has four labels':'String[] labels={"BIST","ALMANYA","ABD","TÜMÜ"};' in sel,
 'main selector visible once':rad.count('content.addView(radarMarketSelector(false));')==1,
 'selector does not auto scan':'scanRadar()' not in sel and 'scanShortTerm(' not in sel,
 'main choice persisted':'radar_market_main' in sel,
}
for k,v in checks.items(): print('v136',k,v)
if not all(checks.values()): raise SystemExit('v136 verification FAILED')
