from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Keep radar visible in navigation and make its purpose explicit.
s=s.replace('button("Radar",GREEN)', 'button("Tarama",GREEN)')
s=s.replace('shell("Tüm Borsa İstanbul Radarı")', 'shell("Güncel Fırsat Taraması")')
s=s.replace('button(scanRunning?"Tarama devam ediyor…":"Tüm BIST\'i Tara",GREEN)', 'button(scanRunning?"Tarama devam ediyor…":"Güncel AL/SAT Fırsatlarını Tara",GREEN)')

# Preserve the last completed scan while the replacement scan runs.
start='if(scanRunning)return; scanRunning=true;scanDone.set(0);scanFailed.set(0);radarResults.clear();showRadar();'
replacement='''if(scanRunning)return; scanRunning=true;scanDone.set(0);scanFailed.set(0);showRadar();
        final List<RadarItem> freshResults=Collections.synchronizedList(new ArrayList<>());'''
if start not in s:
    raise SystemExit('persistent radar start patch failed')
s=s.replace(start,replacement,1)

# v52 has already converted the scanner to RadarTechnicalEngine at this stage.
add='''                radarResults.add(item);'''
if add not in s:
    raise SystemExit('persistent radar buffer patch failed')
s=s.replace(add,'''                freshResults.add(item);''',1)

finish='''                List<RadarItem>sorted=new ArrayList<>(radarResults);
                sorted.sort((a,b)->Double.compare(b.score,a.score));
                radarResults.clear();radarResults.addAll(sorted);'''
if finish not in s:
    raise SystemExit('persistent radar completion patch failed')
s=s.replace(finish,'''                List<RadarItem>sorted=new ArrayList<>(freshResults);
                sorted.sort((a,b)->Double.compare(b.score,a.score));
                radarResults.clear();radarResults.addAll(sorted);''',1)

# Add a permanent short-term scan block to the three-basket page.
marker='private void showBaskets() {'
if marker not in s:
    raise SystemExit('three basket method missing')
m=re.search(r'(private void showBaskets\(\) \{.*?shell\([^;]+;)',s,re.S)
if not m:
    raise SystemExit('three basket insertion point missing')
ui='''
        LinearLayout shortTermScanCard=card();
        shortTermScanCard.addView(bold("Kısa Vade Güncel AL/SAT Taraması",19,GREEN));
        shortTermScanCard.addView(txt("BIST hisselerini güncel teknik veriyle tarar. Son tamamlanan sonuçlar yeni tarama bitene kadar ekranda ve üçlü stratejide korunur.",13,Color.DKGRAY));
        Button shortTermScanButton=button(scanRunning?"Tarama devam ediyor…":"Kısa Vade Fırsatlarını Tara",GREEN);
        shortTermScanButton.setEnabled(!scanRunning);
        shortTermScanButton.setOnClickListener(v->scanRadar());
        shortTermScanCard.addView(shortTermScanButton); content.addView(shortTermScanCard); spacer(8);
        if(!radarResults.isEmpty()){ content.addView(bold("Güncel 1–3 günlük fırsatlar",17,NAVY)); renderRadarList(new ArrayList<>(radarResults),10); spacer(8); }
'''
s=s[:m.end()]+ui+s[m.end():]
p.write_text(s,encoding='utf-8')

# Stable signed update version.
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 47',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.11.1'",g)
b.write_text(g,encoding='utf-8')
