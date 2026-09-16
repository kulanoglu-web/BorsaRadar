from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v106b: synchronize market context without referencing fields that do not exist in every generated radar path.
old='''b.setOnClickListener(v->{radarMarketChoice=pick;if(hourly){radarMarketChoiceHourly=pick;sp.edit().putInt("radar_market_hourly",pick).apply();showHourlyRadar();}else{radarMarketChoiceMain=pick;sp.edit().putInt("radar_market_main",pick).apply();showRadar();}});'''
new='''b.setOnClickListener(v->{
            int previous=radarMarketChoice;radarMarketChoice=pick;
            if(pick<3)getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("primary_market",pick).apply();
            if(hourly){radarMarketChoiceHourly=pick;sp.edit().putInt("radar_market_hourly",pick).apply();showHourlyRadar();if(previous!=pick&&!shortScanRunning)scanShortTerm(shortScanMode);}
            else{radarMarketChoiceMain=pick;sp.edit().putInt("radar_market_main",pick).apply();showRadar();if(previous!=pick)scanRadar();}
        });'''
if old in s:s=s.replace(old,new,1)
else:
    old2='''b.setOnClickListener(v->{radarMarketChoice=pick;if(hourly)showHourlyRadar();else showRadar();});'''
    new2='''b.setOnClickListener(v->{int previous=radarMarketChoice;radarMarketChoice=pick;if(pick<3)getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("primary_market",pick).apply();if(hourly){radarMarketChoiceHourly=pick;getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("radar_market_hourly",pick).apply();showHourlyRadar();if(previous!=pick&&!shortScanRunning)scanShortTerm(shortScanMode);}else{radarMarketChoiceMain=pick;getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("radar_market_main",pick).apply();showRadar();if(previous!=pick)scanRadar();}});'''
    if old2 in s:s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
