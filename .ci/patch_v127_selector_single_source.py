from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
a=s.find('private LinearLayout radarMarketSelector(final boolean hourly)')
if a<0: raise SystemExit('selector missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
new='''private LinearLayout radarMarketSelector(final boolean hourly){
        final android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        final int selected=hourly?radarMarketChoiceHourly:radarMarketChoiceMain;
        radarMarketChoice=selected;
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
        String[] labels={"BIST","ALMANYA","ABD","TÜMÜ"};
        for(int i=0;i<labels.length;i++){final int pick=i;Button bt=button(labels[i],selected==i?GREEN:NAVY2);bt.setOnClickListener(v->{
            if(hourly){radarMarketChoiceHourly=pick;sp.edit().putInt("radar_market_hourly",pick).apply();}
            else{radarMarketChoiceMain=pick;sp.edit().putInt("radar_market_main",pick).apply();}
            radarMarketChoice=pick;
            restoreRadarMarketSnapshot(pick);
            radarProgressMarket=pick;
            if(hourly)showHourlyRadar();else showRadar();
        });row.addView(bt,new LinearLayout.LayoutParams(0,-2,1));}
        return row;
    }
'''
s=s[:a]+new+s[b:]
# Main radar render: selected button market drives every label/card/result.
a=s.find('private void showRadar()')
if a<0: raise SystemExit('showRadar missing')
b=s.find('\n    private ',a+20)
if b<0:b=len(s)
q=s[a:b]
brace=q.find('{')+1
q=q[:brace]+'\n        radarMarketChoice=radarMarketChoiceMain;restoreRadarMarketSnapshot(radarMarketChoiceMain);'+q[brace:]
q=q.replace('"Türkiye / BIST • BorsaRadar"','radarMarketTitle()+" • BorsaRadar"')
q=q.replace('"Türkiye / BIST • öncelikli tarama"','radarMarketTitle()+" • öncelikli tarama"')
q=q.replace('"🌐 TR • BIST"','"🌐 "+radarMarketCode()')
q=q.replace('"TR • BIST"','radarMarketCode()')
s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
