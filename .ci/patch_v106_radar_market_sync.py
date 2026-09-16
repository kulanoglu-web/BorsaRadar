from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v106: market selector must change the entire radar screen, not only the top button.
# On selection: persist choice, switch app market context/header, clear only incompatible old results,
# then start a scan for the selected market. Detail navigation keeps the running scan untouched.
old='''b.setOnClickListener(v->{radarMarketChoice=pick;if(hourly){radarMarketChoiceHourly=pick;sp.edit().putInt("radar_market_hourly",pick).apply();showHourlyRadar();}else{radarMarketChoiceMain=pick;sp.edit().putInt("radar_market_main",pick).apply();showRadar();}});'''
new='''b.setOnClickListener(v->{
            int previous=radarMarketChoice; radarMarketChoice=pick;
            if(pick<3)getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("primary_market",pick).apply();
            if(hourly){radarMarketChoiceHourly=pick;sp.edit().putInt("radar_market_hourly",pick).apply();if(previous!=pick){shortScanRunning=false;shortScanDone.set(0);shortScanTotal=0;shortResults.clear();}showHourlyRadar();if(previous!=pick)scanShortTerm(shortScanMode);}
            else{radarMarketChoiceMain=pick;sp.edit().putInt("radar_market_main",pick).apply();if(previous!=pick){radarRunning=false;radarResults.clear();}showRadar();if(previous!=pick)scanRadar();}
        });'''
if old in s:s=s.replace(old,new,1)
else:
    # compact v94 selector fallback, before v97 expansion
    old2='''b.setOnClickListener(v->{radarMarketChoice=pick;if(hourly)showHourlyRadar();else showRadar();});'''
    new2='''b.setOnClickListener(v->{int previous=radarMarketChoice;radarMarketChoice=pick;if(pick<3)getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("primary_market",pick).apply();if(hourly){radarMarketChoiceHourly=pick;getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("radar_market_hourly",pick).apply();if(previous!=pick){shortScanRunning=false;shortScanDone.set(0);shortScanTotal=0;shortResults.clear();}showHourlyRadar();if(previous!=pick)scanShortTerm(shortScanMode);}else{radarMarketChoiceMain=pick;getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("radar_market_main",pick).apply();if(previous!=pick){radarRunning=false;radarResults.clear();}showRadar();if(previous!=pick)scanRadar();}});'''
    if old2 in s:s=s.replace(old2,new2,1)
# Header should follow selected radar market while on radar screens.
# primary_market update above makes shell/header and lower market-specific cards consistent on repaint.
p.write_text(s,encoding='utf-8')
