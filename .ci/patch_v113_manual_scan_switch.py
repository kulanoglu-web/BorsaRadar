from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Market selection changes only the visible market. Scanning remains button-triggered.
s=s.replace('radarMarketChoiceMain=pick;scanRadar();','radarMarketChoiceMain=pick;showRadar();')
s=s.replace('radarMarketChoiceHourly=pick;scanShortTerm(shortScanMode);','radarMarketChoiceHourly=pick;showHourlyRadar();')
s=s.replace('radarMarketChoice=pick;scanRadar();','radarMarketChoice=pick;showRadar();')
s=s.replace('radarMarketChoice=pick;scanShortTerm(shortScanMode);','radarMarketChoice=pick;showHourlyRadar();')
p.write_text(s,encoding='utf-8')
