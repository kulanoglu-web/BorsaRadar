from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# showHourlyRadar is defined before scanShortTerm in the generated source, so locate methods independently.
a=s.find('private void showHourlyRadar()')
if a<0: raise SystemExit('hourly renderer missing')
b=s.find('private void ',a+20)
if b<0: b=len(s)
q=s[a:b]
old='if(!shortRadarResults.isEmpty())renderRadarList(new ArrayList<>(shortRadarResults),20);'
new='''if(!shortRadarResults.isEmpty()){synchronized(shortRadarResults){renderRadarList(new ArrayList<>(shortRadarResults),20);}}else{LinearLayout empty=card();empty.addView(bold(shortScanRunning?"İlk sonuçlar bekleniyor…":"Henüz saatlik sonuç yok",17,Color.LTGRAY));empty.addView(txt(shortScanRunning?"Tarama devam ediyor; uygun aday bulunduğunda burada anında gösterilecek.":"Saatlik Taramayı Yenile düğmesine bas. Sonuçlar tarama tamamlanmadan da listelenecek.",13,Color.GRAY));content.addView(empty);}'''
if old not in q: raise SystemExit('hourly result render anchor missing')
q=q.replace(old,new,1)
q=q.replace('int total=marketSymbols(primaryMarket()).length;','int total=radarUniverse().length;')
s=s[:a]+q+s[b:]
# scanShortTerm may appear later in the class; patch only its own method body.
a=s.find('private void scanShortTerm(String mode)')
if a<0: raise SystemExit('hourly scan missing')
b=s.find('private void ',a+20)
if b<0: b=len(s)
q=s[a:b].replace('marketSymbols(primaryMarket()).length','radarUniverse().length')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
a=s.find('private void showHourlyRadar()');b=s.find('private void ',a+20);hour=s[a:b]
a2=s.find('private void scanShortTerm(String mode)');b2=s.find('private void ',a2+20);scan=s[a2:b2]
checks={'renders list':'renderRadarList(new ArrayList<>(shortRadarResults),20)' in hour,'empty state':'Henüz saatlik sonuç yok' in hour,'progress state':'İlk sonuçlar bekleniyor' in hour,'hourly selected total':'int total=radarUniverse().length;' in hour,'scan exists':a2>=0}
for k,v in checks.items():print('v139',k,v)
if not all(checks.values()):raise SystemExit('v139 verification FAILED')
