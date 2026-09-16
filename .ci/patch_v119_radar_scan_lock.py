from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v119 stability first: a running radar scan owns an immutable market/universe.
# Do not allow market switching until that scan finishes; this prevents old worker
# callbacks from writing into a newly selected market and prevents premature restart.
a=s.find('private void scanRadar()')
if a>=0:
    b=s.find('private void enrichRadarTopCandidates',a)
    if b<0:b=s.find('\n    private void ',a+20)
    if b<0:b=len(s)
    block=s[a:b]
    # Critical race fix: completion must use the universe captured when scan started,
    # never radarUniverse(), which changes when the user changes market.
    block=block.replace('radarUniverse().length','scanUniverse.length')
    # Ensure scan universe is captured once.
    if 'String[] scanUniverse=radarUniverse();' not in block:
        brace=block.find('{')+1
        block=block[:brace]+'\n        final String[] scanUniverse=radarUniverse();'+block[brace:]
    # Clear per-market running flag when immutable universe completes if completion exists.
    block=block.replace('scanRunning=false;','scanRunning=false;radarRunningByMarket[ownedMarket]=false;',1)
    s=s[:a]+block+s[b:]
# While the main Radar scan is running, keep market buttons visible but locked.
# User can switch immediately again as soon as the scan has really completed.
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
if a>=0:
    b=s.find('\n    private ',a+10)
    if b<0:b=len(s)
    block=s[a:b]
    needle='Button bt=button(labels[i],selected==i?GREEN:NAVY2);'
    if needle in block and 'bt.setEnabled(hourly||!scanRunning);' not in block:
        block=block.replace(needle,needle+'bt.setEnabled(hourly||!scanRunning);',1)
    # Older generated selector may use b instead of bt.
    needle2='Button b=button(labels[i],radarMarketChoice==i?GREEN:NAVY2);'
    if needle2 in block and 'b.setEnabled(hourly||!scanRunning);' not in block:
        block=block.replace(needle2,needle2+'b.setEnabled(hourly||!scanRunning);',1)
    s=s[:a]+block+s[b:]
# Never let a stale per-market flag survive after the global scan is finished.
a=s.find('private void showRadar()')
if a>=0:
    brace=s.find('{',a)+1
    guard='\n        if(!scanRunning&&radarProgressMarket>=0&&radarProgressMarket<4)radarRunningByMarket[radarProgressMarket]=false;'
    if guard.strip() not in s[brace:brace+350]:s=s[:brace]+guard+s[brace:]
p.write_text(s,encoding='utf-8')
