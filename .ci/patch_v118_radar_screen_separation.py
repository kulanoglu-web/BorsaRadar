from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v118: make BIST/DE/US/ALL visually and functionally separate on the Radar screen.
# The screenshot showed ALMANYA selected while header/card/progress still belonged to BIST.
# Use selected Radar market for every visible label and hide stale progress from another market.
# Market-specific scan metadata.
field='private int radarResultMarket=-1;'
if field in s and 'radarProgressMarket' not in s:
    s=s.replace(field,field+'\n    private int radarProgressMarket=-1;\n    private final int[] radarDoneByMarket=new int[]{0,0,0,0};\n    private final int[] radarFailByMarket=new int[]{0,0,0,0};\n    private final boolean[] radarRunningByMarket=new boolean[]{false,false,false,false};',1)
# Dynamic human-readable market labels.
marker='    private String radarMarketLabel()'
helper='''    private String radarMarketTitle(){return radarMarketChoice==0?"Türkiye / BIST":radarMarketChoice==1?"Almanya":radarMarketChoice==2?"ABD":"Tüm Piyasalar";}\n    private String radarMarketCode(){return radarMarketChoice==0?"TR • BIST":radarMarketChoice==1?"DE • XETRA":radarMarketChoice==2?"US • NASDAQ/NYSE":"GLOBAL";}\n'''
if marker in s and 'private String radarMarketTitle()' not in s:s=s.replace(marker,helper+marker,1)
# Replace hard-coded BIST text in radar UI after all older patches.
s=s.replace('"Türkiye / BIST • öncelikli tarama"','radarMarketTitle()+" • öncelikli tarama"')
s=s.replace('"Türkiye / BIST • BorsaRadar"','radarMarketTitle()+" • BorsaRadar"')
# Some patched source may contain concatenated dynamic expression from v114; normalize it.
s=s.replace('"+radarMarketLabel()+" • öncelikli tarama', '"+radarMarketTitle()+" • öncelikli tarama')
# On market selection: clear stale global progress counters visually by restoring only selected snapshot.
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
if a>=0:
    b=s.find('\n    private ',a+10)
    if b<0:b=len(s)
    block=s[a:b]
    block=block.replace('restoreRadarMarketSnapshot(pick);','restoreRadarMarketSnapshot(pick);radarProgressMarket=pick;')
    s=s[:a]+block+s[b:]
# Capture scan ownership and initialize market-specific progress.
a=s.find('private void scanRadar()')
if a>=0:
    brace=s.find('{',a)+1
    ins='''\n        radarMarketChoice=radarMarketChoiceMain; final int ownedMarket=radarMarketChoice;radarProgressMarket=ownedMarket;radarDoneByMarket[ownedMarket]=0;radarFailByMarket[ownedMarket]=0;radarRunningByMarket[ownedMarket]=true;'''
    # replace v117 scanMarket line if present, otherwise insert
    segment=s[brace:brace+450]
    if 'final int scanMarket=' in segment:
        old='radarMarketChoice=radarMarketChoiceMain; final int scanMarket=radarMarketChoice;'
        s=s.replace(old,ins.strip(),1)
    elif 'final int ownedMarket=' not in segment:s=s[:brace]+ins+s[brace:]
# Empty result text must identify selected market instead of looking like a BIST scan.
s=s.replace('"Henüz radar sonucu yok."','"Henüz "+radarMarketTitle()+" radar sonucu yok. Tara düğmesine basarak bu piyasayı tara."')
# Top header market badge: if exact hard-coded TR/BIST text exists in radar rendering, make it selected-market aware.
s=s.replace('"🌐 TR • BIST"','"🌐 "+radarMarketCode()')
p.write_text(s,encoding='utf-8')
