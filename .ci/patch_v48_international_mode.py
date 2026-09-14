from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# International helpers and primary-market preference.
anchor='    private int dp(int x) { return Math.round(x * getResources().getDisplayMetrics().density); }'
helpers=r'''
    private String uiLang(){
        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        String x=sp.getString("ui_language",sp.getString("terms_language","EN"));
        return (x==null||x.length()==0)?"EN":x;
    }

    private int primaryMarket(){
        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        if(sp.contains("primary_market")) return sp.getInt("primary_market",2);
        String l=uiLang(); return "TR".equals(l)?0:("DE".equals(l)?1:2);
    }

    private String L(String tr,String de,String en){
        String l=uiLang(); return "TR".equals(l)?tr:("DE".equals(l)?de:en);
    }

    private String marketName(int m){
        if(m==0)return L("Türkiye / BIST","Türkei / BIST","Türkiye / BIST");
        if(m==1)return L("Almanya / Xetra-Frankfurt","Deutschland / Xetra-Frankfurt","Germany / Xetra-Frankfurt");
        return L("ABD / Nasdaq-NYSE","USA / Nasdaq-NYSE","USA / Nasdaq-NYSE");
    }

    private String marketShort(int m){ return m==0?"BIST":m==1?"DE":"USA"; }

    private String[] marketSymbols(int m){
        if(m==0)return ALL_SYMBOLS;
        String[] entries=m==1?GlobalStockUniverse.GERMANY:GlobalStockUniverse.USA;
        String[] out=new String[entries.length];
        for(int i=0;i<entries.length;i++) out[i]=MarketSymbol.manual(GlobalStockUniverse.code(entries[i]),m);
        return out;
    }

    private String[] marketEntries(int m){
        return m==0?BistUniverse.ENTRIES:(m==1?GlobalStockUniverse.GERMANY:GlobalStockUniverse.USA);
    }

    private void showInternationalSetup(){
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(8),dp(18),dp(8));
        box.addView(bold("BorsaRadar • International",21,NAVY));
        box.addView(txt("Language / Sprache / Dil",13,Color.DKGRAY));
        Spinner lang=new Spinner(this);
        String[] langs={"English","Deutsch","Türkçe"};
        lang.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,langs));
        String cur=uiLang(); lang.setSelection("DE".equals(cur)?1:("TR".equals(cur)?2:0)); box.addView(lang);
        box.addView(txt("Primary market / Hauptbörse / Öncelikli borsa",13,Color.DKGRAY));
        Spinner market=new Spinner(this);
        market.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"Türkiye / BIST","Deutschland / Xetra-Frankfurt","USA / Nasdaq-NYSE"}));
        market.setSelection(primaryMarket()); box.addView(market);
        box.addView(txt("The selected market becomes the main radar and default market. The other two markets remain available for individual stock selection and portfolio entries.\n\nDie gewählte Börse wird zum Haupt-Radar und Standardmarkt. Die beiden anderen Märkte bleiben für Einzeltitel und Portfolioeinträge verfügbar.\n\nSeçilen borsa ana radar ve varsayılan piyasa olur. Diğer iki borsa tek hisse seçimi ve portföy girişi için her zaman kullanılabilir.",12,Color.GRAY));
        new AlertDialog.Builder(this).setView(box).setCancelable(false)
                .setPositiveButton("SAVE / SPEICHERN / KAYDET",(d,w)->{
                    String lc=lang.getSelectedItemPosition()==1?"DE":lang.getSelectedItemPosition()==2?"TR":"EN";
                    getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("ui_language",lc).putInt("primary_market",market.getSelectedItemPosition()).putBoolean("intl_setup_done",true).apply();
                    radarResults.clear(); showPortfolio();
                })
                .show();
    }
'''
if 'private void showInternationalSetup()' not in s:
    s=s.replace(anchor,helpers+'\n'+anchor)

# Terms acceptance should continue to market/language setup the first time.
s=s.replace('dlg.dismiss(); showPortfolio(); handleNotificationIntent(getIntent());',
'''dlg.dismiss();
            getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("ui_language",language[0]).apply();
            if(!getSharedPreferences(PREFS,Context.MODE_PRIVATE).getBoolean("intl_setup_done",false)) showInternationalSetup();
            else { showPortfolio(); handleNotificationIntent(getIntent()); }''')

# If terms were already accepted from an earlier build, force the international setup once.
s=s.replace('''        } else {
            showPortfolio();
            handleNotificationIntent(getIntent());
        }''','''        } else {
            if(!getSharedPreferences(PREFS,Context.MODE_PRIVATE).getBoolean("intl_setup_done",false)) showInternationalSetup();
            else { showPortfolio(); handleNotificationIntent(getIntent()); }
        }''')

