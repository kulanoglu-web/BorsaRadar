from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v126: the main Radar selector is authoritative for all visible market labels.
# Fix screenshot state where ABD is selected and US results are shown while header/card still say BIST.
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
block=s[a:b]
brace=block.find('{')+1
guard='\n        radarMarketChoice=radarMarketChoiceMain;'
# Put the authoritative assignment at the start even if an older one exists later.
block=block[:brace]+guard+block[brace:]
# Normalize every known hard-coded/main-radar BIST label.
block=block.replace('"Türkiye / BIST • BorsaRadar"','radarMarketTitle()+" • BorsaRadar"')
block=block.replace('"Türkiye / BIST • öncelikli tarama"','radarMarketTitle()+" • öncelikli tarama"')
block=block.replace('"🌐 TR • BIST"','"🌐 "+radarMarketCode()')
block=block.replace('"TR • BIST"','radarMarketCode()')
# If shell/subtitle was built from primaryMarket(), make Radar follow selected market instead.
block=block.replace('(primaryMarket()==0?"Türkiye / BIST":primaryMarket()==1?"Almanya":"ABD")+" • BorsaRadar"','radarMarketTitle()+" • BorsaRadar"')
s=s[:a]+block+s[b:]
# Ensure selector click updates the authoritative main choice before rendering.
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
if a>=0:
    b=s.find('\n    private ',a+20)
    if b<0:b=len(s)
    q=s[a:b]
    q=q.replace('if(hourly)radarMarketChoiceHourly=pick;else radarMarketChoiceMain=pick;','if(hourly)radarMarketChoiceHourly=pick;else radarMarketChoiceMain=pick;')
    s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
