from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
s=s.replace('Button r=button("↗\\n"+L("Radar","Radar","Radar"),ACCENT);','Button r=button("↗\\n"+L("Radar","Radar","Radar"),ACCENT);\n        Button hour=button("◷\\n"+L("Saatlik","Stündlich","Hourly"),GREEN);',1)
s=s.replace('for(Button b:new Button[]{p,r,one,three})','for(Button b:new Button[]{p,r,hour,one,three})',1)
s=s.replace('nav.addView(r,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(one','nav.addView(r,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(hour,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(one',1)
s=s.replace('r.setOnClickListener(v->showRadar()); one.setOnClickListener','r.setOnClickListener(v->showRadar()); hour.setOnClickListener(v->showHourlyRadar()); one.setOnClickListener',1)
anchor=s.find('private void showBaskets()')
if anchor<0: raise SystemExit('basket anchor missing')
method='''private void showHourlyRadar() {\n        shell("Saatlik Radar • Kalıcı");\n        LinearLayout c=card();c.addView(bold("SAATLİK FIRSAT / RİSK",20,GREEN));c.addView(txt("Ana radardan ayrıdır. Son sonuç yeni tarama bitene kadar kalır.",13,Color.DKGRAY));\n        Button b=button(shortScanRunning?"Taranıyor…":"Saatlik Taramayı Yenile",GREEN);b.setEnabled(!shortScanRunning);b.setOnClickListener(v->scanShortTerm("1S"));c.addView(b);content.addView(c);spacer(8);\n        if(!shortRadarResults.isEmpty())renderRadarList(new ArrayList<>(shortRadarResults),20);\n    }\n\n    '''
s=s[:anchor]+method+s[anchor:]
p.write_text(s,encoding='utf-8')
