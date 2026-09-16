from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v122: one selected market must drive every visible Radar element.
# Screenshot showed ALMANYA selected while header/card stayed BIST and BIST results disappeared.
# Do not let restore/render helpers silently overwrite the visible main-market selection.
a=s.find('private void showRadar()')
if a>=0:
    b=s.find('\n    private ',a+20)
    if b<0:b=len(s)
    block=s[a:b]
    # Main radar preference is authoritative for rendering.
    brace=block.find('{')+1
    guard='\n        radarMarketChoice=radarMarketChoiceMain;'
    if guard.strip() not in block[brace:brace+500]: block=block[:brace]+guard+block[brace:]
    # Hard-coded BIST card/header strings must follow selected market.
    block=block.replace('"Türkiye / BIST • öncelikli tarama"','radarMarketTitle()+" • öncelikli tarama"')
    block=block.replace('"Türkiye / BIST • BorsaRadar"','radarMarketTitle()+" • BorsaRadar"')
    block=block.replace('"🌐 TR • BIST"','"🌐 "+radarMarketCode()')
    # Empty-state belongs to selected market only.
    block=block.replace('"Henüz radar sonucu yok."','"Henüz "+radarMarketTitle()+" radar sonucu yok. Tara düğmesine basarak bu piyasayı tara."')
    s=s[:a]+block+s[b:]
# Selector click: set all main-market state before restoring snapshot and rendering.
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
if a>=0:
    b=s.find('\n    private ',a+20)
    if b<0:b=len(s)
    block=s[a:b]
    block=block.replace('if(hourly)radarMarketChoiceHourly=pick;else radarMarketChoiceMain=pick;\n            radarMarketChoice=pick;', 'if(hourly)radarMarketChoiceHourly=pick;else radarMarketChoiceMain=pick;\n            radarMarketChoice=pick;')
    # Make selected button derive from the actual per-screen state.
    block=block.replace('final int selected=sp.getInt(hourly?"radar_market_hourly":"radar_market_main",hourly?radarMarketChoiceHourly:radarMarketChoiceMain);','final int selected=sp.getInt(hourly?"radar_market_hourly":"radar_market_main",hourly?radarMarketChoiceHourly:radarMarketChoiceMain);')
    s=s[:a]+block+s[b:]
# Scan completion must save results into the market that owned the scan, not whichever market is visible later.
a=s.find('private void scanRadar()')
if a>=0:
    b=s.find('\n    private ',a+20)
    if b<0:b=len(s)
    block=s[a:b]
    # Capture owned market and immutable universe if prior patches did not.
    brace=block.find('{')+1
    if 'final int ownedMarket=' not in block[:900]:
        block=block[:brace]+'\n        radarMarketChoice=radarMarketChoiceMain; final int ownedMarket=radarMarketChoice;'+block[brace:]
    # Any result snapshot write using current mutable market should use scan owner.
    block=block.replace('saveRadarMarketSnapshot(radarMarketChoice);','saveRadarMarketSnapshot(ownedMarket);')
    block=block.replace('radarResultMarket=radarMarketChoice;','radarResultMarket=ownedMarket;')
    s=s[:a]+block+s[b:]
# Snapshot restore: empty selected market must clear stale rows; populated selected market restores its own rows.
a=s.find('private void restoreRadarMarketSnapshot(int market)')
if a>=0:
    b=s.find('\n    private ',a+20)
    if b<0:b=len(s)
    block=s[a:b]
    # Ensure restore cannot leave previous market's rows behind when target has no cache.
    if 'radarResults.clear();' not in block:
        brace=block.find('{')+1
        block=block[:brace]+'\n        radarResults.clear();'+block[brace:]
    s=s[:a]+block+s[b:]
p.write_text(s,encoding='utf-8')
