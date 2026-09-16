from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+30)
if b<0:b=len(s)
q=s[a:b]
brace=q.find('{')+1
# Authoritative market for this render.
pro='''\n        radarMarketChoiceMain=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("radar_market_main",radarMarketChoiceMain);\n        final int rm=radarMarketChoiceMain;radarMarketChoice=rm;restoreRadarMarketSnapshot(rm);'''
q=q[:brace]+pro+q[brace:]
# Do not rely on old helper state: force all literal market labels inside showRadar to rm expressions.
q=q.replace('"🌐 TR • BIST"','"🌐 "+radarCodeFor(rm)')
q=q.replace('"TR • BIST"','radarCodeFor(rm)')
q=q.replace('"Türkiye / BIST • BorsaRadar"','radarTitleFor(rm)+" • BorsaRadar"')
q=q.replace('"Türkiye / BIST • öncelikli tarama"','radarTitleFor(rm)+" • öncelikli tarama"')
q=q.replace('radarMarketTitle()+" • BorsaRadar"','radarTitleFor(rm)+" • BorsaRadar"')
q=q.replace('radarMarketTitle()+" • öncelikli tarama"','radarTitleFor(rm)+" • öncelikli tarama"')
q=q.replace('radarTitleFor(renderMarket)', 'radarTitleFor(rm)')
q=q.replace('radarCodeFor(renderMarket)', 'radarCodeFor(rm)')
# Replace any primary-profile ternary used for the Radar subtitle/card.
q=q.replace('(primaryMarket()==0?"Türkiye / BIST":primaryMarket()==1?"Almanya":"ABD")','radarTitleFor(rm)')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
