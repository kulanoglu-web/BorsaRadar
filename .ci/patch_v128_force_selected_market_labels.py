from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v128: selected main radar market is the only source for all visible labels.
# Do not let shell()/primaryMarket() overwrite Germany/US labels after selector render.
# Add helpers that take an explicit market, avoiding mutable radarMarketChoice ambiguity.
anchor='    private String radarMarketTitle()'
helpers='''    private String radarTitleFor(int m){return m==0?"Türkiye / BIST":m==1?"Almanya / XETRA":m==2?"ABD / NASDAQ-NYSE":"Tüm Piyasalar";}\n    private String radarCodeFor(int m){return m==0?"TR • BIST":m==1?"DE • XETRA":m==2?"US • NASDAQ/NYSE":"GLOBAL";}\n'''
if 'private String radarTitleFor(int m)' not in s:
    if anchor in s:s=s.replace(anchor,helpers+anchor,1)
    else:
        marker='    private void showRadar()'
        s=s.replace(marker,helpers+marker,1)
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+30)
if b<0:b=len(s)
q=s[a:b]
brace=q.find('{')+1
# Load the persisted selector first and pin an immutable render market for this frame.
pro='''\n        radarMarketChoiceMain=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("radar_market_main",radarMarketChoiceMain);\n        final int renderMarket=radarMarketChoiceMain;radarMarketChoice=renderMarket;restoreRadarMarketSnapshot(renderMarket);'''
q=q[:brace]+pro+q[brace:]
# Every visible radar title/code in this method must use renderMarket explicitly.
q=q.replace('radarMarketTitle()', 'radarTitleFor(renderMarket)')
q=q.replace('radarMarketCode()', 'radarCodeFor(renderMarket)')
q=q.replace('"Türkiye / BIST • BorsaRadar"','radarTitleFor(renderMarket)+" • BorsaRadar"')
q=q.replace('"Türkiye / BIST • öncelikli tarama"','radarTitleFor(renderMarket)+" • öncelikli tarama"')
q=q.replace('"🌐 TR • BIST"','"🌐 "+radarCodeFor(renderMarket)')
q=q.replace('"TR • BIST"','radarCodeFor(renderMarket)')
# Common shell/subtitle constructions from primary profile must not leak into Radar.
q=q.replace('(primaryMarket()==0?"Türkiye / BIST":primaryMarket()==1?"Almanya":"ABD")+" • BorsaRadar"','radarTitleFor(renderMarket)+" • BorsaRadar"')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
