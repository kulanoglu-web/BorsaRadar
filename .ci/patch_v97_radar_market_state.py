from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Persist the selected Radar/Hourly market independently from the active portfolio profile.
old='private int radarMarketChoice=0; // 0 BIST, 1 Germany, 2 USA, 3 All'
new='private int radarMarketChoice=0; // 0 BIST, 1 Germany, 2 USA, 3 All\n    private int radarMarketChoiceMain=0;\n    private int radarMarketChoiceHourly=0;'
if old in s and 'radarMarketChoiceMain' not in s:s=s.replace(old,new,1)
old='private LinearLayout radarMarketSelector(final boolean hourly){\n        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);\n        String[] labels={"BIST","ALMANYA","ABD","TÜMÜ"};\n        for(int i=0;i<labels.length;i++){final int pick=i;Button b=button(labels[i],radarMarketChoice==i?GREEN:NAVY2);b.setOnClickListener(v->{radarMarketChoice=pick;if(hourly)showHourlyRadar();else showRadar();});row.addView(b,new LinearLayout.LayoutParams(0,-2,1));}\n        return row;\n    }'
new='private LinearLayout radarMarketSelector(final boolean hourly){\n        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);\n        if(hourly)radarMarketChoiceHourly=sp.getInt("radar_market_hourly",radarMarketChoiceHourly);else radarMarketChoiceMain=sp.getInt("radar_market_main",radarMarketChoiceMain);\n        radarMarketChoice=hourly?radarMarketChoiceHourly:radarMarketChoiceMain;\n        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);\n        String[] labels={"BIST","ALMANYA","ABD","TÜMÜ"};\n        for(int i=0;i<labels.length;i++){final int pick=i;Button b=button(labels[i],radarMarketChoice==i?GREEN:NAVY2);b.setOnClickListener(v->{radarMarketChoice=pick;if(hourly){radarMarketChoiceHourly=pick;sp.edit().putInt("radar_market_hourly",pick).apply();showHourlyRadar();}else{radarMarketChoiceMain=pick;sp.edit().putInt("radar_market_main",pick).apply();showRadar();}});row.addView(b,new LinearLayout.LayoutParams(0,-2,1));}\n        return row;\n    }'
if old in s:s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
