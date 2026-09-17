from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Hourly radar must always render the currently available results and make an empty state explicit.
a=s.find('private void showHourlyRadar()')
b=s.find('private void showBaskets()',a)
if a<0 or b<0: raise SystemExit('hourly renderer missing')
q=s[a:b]
old='if(!shortRadarResults.isEmpty())renderRadarList(new ArrayList<>(shortRadarResults),20);'
new='''if(!shortRadarResults.isEmpty()){synchronized(shortRadarResults){renderRadarList(new ArrayList<>(shortRadarResults),20);}}else{LinearLayout empty=card();empty.addView(bold(shortScanRunning?"İlk sonuçlar bekleniyor…":"Henüz saatlik sonuç yok",17,Color.LTGRAY));empty.addView(txt(shortScanRunning?"Tarama devam ediyor; uygun aday bulunduğunda burada anında gösterilecek.":"Saatlik Taramayı Yenile düğmesine bas. Sonuçlar tarama tamamlanmadan da listelenecek.",13,Color.GRAY));content.addView(empty);}'''
if old not in q: raise SystemExit('hourly result render anchor missing')
q=q.replace(old,new,1)
s=s[:a]+q+s[b:]
# Fix stale scan recovery against the selected hourly universe, not primaryMarket().
a=s.find('private void scanShortTerm(String mode)')
b=s.find('private void showHourlyRadar()',a)
if a<0 or b<0: raise SystemExit('hourly scan missing')
q=s[a:b]
q=q.replace('marketSymbols(primaryMarket()).length','radarUniverse().length')
# Keep previous results while a new scan starts; never clear them at scan start.
# Progressive publisher already replaces them only after useful candidates exist.
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void showHourlyRadar()');b=s.find('private void showBaskets()',a);hour=s[a:b]
a2=s.find('private void scanShortTerm(String mode)');b2=s.find('private void showHourlyRadar()',a2);scan=s[a2:b2]
checks={'renders list':'renderRadarList(new ArrayList<>(shortRadarResults),20)' in hour,'empty state':'Henüz saatlik sonuç yok' in hour,'progress state':'İlk sonuçlar bekleniyor' in hour,'selected universe':'radarUniverse().length' in scan,'no primary length':'marketSymbols(primaryMarket()).length' not in scan}
for k,v in checks.items():print('v139',k,v)
if not all(checks.values()):raise SystemExit('v139 verification FAILED')
