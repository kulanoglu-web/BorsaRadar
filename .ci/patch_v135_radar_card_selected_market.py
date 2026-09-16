from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
# v135: the scan card above the button was still driven by portfolio primaryMarket().
# Make the whole visible scan card use the selected Radar market instead.
q=q.replace('int pm=primaryMarket(); String[] universe=marketSymbols(pm);','int pm=radarMarketChoiceMain; String[] universe=radarUniverse();')
q=q.replace('top.addView(bold(marketName(pm)+" • "+L("öncelikli tarama","priorisierte Analyse","priority scan"),19,NAVY));','top.addView(bold(radarTitleFor(pm)+" • "+L("öncelikli tarama","priorisierte Analyse","priority scan"),19,NAVY));')
q=q.replace('"Das Borsa-Istanbul-Universum wird gescannt."','"Das ausgewählte Marktuniversum wird nur nach Tippen auf Scannen durchsucht."')
q=q.replace('"The Borsa Istanbul universe is scanned."','"The selected market universe is scanned only after pressing Scan."')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
# strict final check of requested area
s=p.read_text(encoding='utf-8');a=s.find('private void showRadar()');b=s.find('\n    private ',a+20);q=s[a:b]
checks={
 'no portfolio primary market in showRadar':'int pm=primaryMarket()' not in q,
 'selected radar market drives card':'int pm=radarMarketChoiceMain;' in q,
 'selected radar universe drives progress':'String[] universe=radarUniverse();' in q,
 'card label uses radar title':'bold(radarTitleFor(pm)' in q,
}
for k,v in checks.items(): print('v135',k,v)
if not all(checks.values()): raise SystemExit('v135 verification FAILED')
