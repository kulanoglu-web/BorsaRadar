from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Active exchange profile is also the default market. Existing users are migrated
# into whichever market was selected before profiles were introduced.
pat=r'    private int primaryMarket\(\)\{.*?\n    \}\n'
rep='''    private int primaryMarket(){
        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        if(sp.contains("active_profile")) return sp.getInt("active_profile",0);
        int initial;
        if(sp.contains("primary_market")) initial=sp.getInt("primary_market",0);
        else { String l=uiLang(); initial="TR".equals(l)?0:("DE".equals(l)?1:2); }
        sp.edit().putInt("active_profile",initial).apply();
        return initial;
    }

    private String profileKey(String base){ return base+"_"+primaryMarket(); }

    private void migrateLegacyPortfolioProfiles(){
        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        if(sp.getBoolean("portfolio_profiles_migrated",false)) return;
        JSONArray[] buckets={new JSONArray(),new JSONArray(),new JSONArray()};
        try{
            JSONArray old=new JSONArray(sp.getString("portfolio","[]"));
            for(int i=0;i<old.length();i++){
                JSONObject o=old.getJSONObject(i);
                int market=MarketSymbol.marketIndex(o.optString("s",""));
                if(market<0||market>2) market=0;
                buckets[market].put(o);
            }
        }catch(Exception ignored){}
        sp.edit()
                .putString("portfolio_0",buckets[0].toString())
                .putString("portfolio_1",buckets[1].toString())
                .putString("portfolio_2",buckets[2].toString())
                .putBoolean("portfolio_profiles_migrated",true)
                .apply();
    }

    private String loadProfileJson(String base){
        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        if("portfolio".equals(base)){
            migrateLegacyPortfolioProfiles();
            return sp.getString(profileKey(base),"[]");
        }
        String key=profileKey(base); String raw=sp.getString(key,null);
        if(raw==null){
            String migrated=base+"_profiles_migrated";
            raw=sp.getBoolean(migrated,false)?"[]":sp.getString(base,"[]");
            sp.edit().putString(key,raw).putBoolean(migrated,true).apply();
        }
        return raw;
    }

    private void switchExchangeProfile(int profile){
        if(profile==primaryMarket()){showPortfolio();return;}
        if(scanRunning){Toast.makeText(this,L("Tarama tamamlanınca profil değiştirilebilir.","Profilwechsel nach Abschluss des Scans.","Switch profiles after the scan finishes."),Toast.LENGTH_LONG).show();return;}
        savePortfolio(); saveRadarCache();
        getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("active_profile",profile).putInt("primary_market",profile).apply();
        holdingSignals.clear(); holdingContexts.clear();
        loadPortfolio(); loadRadarCache(); showPortfolio();
    }
'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('primaryMarket profile patch failed')

# One-tap exchange profile switcher below the header.
needle='''        intl.setOnClickListener(v->showInternationalSetup());
        LinearLayout nav=new LinearLayout(this);'''
replacement='''        intl.setOnClickListener(v->showInternationalSetup());
        LinearLayout profiles=new LinearLayout(this); profiles.setOrientation(LinearLayout.HORIZONTAL);
        int active=primaryMarket();
        Button profileTr=button("BIST",active==0?GREEN:NAVY2);
        Button profileDe=button("ALMANYA",active==1?GREEN:NAVY2);
        Button profileUs=button("ABD",active==2?GREEN:NAVY2);
        profiles.addView(profileTr,new LinearLayout.LayoutParams(0,-2,1));
        profiles.addView(profileDe,new LinearLayout.LayoutParams(0,-2,1));
        profiles.addView(profileUs,new LinearLayout.LayoutParams(0,-2,1));
        profileTr.setOnClickListener(v->switchExchangeProfile(0));
        profileDe.setOnClickListener(v->switchExchangeProfile(1));
        profileUs.setOnClickListener(v->switchExchangeProfile(2));
        root.addView(profiles);
        LinearLayout nav=new LinearLayout(this);'''
if needle not in s: raise SystemExit('profile switcher insertion failed')
s=s.replace(needle,replacement,1)

# Setup dialog now switches profiles through the same safe path.
old='''getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("ui_language",lc).putInt("primary_market",market.getSelectedItemPosition()).putBoolean("intl_setup_done",true).apply();
                    radarResults.clear(); showPortfolio();'''
new='''getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("ui_language",lc).putBoolean("intl_setup_done",true).apply();
                    switchExchangeProfile(market.getSelectedItemPosition());'''
if old not in s: raise SystemExit('setup profile save patch failed')
s=s.replace(old,new,1)

# Separate portfolio storage, with one-time migration of the old shared portfolio.
pat=r'    private void savePortfolio\(\)\{.*?\n    private void loadPortfolio\(\)\{.*?\n'
rep='''    private void savePortfolio(){JSONArray a=new JSONArray();try{for(Holding h:holdings){JSONObject o=new JSONObject();o.put("s",h.symbol);o.put("q",h.qty);o.put("c",h.cost);a.put(o);}}catch(Exception ignored){}getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString(profileKey("portfolio"),a.toString()).apply();}
    private void loadPortfolio(){holdings.clear();try{String raw=loadProfileJson("portfolio");JSONArray a=new JSONArray(raw);for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);if(MarketSymbol.marketIndex(o.optString("s",""))==primaryMarket())holdings.add(new Holding(o.getString("s"),o.getInt("q"),o.getDouble("c")));}}catch(Exception ignored){}}
