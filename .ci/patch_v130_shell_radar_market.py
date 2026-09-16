from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v130: shell() owns the top badge/breadcrumb. On Radar it must use radarMarketChoiceMain,
# not the portfolio primaryMarket(). This is the source missed by v127-v129.
a=s.find('private void shell(String page)')
if a<0: raise SystemExit('shell missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
# Detect Radar page before displayMarket is frozen.
old='int shellMarket=primaryMarket();'
new='''int shellMarket=primaryMarket();
        final boolean radarPage=page!=null && (page.contains("Ana Borsa Radarı") || page.contains("Hauptmarkt-Radar") || page.contains("Primary Market Radar"));
        if(radarPage){radarMarketChoiceMain=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getInt("radar_market_main",radarMarketChoiceMain);shellMarket=radarMarketChoiceMain;}'''
if old not in q: raise SystemExit('shellMarket anchor missing')
q=q.replace(old,new,1)
# For radar screen, use radar-specific code/title instead of portfolio market helpers.
q=q.replace('button("🌐 "+uiLang()+" • "+marketShort(displayMarket),Color.rgb(48,54,62))','button(radarPage?"🌐 "+radarCodeFor(displayMarket):"🌐 "+uiLang()+" • "+marketShort(displayMarket),Color.rgb(48,54,62))')
q=q.replace('txt(marketName(displayMarket)+"  •  BorsaRadar",11,MUTED)','txt((radarPage?radarTitleFor(displayMarket):marketName(displayMarket))+"  •  BorsaRadar",11,MUTED)')
s=s[:a]+q+s[b:]
# showRadar card title: replace the actual bold() expression immediately after shell.
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
# Normalize all known card-title forms after all prior patches.
for old in ['bold("Türkiye / BIST • öncelikli tarama"','bold(radarMarketTitle()+" • öncelikli tarama"','bold(radarTitleFor(renderMarket)+" • öncelikli tarama"']:
    q=q.replace(old,'bold(radarTitleFor(radarMarketChoiceMain)+" • öncelikli tarama"')
# If older title was constructed from primary market, force it too.
q=q.replace('bold(marketName(primaryMarket())+" • öncelikli tarama"','bold(radarTitleFor(radarMarketChoiceMain)+" • öncelikli tarama"')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
