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
    block=s[start:end].replace('marketSymbols(primaryMarket())','radarUniverse()').replace('String[] universe=marketSymbols(primaryMarket());','String[] universe=radarUniverse()')
    s=s[:start]+block+s[end:]
p.write_text(s,encoding='utf-8')
for name in ['patch_v95_portfolio_persistence.py','patch_v96_portfolio_add_fix.py','patch_v97_radar_market_state.py','patch_v98_chart_trade_levels.py','patch_v99_portfolio_market_routing.py','patch_v100_hourly_scan_speed.py','patch_v101_single_stock_no_freeze.py','patch_v104_radar_detail_state_portfolio.py','patch_v105_portfolio_qty_unified_detail.py','patch_v106_radar_market_sync.py','patch_v107_detail_unlock.py','patch_v108_portfolio_switch.py','patch_v110_portfolio_safe_switch.py','patch_v111_startup_recovery.py','patch_v112_single_stock_portfolio_fix.py','patch_v113_manual_scan_switch.py','patch_v114_market_result_isolation.py','patch_v115_portfolio_selector_restore.py','patch_v116_portfolio_shell_guard.py','patch_v117_market_and_portfolio_state.py','patch_v118_radar_screen_separation.py','patch_v119_radar_scan_lock.py','patch_v120_compile_scope_guard.py','patch_v122_radar_selected_market_render.py','patch_v123_radar_unlock.py','patch_v124_radar_completion_state.py','patch_v125_restore_radar_finish.py','patch_v126_radar_header_selected_market.py','patch_v127_selector_single_source.py','patch_v128_force_selected_market_labels.py','patch_v129_rebuild_radar_header_block.py','patch_v130_shell_radar_market.py','patch_v132_radar_market_state_fix.py','patch_v133_radar_render_context.py','patch_v134_radar_text_above_scan.py','patch_v135_radar_card_selected_market.py','patch_v136_restore_four_market_selector.py','patch_v137_detail_design_step1.py','patch_v138_detail_tabs_functional.py','patch_v139_hourly_results_restore.py','patch_v140_timeframe_no_blank.py','patch_v141_detail_back_previous.py','patch_v142_bist_timeframes.py','patch_v143_bist_intraday_fallback.py','patch_v144_bist_same_as_usa_timeframe_path.py','patch_v146_bist_yahoo_symbol_encoding.py']:
    q=Path('.ci')/name
    if q.exists(): exec(q.read_text(encoding='utf-8'),{'__name__':name})