from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v133: do not infer Radar context from localized/dynamic page text.
# showRadar explicitly marks the next shell render as Radar, then shell consumes/reset the flag.
field='    private String shortScanMode="1S";'
if 'private boolean radarShellMode=' not in s:
    if field not in s: raise SystemExit('field anchor missing')
    s=s.replace(field,field+'\n    private boolean radarShellMode=false;',1)

def block(sig):
    global s
    a=s.find(sig)
    if a<0: raise SystemExit('missing '+sig)
    b=s.find('\n    private ',a+len(sig))
    if b<0:b=len(s)
    return a,b,s[a:b]

# Mark every main Radar render before shell() is called.
a,b,q=block('private void showRadar()')
brace=q.find('{')+1
q=q[:brace]+'\n        radarShellMode=true;'+q[brace:]
s=s[:a]+q+s[b:]

# shell consumes explicit context. This survives translated/dynamic page titles.
a,b,q=block('private void shell(String page)')
old='final boolean radarPage=page!=null && (page.contains("Ana Borsa Radarı") || page.contains("Hauptmarkt-Radar") || page.contains("Primary Market Radar"));'
new='final boolean radarPage=radarShellMode || (page!=null && (page.contains("Ana Borsa Radarı") || page.contains("Hauptmarkt-Radar") || page.contains("Primary Market Radar"))); radarShellMode=false;'
if old not in q: raise SystemExit('radarPage detector missing')
q=q.replace(old,new,1)
# Radar must always read persisted selector value; never portfolio primary market.
old2='if(radarPage){radarMarketChoiceMain=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("radar_market_main",0);radarMarketChoice=radarMarketChoiceMain;shellMarket=radarMarketChoiceMain;}'
if old2 not in q: raise SystemExit('v132 shell state missing')
s=s[:a]+q+s[b:]

p.write_text(s,encoding='utf-8')
# Strict verification
s=p.read_text(encoding='utf-8')
a=s.find('private void showRadar()'); b=s.find('\n    private ',a+20); sr=s[a:b]
a=s.find('private void shell(String page)'); b=s.find('\n    private ',a+20); sh=s[a:b]
checks={
 'showRadar marks radar context':'radarShellMode=true;' in sr,
 'shell consumes explicit radar context':'radarPage=radarShellMode ||' in sh,
 'shell resets context':'radarShellMode=false;' in sh,
 'shell reads persisted main':'getInt("radar_market_main",0)' in sh,
 'shell uses radar main':'shellMarket=radarMarketChoiceMain' in sh,
}
for k,v in checks.items(): print('v133',k,v)
if not all(checks.values()): raise SystemExit('v133 verification FAILED')
