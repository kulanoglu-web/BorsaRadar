from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
field='    private String shortScanMode="1S";'
if 'private int radarMarketChoice=' not in s:s=s.replace(field,field+'\n    private int radarMarketChoice=0; // 0 BIST, 1 Germany, 2 USA, 3 All',1)
marker='    private void showPortfolio()'
helpers=r'''    private String radarMarketLabel(){return radarMarketChoice==0?"BIST":radarMarketChoice==1?"ALMANYA":radarMarketChoice==2?"ABD":"TÜMÜ";}
    private String[] radarUniverse(){if(radarMarketChoice<3)return marketSymbols(radarMarketChoice);java.util.LinkedHashSet<String> u=new java.util.LinkedHashSet<>();for(int m=0;m<3;m++)for(String x:marketSymbols(m))u.add(x);return u.toArray(new String[0]);}
    private LinearLayout radarMarketSelector(final boolean hourly){LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);String[] labels={"BIST","ALMANYA","ABD","TÜMÜ"};for(int i=0;i<labels.length;i++){final int pick=i;Button b=button(labels[i],radarMarketChoice==i?GREEN:NAVY2);b.setOnClickListener(v->{radarMarketChoice=pick;if(hourly)showHourlyRadar();else showRadar();});row.addView(b,new LinearLayout.LayoutParams(0,-2,1));}return row;}

'''
if 'private String[] radarUniverse()' not in s:
    if marker not in s: raise SystemExit('helper anchor missing')
    s=s.replace(marker,helpers+marker,1)
start=s.find('private void scanRadar()');end=s.find('private void enrichRadarTopCandidates',start)
if start<0 or end<0: raise SystemExit('scanRadar missing')
block=s[start:end].replace('for(String sym:ALL_SYMBOLS)','String[] scanUniverse=radarUniverse();\n        for(String sym:scanUniverse)',1).replace('if(done>=ALL_SYMBOLS.length)','if(done>=radarUniverse().length)')
s=s[:start]+block+s[end:]
old='''        if(pm!=0){
            shell(L("Yurtdışı Hisse Profili","Auslandsaktien-Profil","International Stock Profile"));'''
pos=s.find(old)
if pos>=0:
    ret=s.find('        shell(L("Ana Borsa Radarı"',pos)
    if ret>pos:s=s[:pos]+s[ret:]
needle='''shell(L("Ana Borsa Radarı","Hauptmarkt-Radar","Primary Market Radar"));'''
if needle in s and 'radarMarketSelector(false)' not in s:s=s.replace(needle,needle+'\n        content.addView(radarMarketSelector(false));spacer(8);',1)
needle='''shell("Saatlik Radar • Kalıcı");'''
if needle in s and 'radarMarketSelector(true)' not in s:s=s.replace(needle,needle+'\n        content.addView(radarMarketSelector(true));spacer(8);',1)
start=s.find('private void scanShortTerm(String mode)');end=s.find('private void showHourlyRadar()',start)
if start>=0:
    if end<0:end=s.find('private void showBaskets()',start)
    block=s[start:end].replace('marketSymbols(primaryMarket())','radarUniverse()').replace('String[] universe=marketSymbols(primaryMarket());','String[] universe=radarUniverse();')
    s=s[:start]+block+s[end:]
p.write_text(s,encoding='utf-8')
for name in ['patch_v95_portfolio_persistence.py','patch_v96_portfolio_add_fix.py','patch_v97_radar_market_state.py','patch_v98_chart_trade_levels.py','patch_v99_portfolio_market_routing.py','patch_v100_hourly_scan_speed.py','patch_v101_single_stock_no_freeze.py','patch_v104_radar_detail_state_portfolio.py','patch_v105_portfolio_qty_unified_detail.py','patch_v106_radar_market_sync.py','patch_v107_detail_unlock.py','patch_v108_portfolio_switch.py','patch_v110_portfolio_safe_switch.py','patch_v111_startup_recovery.py','patch_v112_single_stock_portfolio_fix.py','patch_v113_manual_scan_switch.py','patch_v114_market_result_isolation.py','patch_v115_portfolio_selector_restore.py','patch_v116_portfolio_shell_guard.py']:
    q=Path('.ci')/name
    if q.exists(): exec(q.read_text(encoding='utf-8'),{'__name__':name})