'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('portfolio profile storage patch failed')

# Lock portfolio entry to the active exchange profile so holdings cannot leak across profiles.
needle='''        market.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,markets));
        AutoCompleteTextView sym=new AutoCompleteTextView(this);'''
replacement='''        market.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,markets));
        market.setSelection(primaryMarket());
        market.setEnabled(false);
        AutoCompleteTextView sym=new AutoCompleteTextView(this);'''
if needle not in s: raise SystemExit('portfolio market lock patch failed')
s=s.replace(needle,replacement,1)

# Separate radar cache per exchange profile. Legacy radar is migrated once.
s=s.replace('''putString("radar",a.toString()).apply();}''','''putString(profileKey("radar"),a.toString()).apply();}''',1)
s=s.replace('''getString("radar","[]")''','''getString(profileKey("radar"),loadProfileJson("radar"))''',1)

# Respect the earlier rule: foreign profiles use direct stock analysis, no bulk scan.
needle='''        int pm=primaryMarket(); String[] universe=marketSymbols(pm);
        shell(L("Ana Borsa Radarı","Hauptmarkt-Radar","Primary Market Radar"));'''
replacement='''        int pm=primaryMarket(); String[] universe=marketSymbols(pm);
        if(pm!=0){
            shell(L("Yurtdışı Hisse Profili","Auslandsaktien-Profil","International Stock Profile"));
            LinearLayout direct=card();
            direct.addView(bold(marketName(pm),20,NAVY));
            direct.addView(txt(L("Bu profilde toplu tarama yapılmaz. Hisseyi doğrudan seçerek güncel fiyat, grafik, kâr/zarar ve AL–TUT–SAT değerlendirmesini açabilirsin.","In diesem Profil gibt es keinen Massenscan. Aktien werden direkt für Kurs, Chart, Gewinn/Verlust und KAUFEN–HALTEN–VERKAUFEN ausgewählt.","This profile does not run a bulk scan. Select a stock directly for price, chart, profit/loss and BUY–HOLD–SELL analysis."),14,Color.DKGRAY));
            Button select=button(L("Hisse Seç ve Analiz Et","Aktie wählen und analysieren","Select and analyze stock"),PURPLE);
            select.setOnClickListener(v->singleStockDialog());direct.addView(select);content.addView(direct);return;
        }
        shell(L("Ana Borsa Radarı","Hauptmarkt-Radar","Primary Market Radar"));'''
if needle not in s: raise SystemExit('foreign radar guard patch failed')
s=s.replace(needle,replacement,1)

# Version.
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 48',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.0'",g)
b.write_text(g,encoding='utf-8')
p.write_text(s,encoding='utf-8')
