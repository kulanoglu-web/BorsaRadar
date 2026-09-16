from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
# The text ABOVE the main scan card is the shell subtitle. It must follow the selected Radar market.
# Do not leave the old static BIST wording in this screen.
q=q.replace('shell("Tüm Borsa İstanbul Radarı")','shell(radarTitleFor(radarMarketChoiceMain)+" Radarı")')
q=q.replace('shell(L("Ana Borsa Radarı","Hauptmarkt-Radar","Primary Market Radar"))','shell(radarTitleFor(radarMarketChoiceMain)+" Radarı")')
# Normalize any remaining static BIST radar page wording in showRadar only.
q=q.replace('"Tüm Borsa İstanbul Radarı"','radarTitleFor(radarMarketChoiceMain)+" Radarı"')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
# verify exact requested area is dynamic
s=p.read_text(encoding='utf-8')
a=s.find('private void showRadar()');b=s.find('\n    private ',a+20);q=s[a:b]
if 'Tüm Borsa İstanbul Radarı' in q: raise SystemExit('static BIST text still present above scan')
if 'radarTitleFor(radarMarketChoiceMain)+" Radarı"' not in q: raise SystemExit('dynamic radar page title missing')
print('v134 radar text above scan follows selected market')
