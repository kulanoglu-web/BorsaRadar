from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v119 stability first: a running radar scan owns one immutable market/universe.
a=s.find('private void scanRadar()')
if a>=0:
    b=s.find('private void enrichRadarTopCandidates',a)
    if b<0:b=s.find('\n    private void ',a+20)
    if b<0:b=len(s)
    block=s[a:b]
    # Replace mutable completion lengths only inside scanRadar.
    block=block.replace('radarUniverse().length','scanUniverse.length')
    # Define scanUniverse at method scope before any worker lambda uses it.
    brace=block.find('{')+1
    if 'final String[] scanUniverse=radarUniverse();' not in block[:min(len(block),700)]:
        block=block[:brace]+'\n        final String[] scanUniverse=radarUniverse();'+block[brace:]
    # v118 may already declare a second scanUniverse later; remove only duplicate declarations.
    first=block.find('final String[] scanUniverse=radarUniverse();')
    second=block.find('String[] scanUniverse=radarUniverse();',first+10)
    if second>=0:
        line_end=block.find('\n',second)
        block=block[:second]+block[line_end+1:]
    # Do not reference scanUniverse outside this method; clear running flag safely.
    block=block.replace('scanRunning=false;','scanRunning=false;if(ownedMarket>=0&&ownedMarket<4)radarRunningByMarket[ownedMarket]=false;',1)
    s=s[:a]+block+s[b:]
# Lock main-market buttons while a scan is active. Hourly selector remains independent.
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
if a>=0:
    b=s.find('\n    private ',a+10)
    if b<0:b=len(s)
    block=s[a:b]
    if 'Button bt=button(labels[i],selected==i?GREEN:NAVY2);' in block and 'bt.setEnabled(hourly||!scanRunning);' not in block:
        block=block.replace('Button bt=button(labels[i],selected==i?GREEN:NAVY2);','Button bt=button(labels[i],selected==i?GREEN:NAVY2);bt.setEnabled(hourly||!scanRunning);',1)
    if 'Button b=button(labels[i],radarMarketChoice==i?GREEN:NAVY2);' in block and 'b.setEnabled(hourly||!scanRunning);' not in block:
        block=block.replace('Button b=button(labels[i],radarMarketChoice==i?GREEN:NAVY2);','Button b=button(labels[i],radarMarketChoice==i?GREEN:NAVY2);b.setEnabled(hourly||!scanRunning);',1)
    s=s[:a]+block+s[b:]
# Reset stale visible running metadata only after the real scan has stopped.
a=s.find('private void showRadar()')
if a>=0:
    brace=s.find('{',a)+1
    guard='\n        if(!scanRunning&&radarProgressMarket>=0&&radarProgressMarket<4)radarRunningByMarket[radarProgressMarket]=false;'
    if guard.strip() not in s[brace:brace+350]:s=s[:brace]+guard+s[brace:]
p.write_text(s,encoding='utf-8')
