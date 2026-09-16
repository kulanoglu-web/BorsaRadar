from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v132: make the persisted MAIN radar selection the single source of truth.
# This runs AFTER v94's chained v95-v130 patches.
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
brace=q.find('{')+1
sync='''\n        final android.content.SharedPreferences radarPrefs=getSharedPreferences(PREFS,Context.MODE_PRIVATE);\n        radarMarketChoiceMain=radarPrefs.getInt("radar_market_main",radarMarketChoiceMain);\n        radarMarketChoice=radarMarketChoiceMain;\n'''
# remove older injected one-liner so state restoration cannot obscure the selected market
q=q.replace('\n        radarMarketChoice=radarMarketChoiceMain;restoreRadarMarketSnapshot(radarMarketChoiceMain);','')
q=q[:brace]+sync+q[brace:]
# force every known main-radar title source to the persisted main selection
q=q.replace('radarMarketTitle()', 'radarTitleFor(radarMarketChoiceMain)')
q=q.replace('radarTitleFor(renderMarket)', 'radarTitleFor(radarMarketChoiceMain)')
q=q.replace('marketName(primaryMarket())', 'radarTitleFor(radarMarketChoiceMain)')
s=s[:a]+q+s[b:]
# Selector: persist synchronously before rebuilding UI; then restore that market's cached result.
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
if a<0: raise SystemExit('selector missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
q=q.replace('sp.edit().putInt("radar_market_main",pick).apply();','sp.edit().putInt("radar_market_main",pick).commit();')
q=q.replace('sp.edit().putInt("radar_market_hourly",pick).apply();','sp.edit().putInt("radar_market_hourly",pick).commit();')
s=s[:a]+q+s[b:]
# shell: radar page always reads persisted MAIN radar market, never portfolio primary market.
a=s.find('private void shell(String page)')
if a<0: raise SystemExit('shell missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
old='if(radarPage){radarMarketChoiceMain=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("radar_market_main",radarMarketChoiceMain);shellMarket=radarMarketChoiceMain;}'
new='if(radarPage){radarMarketChoiceMain=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("radar_market_main",0);radarMarketChoice=radarMarketChoiceMain;shellMarket=radarMarketChoiceMain;}'
if old in q:q=q.replace(old,new,1)
else: raise SystemExit('v130 radarPage shell guard missing')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
# Verification is deliberately behavioral/source-specific, not merely compilation.
s=p.read_text(encoding='utf-8')
def method(name):
    a=s.find(name)
    if a<0: raise SystemExit('MISSING '+name)
    b=s.find('\n    private ',a+len(name))
    return s[a:b if b>=0 else len(s)]
sh=method('private void shell(String page)')
sr=method('private void showRadar()')
sel=method('private LinearLayout radarMarketSelector(final boolean hourly)')
checks={
 'main selection persisted synchronously':'putInt("radar_market_main",pick).commit()' in sel,
 'showRadar reloads persisted main':'getInt("radar_market_main",radarMarketChoiceMain)' in sr,
 'showRadar syncs generic market':'radarMarketChoice=radarMarketChoiceMain' in sr,
 'shell radar uses main':'shellMarket=radarMarketChoiceMain' in sh,
 'shell radar code':'radarCodeFor(displayMarket)' in sh,
 'shell radar title':'radarTitleFor(displayMarket)' in sh,
}
for k,v in checks.items(): print('v132',k,v)
if not all(checks.values()): raise SystemExit('v132 radar market state verification FAILED')
