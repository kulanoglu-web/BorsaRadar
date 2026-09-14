from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Keep radar visible in navigation and make its purpose explicit.
s=s.replace('button("Radar",GREEN)', 'button("Tarama",GREEN)')
s=s.replace('shell("Tüm Borsa İstanbul Radarı")', 'shell("Güncel Fırsat Taraması")')
s=s.replace('top.addView(bold("Tüm hisseler • hafif tarama",19,NAVY));', 'top.addView(bold("Tüm BIST • güncel kısa vade fırsat taraması",19,NAVY));')
s=s.replace('button(scanRunning?"Tarama devam ediyor…":"Tüm BIST\'i Tara",GREEN)', 'button(scanRunning?"Tarama devam ediyor…":"Güncel AL/SAT Fırsatlarını Tara",GREEN)')

# Never erase a completed scan merely because a new scan starts. Keep old results visible until new results are ready.
s=s.replace('if(scanRunning)return; scanRunning=true;scanDone.set(0);scanFailed.set(0);radarResults.clear();showRadar();',
'''if(scanRunning)return; scanRunning=true;scanDone.set(0);scanFailed.set(0);showRadar();
        final List<RadarItem> freshResults=Collections.synchronizedList(new ArrayList<>());''')
s=s.replace('radarResults.add(new RadarItem(sym,r));}catch(Exception e)', 'freshResults.add(new RadarItem(sym,r));}catch(Exception e)')
s=s.replace('List<RadarItem>sorted=new ArrayList<>(radarResults);sorted.sort((a,b)->Double.compare(b.score,a.score));radarResults.clear();radarResults.addAll(sorted);saveRadarCache();',
'''List<RadarItem>sorted=new ArrayList<>(freshResults);sorted.sort((a,b)->Double.compare(b.score,a.score));radarResults.clear();radarResults.addAll(sorted);saveRadarCache();''')

# Add a permanent short-term scan block to the 3-basket page.
marker='private void showBaskets() {'
if marker in s and 'Kısa Vade Güncel Tarama' not in s:
    pos=s.index(marker)
    body=s.index('{',pos)+1
    inject='''\n        // Kısa vade taraması üçlü stratejinin ayrılmaz parçası: son tarama kaybolmaz.\n'''
    s=s[:body]+inject+s[body:]
    # Insert UI immediately after shell call in showBaskets when possible.
    m=re.search(r'(private void showBaskets\(\) \{.*?shell\([^;]+;)',s,re.S)
    if m:
        add='''\n        LinearLayout shortScan=card();\n        shortScan.addView(bold("Kısa Vade Güncel Tarama",19,GREEN));\n        shortScan.addView(txt("Güncel AL/SAT fırsatları için BIST taramasını çalıştırır. Son tamamlanan tarama yeni tarama bitene kadar korunur.",13,Color.DKGRAY));\n        Button shortScanBtn=button(scanRunning?"Tarama devam ediyor…":"Kısa Vade Fırsatlarını Tara",GREEN);\n        shortScanBtn.setEnabled(!scanRunning);\n        shortScanBtn.setOnClickListener(v->scanRadar());\n        shortScan.addView(shortScanBtn); content.addView(shortScan); spacer(8);\n        if(!radarResults.isEmpty()){ content.addView(bold("Son kısa vade fırsatları",17,NAVY)); renderRadarList(new ArrayList<>(radarResults),10); spacer(8); }\n'''
        s=s[:m.end()]+add+s[m.end():]

p.write_text(s,encoding='utf-8')

# Version bump.
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 46',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.10.5'",g)
b.write_text(g,encoding='utf-8')
