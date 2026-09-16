from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v104: Radar -> detail must not stop/reset scan; return should restore last radar view.
# Persist navigation origin so Back/refresh can return to the same radar mode.
field='    private String shortScanMode="1S";'
if field in s and 'private String detailReturnScreen=' not in s:
    s=s.replace(field,field+'\n    private String detailReturnScreen="";\n    private int radarLastScrollY=0;',1)
# Give the fast detail the same real/fake portfolio controls immediately; BIST and foreign symbols use one dialog.
needle='''        if(st!=null){String cur=MarketSymbol.marketIndex(symbol)==0?"TL":"€";LinearLayout t=card();t.addView(bold("Kısa Vade Hedef Planı",17,Color.WHITE));t.addView(txt(st.summary(cur),13,Color.DKGRAY));content.addView(t);spacer(7);}'''
if needle in s and 'Hızlı Portföy İşlemleri' not in s:
    add=needle+'''\n        LinearLayout quickPf=card(); quickPf.addView(bold("Hızlı Portföy İşlemleri",17,Color.WHITE));\n        LinearLayout quickBtns=new LinearLayout(this);quickBtns.setOrientation(LinearLayout.HORIZONTAL);\n        Button quickReal=button("Gerçek Portföye Ekle",GREEN),quickFake=button("Fake Portföye Ekle",Color.rgb(35,105,180));\n        quickBtns.addView(quickReal,new LinearLayout.LayoutParams(0,-2,1));quickBtns.addView(quickFake,new LinearLayout.LayoutParams(0,-2,1));quickPf.addView(quickBtns);\n        quickReal.setOnClickListener(v->portfolioDialog(null,symbol)); quickFake.setOnClickListener(v->addPaperPosition(symbol,last.close,1));\n        content.addView(quickPf);spacer(7);'''
    s=s.replace(needle,add,1)
# When any radar result opens a stock, remember which radar should be restored. Do not touch scan flags/results.
# Cover common click targets used by main/hourly result cards.
s=s.replace('v->showStockDetail(r.symbol)', 'v->{detailReturnScreen="radar";showStockDetail(r.symbol);}')
s=s.replace('v->showStockDetail(x.symbol)', 'v->{detailReturnScreen="radar";showStockDetail(x.symbol);}')
s=s.replace('v->showStockDetail(sym)', 'v->{detailReturnScreen="radar";showStockDetail(sym);}')
s=s.replace('v->openStockDetail(r.symbol)', 'v->{detailReturnScreen="radar";openStockDetail(r.symbol);}')
s=s.replace('v->openStockDetail(x.symbol)', 'v->{detailReturnScreen="radar";openStockDetail(x.symbol);}')
# Never force a new radar scan merely because screen was rebuilt while an existing scan/results exist.
# Existing scan continues on executor and showRadar can repaint progressive results.
s=s.replace('if(!radarRunning && radarResults.isEmpty())scanRadar();','if(!radarRunning && radarResults.isEmpty())scanRadar();')
# Portfolio dialog market selector: preset symbol must resolve to its own market; keep selector locked to avoid BIST->USA mismatch.
old='market.setSelection(preset!=null?MarketSymbol.marketIndex(preset.trim().toUpperCase(java.util.Locale.ROOT)):primaryMarket());\n        market.setEnabled(edit==null&&preset==null);'
new='int presetMarket=preset!=null?MarketSymbol.marketIndex(preset.trim().toUpperCase(java.util.Locale.ROOT)):primaryMarket(); if(presetMarket<0||presetMarket>2)presetMarket=primaryMarket(); market.setSelection(presetMarket);\n        market.setEnabled(edit==null&&preset==null);'
if old in s:s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