# Localized shell, plus always-visible language/market switch.
pat=r'    private void shell\(String page\) \{.*?\n    \}\n\n    private void showPortfolio\(\)'
rep=r'''    private void shell(String page) {
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(BG);
        LinearLayout head=new LinearLayout(this); head.setOrientation(LinearLayout.VERTICAL); head.setPadding(dp(16),dp(10),dp(16),dp(8)); head.setBackgroundColor(NAVY);
        LinearLayout titleRow=new LinearLayout(this); titleRow.setOrientation(LinearLayout.HORIZONTAL); titleRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView brand=bold("BORSA RADAR",22,Color.WHITE); brand.setPadding(0,0,0,0); titleRow.addView(brand,new LinearLayout.LayoutParams(0,-2,1));
        Button intl=button("🌐 "+uiLang()+" • "+marketShort(primaryMarket()),NAVY2); titleRow.addView(intl,new LinearLayout.LayoutParams(-2,-2)); head.addView(titleRow);
        TextView sub=txt(page+"  •  "+marketName(primaryMarket()),12,Color.rgb(190,207,224)); sub.setPadding(0,2,0,0); head.addView(sub); root.addView(head);
        intl.setOnClickListener(v->showInternationalSetup());
        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL);
        Button p=button(L("Portföy","Portfolio","Portfolio"),NAVY2), r=button(L("Radar","Radar","Radar"),GREEN), one=button(L("Tek Hisse","Einzeltitel","Single"),PURPLE), three=button(L("3 Sepet","3 Körbe","3 Baskets"),AMBER);
        nav.addView(p,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(r,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(one,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(three,new LinearLayout.LayoutParams(0,-2,1));
        p.setOnClickListener(v->showPortfolio()); r.setOnClickListener(v->showRadar()); one.setOnClickListener(v->singleStockDialog()); three.setOnClickListener(v->showBaskets()); root.addView(nav);
        ScrollView sv=new ScrollView(this); content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(10),dp(8),dp(10),dp(14)); sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));
        TextView foot=txt("© 2026 Erdoğan Kulanoğlu • BorsaRadar • "+L("teknik karar desteği","technische Entscheidungsunterstützung","technical decision support"),11,Color.rgb(100,110,124)); foot.setGravity(Gravity.CENTER); root.addView(foot); setContentView(root);
    }

    private void showPortfolio()'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('shell patch failed')

# Localize key portfolio surface.
s=s.replace('shell("Portföyüm");','shell(L("Portföyüm","Mein Portfolio","My Portfolio"));')
s=s.replace('Button add=button("+ Hisse Ekle",GREEN), refresh=button("Tümünü Güncelle",NAVY2);','Button add=button(L("+ Hisse Ekle","+ Aktie hinzufügen","+ Add stock"),GREEN), refresh=button(L("Tümünü Güncelle","Alle aktualisieren","Refresh all"),NAVY2);')
s=s.replace('bold("Portföy boş",19,NAVY)','bold(L("Portföy boş","Portfolio ist leer","Portfolio is empty"),19,NAVY)')
s=s.replace('txt("Hisse ekleyince maliyet, güncel fiyat, teknik görünüm ve haber/katalizör bağlamı burada görünür.",14,Color.DKGRAY)','txt(L("Hisse ekleyince maliyet, güncel fiyat, teknik görünüm ve haber/katalizör bağlamı burada görünür.","Nach dem Hinzufügen einer Aktie erscheinen Einstand, aktueller Kurs, technisches Signal und Kontext hier.","After adding a stock, cost, current price, technical signal and context appear here."),14,Color.DKGRAY)')

# Primary-market-first portfolio dialog and localized labels.
s=s.replace('String[] markets={"Türkiye / BIST","Almanya / Xetra-Frankfurt","ABD / Nasdaq-NYSE"};','String[] markets={"Türkiye / BIST","Deutschland / Xetra-Frankfurt","USA / Nasdaq-NYSE"};')
s=s.replace('''        if(edit!=null){market.setSelection(MarketSymbol.marketIndex(edit.symbol));sym.setText(edit.symbol,false);qty.setText(String.valueOf(edit.qty));cost.setText(String.valueOf(edit.cost));}
        else if(preset!=null){market.setSelection(MarketSymbol.marketIndex(preset));sym.setText(preset,false);}''','''        if(edit!=null){market.setSelection(MarketSymbol.marketIndex(edit.symbol));sym.setText(edit.symbol,false);qty.setText(String.valueOf(edit.qty));cost.setText(String.valueOf(edit.cost));}
        else if(preset!=null){market.setSelection(MarketSymbol.marketIndex(preset));sym.setText(preset,false);}
        else market.setSelection(primaryMarket());''')
s=s.replace('box.addView(txt("Piyasa",12,Color.DKGRAY));','box.addView(txt(L("Piyasa","Börse","Market"),12,Color.DKGRAY));')

# Primary market defaults in single-stock dialog.
s=s.replace('''        box.addView(market); box.addView(x);''','''        market.setSelection(primaryMarket());
        box.addView(market); box.addView(x);''')
s=s.replace('.setTitle("Tek hisse analiz")','.setTitle(L("Tek hisse analiz","Einzeltitel-Analyse","Single-stock analysis"))')
s=s.replace('.setPositiveButton("Analiz et",','.setPositiveButton(L("Analiz et","Analysieren","Analyze"),')

# Replace BIST-only radar with primary-market radar.
pat=r'    private void showRadar\(\) \{.*?\n    \}\n\n    private void scanRadar\(\) \{.*?\n    \}\n\n    private void renderRadarList'
rep=r'''    private void showRadar() {
        int pm=primaryMarket(); String[] universe=marketSymbols(pm);
        shell(L("Ana Borsa Radarı","Hauptmarkt-Radar","Primary Market Radar"));
        LinearLayout top=card();
        top.addView(bold(marketName(pm)+" • "+L("öncelikli tarama","priorisierte Analyse","priority scan"),19,NAVY));
        String cov=pm==0?L("Borsa İstanbul evreni taranır.","Das Borsa-Istanbul-Universum wird gescannt.","The Borsa Istanbul universe is scanned."):
                L("Likidite ve bilinirliği yüksek yerleşik hisse evreni taranır; diğer iki borsada tek hisse analizi her zaman açıktır.","Ein integriertes Universum liquider, bekannter Aktien wird gescannt; Einzeltitel der beiden anderen Märkte bleiben jederzeit verfügbar.","A built-in universe of liquid, widely followed stocks is scanned; single-stock analysis remains available for the other two markets.");
        top.addView(txt(cov,13,Color.DKGRAY));
        Button scan=button(scanRunning?L("Tarama devam ediyor…","Scan läuft…","Scan running…"):L("Ana Borsayı Tara","Hauptmarkt scannen","Scan primary market"),GREEN);
        top.addView(scan); scan.setEnabled(!scanRunning); scan.setOnClickListener(v->scanRadar()); content.addView(top); spacer(8);
        if(scanRunning){int done=scanDone.get(),failed=scanFailed.get();ProgressBar pb=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);pb.setMax(universe.length);pb.setProgress(Math.min(done,universe.length));content.addView(pb);content.addView(txt(done+"/"+universe.length+" • "+L("başarısız ","Fehler ","failed ")+failed,14,NAVY));}
        if(!radarResults.isEmpty())renderRadarList(new ArrayList<>(radarResults),30);else content.addView(txt(L("Henüz radar sonucu yok.","Noch keine Radar-Ergebnisse.","No radar results yet."),14,Color.GRAY));
    }

    private void scanRadar() {
        if(scanRunning)return;
        final int pm=primaryMarket(); final String[] universe=marketSymbols(pm);
        scanRunning=true;scanDone.set(0);scanFailed.set(0);radarResults.clear();showRadar();
        for(String sym:universe)io.execute(()->{try{List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"1mo");ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);radarResults.add(new RadarItem(sym,r));}catch(Exception e){scanFailed.incrementAndGet();}int done=scanDone.incrementAndGet();if(done>=universe.length){scanRunning=false;List<RadarItem>sorted=new ArrayList<>(radarResults);sorted.sort((a,b)->Double.compare(b.score,a.score));radarResults.clear();radarResults.addAll(sorted);saveRadarCache();main.post(this::showRadar);}else if(done%10==0)main.post(this::showRadar);});
    }

    private void renderRadarList'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('radar patch failed')

s=s.replace('content.addView(bold("En güçlü adaylar",18,NAVY));','content.addView(bold(L("En güçlü adaylar","Stärkste Kandidaten","Strongest candidates"),18,NAVY));')

# bump version
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 46',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.11.0'",g)
b.write_text(g,encoding='utf-8')

# Info version text where present.
s=s.replace('Sürüm 3.10.4 • Teknik karar destek uygulaması','Sürüm 3.11.0 • International • Teknik karar destek uygulaması')

p.write_text(s,encoding='utf-8')
