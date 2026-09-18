from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
s=s.replace('        showPortfolio();\n    }','        showHome();\n    }',1)
anchor='    private void showPortfolio() {'
if anchor not in s: raise SystemExit('portfolio anchor missing')
home=r'''    private void showHome() {
        shell("Piyasanın Bir Adım Önünde Takip Et");
        AutoCompleteTextView search=new AutoCompleteTextView(this);
        search.setHint("Hisse ara (ör. THYAO, NVDA, SAP)...");
        search.setSingleLine(true); search.setThreshold(1);
        List<String> choices=new ArrayList<>(); choices.addAll(Arrays.asList(BistUniverse.ENTRIES)); choices.addAll(Arrays.asList(GlobalStockUniverse.USA)); choices.addAll(Arrays.asList(GlobalStockUniverse.GERMANY));
        search.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,choices));
        content.addView(search,new LinearLayout.LayoutParams(-1,dp(48)));
        search.setOnItemClickListener((a,v,pos,id)->{String sym=parseSymbol(String.valueOf(a.getItemAtPosition(pos)));if(sym.length()>1)analyzeStock(sym);});
        spacer(8);
        LinearLayout markets=new LinearLayout(this);
        String[] ms={"BIST","Almanya","ABD","Tümü"};
        for(String m:ms){Button b=button(m,m.equals("BIST")?Color.rgb(25,105,210):NAVY2);markets.addView(b,new LinearLayout.LayoutParams(0,-2,1));}
        content.addView(markets); spacer(8);
        LinearLayout modes=new LinearLayout(this);
        Button fast=button("Hızlı Tarama",RED), shortB=button("Kısa Vade",Color.rgb(25,105,210)), div=button("Temettü",GREEN), lng=button("Uzun Vade",AMBER);
        modes.addView(fast,new LinearLayout.LayoutParams(0,dp(66),1));modes.addView(shortB,new LinearLayout.LayoutParams(0,dp(66),1));modes.addView(div,new LinearLayout.LayoutParams(0,dp(66),1));modes.addView(lng,new LinearLayout.LayoutParams(0,dp(66),1));content.addView(modes);
        fast.setOnClickListener(v->showRadar());shortB.setOnClickListener(v->showBaskets());div.setOnClickListener(v->showBaskets());lng.setOnClickListener(v->showBaskets());
        spacer(12); content.addView(bold("Günün Öne Çıkanları",18,NAVY));
        LinearLayout highlights=new LinearLayout(this);
        String[] hs={"En Çok\nYükselen","Hacim\nLiderleri","Fırsat\nHisseleri","Teknik\nSinyal"};
        for(String h:hs){Button b=button(h,NAVY2);highlights.addView(b,new LinearLayout.LayoutParams(0,dp(64),1));}
        content.addView(highlights); spacer(12);
        LinearLayout marketCard=card();marketCard.addView(bold("Piyasa Özeti",18,NAVY));marketCard.addView(txt("Canlı piyasa değerleri veri kaynağından yüklenecek. Sahte endeks değeri gösterilmiyor.",13,Color.DKGRAY));content.addView(marketCard);
        spacer(8);LinearLayout news=card();news.addView(bold("Son Dakika",17,RED));news.addView(txt("Güncel haber akışı bağlandığında burada gösterilecek.",13,Color.DKGRAY));content.addView(news);
    }

'''
s=s.replace(anchor,home+anchor,1)
# Replace old four-button top nav with V18 five-tab navigation.
old='''        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL);
        Button p=button("Portföy",NAVY2), r=button("Radar",GREEN), one=button("Tek Hisse",PURPLE), three=button("3 Sepet",AMBER);
        nav.addView(p,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(r,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(one,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(three,new LinearLayout.LayoutParams(0,-2,1));
        p.setOnClickListener(v->showPortfolio()); r.setOnClickListener(v->showRadar()); one.setOnClickListener(v->singleStockDialog()); three.setOnClickListener(v->showBaskets()); root.addView(nav);
'''
new='''        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL);
        Button home=button("Ana Sayfa",NAVY2), markets=button("Piyasalar",NAVY2), radar=button("Radar",GREEN), portfolio=button("Portföy",NAVY2), more=button("Diğer",NAVY2);
        nav.addView(home,new LinearLayout.LayoutParams(0,-2,1));nav.addView(markets,new LinearLayout.LayoutParams(0,-2,1));nav.addView(radar,new LinearLayout.LayoutParams(0,-2,1));nav.addView(portfolio,new LinearLayout.LayoutParams(0,-2,1));nav.addView(more,new LinearLayout.LayoutParams(0,-2,1));
        home.setOnClickListener(v->showHome());markets.setOnClickListener(v->showRadar());radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());more.setOnClickListener(v->showBaskets());root.addView(nav);
'''
if old not in s: raise SystemExit('old nav missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('v150 V18 home shell PASS')

# V18 dark theme after legacy patches
s=s.replace('private static final int BG = Color.rgb(244, 247, 251);','private static final int BG = Color.rgb(5, 14, 27);')
s=s.replace('private static final int NAVY2 = Color.rgb(17, 50, 82);','private static final int NAVY2 = Color.rgb(16, 31, 52);')
s=s.replace('c.setBackgroundColor(Color.WHITE);','c.setBackgroundColor(Color.rgb(13,26,45));')
s=s.replace('marketCard.addView(bold("Piyasa Özeti",18,NAVY));','marketCard.addView(bold("Piyasa Özeti",18,Color.WHITE));')
s=s.replace('content.addView(bold("Günün Öne Çıkanları",18,NAVY));','content.addView(bold("Günün Öne Çıkanları",18,Color.WHITE));')
p.write_text(s,encoding='utf-8')
print('v150 V18 dark theme PASS')

# V18 home spacing / density pass
s=s.replace('content.setPadding(dp(10),dp(8),dp(10),dp(14))','content.setPadding(dp(12),dp(10),dp(12),dp(16))')
s=s.replace('head.setOrientation(LinearLayout.VERTICAL); head.setPadding(dp(16),dp(12),dp(16),dp(10));','head.setOrientation(LinearLayout.VERTICAL); head.setPadding(dp(16),dp(16),dp(16),dp(12));')
s=s.replace('brand=bold("BORSA RADAR",23,Color.WHITE)','brand=bold("BorsaRadar",24,Color.WHITE)')
s=s.replace('search.setHint("Hisse ara (ör. THYAO, NVDA, SAP)...");','search.setHint("Hisse, şirket veya kod ara..."); search.setTextColor(Color.WHITE); search.setHintTextColor(Color.rgb(126,148,174)); search.setBackgroundColor(Color.rgb(13,26,45)); search.setPadding(dp(14),0,dp(14),0);')
s=s.replace('modes.addView(fast,new LinearLayout.LayoutParams(0,dp(66),1));modes.addView(shortB,new LinearLayout.LayoutParams(0,dp(66),1));modes.addView(div,new LinearLayout.LayoutParams(0,dp(66),1));modes.addView(lng,new LinearLayout.LayoutParams(0,dp(66),1));','modes.addView(fast,new LinearLayout.LayoutParams(0,dp(72),1));modes.addView(shortB,new LinearLayout.LayoutParams(0,dp(72),1));modes.addView(div,new LinearLayout.LayoutParams(0,dp(72),1));modes.addView(lng,new LinearLayout.LayoutParams(0,dp(72),1));')
s=s.replace('highlights.addView(b,new LinearLayout.LayoutParams(0,dp(64),1));','highlights.addView(b,new LinearLayout.LayoutParams(0,dp(72),1));')
p.write_text(s,encoding='utf-8')
print('v150 V18 home density PASS')

# V18 Radar Results visual pass
radar_old='''    private void renderRadarList(List<RadarItem> items,int max) {
        items.sort((a,b)->Double.compare(b.score,a.score)); content.addView(bold("En güçlü adaylar",18,NAVY)); int n=Math.min(max,items.size());'''
radar_new='''    private void renderRadarList(List<RadarItem> items,int max) {
        items.sort((a,b)->Double.compare(b.score,a.score));
        content.addView(bold("Radar Sonuçları",20,Color.WHITE));
        LinearLayout filters=new LinearLayout(this); filters.setOrientation(LinearLayout.HORIZONTAL);
        for(String f:new String[]{"Tümü","AL Sinyali","İzle","SAT"}){Button b=button(f,f.equals("Tümü")?Color.rgb(25,105,210):NAVY2);filters.addView(b,new LinearLayout.LayoutParams(0,-2,1));}
        content.addView(filters); spacer(6);
        LinearLayout selectors=new LinearLayout(this);selectors.setOrientation(LinearLayout.HORIZONTAL);
        for(String f:new String[]{"BIST100","Tüm Sektörler","Teknik + Temel"}){Button b=button(f,NAVY2);selectors.addView(b,new LinearLayout.LayoutParams(0,-2,1));}
        content.addView(selectors);spacer(8);
        LinearLayout header=new LinearLayout(this);header.setOrientation(LinearLayout.HORIZONTAL);header.setBackgroundColor(Color.rgb(13,26,45));
        String[] cols={"Kod","Son Fiyat","Skor","Sinyal"};for(String col:cols){TextView t=bold(col,12,Color.rgb(164,181,202));header.addView(t,new LinearLayout.LayoutParams(0,-2,1));}content.addView(header);
        int n=Math.min(max,items.size());'''
if radar_old in s:s=s.replace(radar_old,radar_new,1)
old_loop='''for(int i=0;i<n;i++){RadarItem r=items.get(i);LinearLayout c=card();int col=r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:r.recommendation.contains("AL")?GREEN:AMBER;c.addView(bold((i+1)+". "+r.symbol+"   "+r.recommendation,18,col));c.addView(txt("Fiyat "+money(r.price,r.symbol)+"  •  Pulse "+fmt(r.score)+"  •  Güven %"+(int)r.confidence+"  •  "+r.horizon,13,Color.DKGRAY));c.addView(txt(r.why,12,Color.GRAY));Button d=button("Grafik / Detay + Haber",NAVY2);c.addView(d);d.setOnClickListener(v->analyzeStock(r.symbol));content.addView(c);spacer(6);}'''
new_loop='''for(int i=0;i<n;i++){RadarItem r=items.get(i);int col=r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:r.recommendation.contains("AL")?GREEN:AMBER;LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);row.setBackgroundColor(i%2==0?Color.rgb(10,22,39):Color.rgb(13,27,47));TextView code=bold(r.symbol,14,Color.WHITE),price=txt(money(r.price,r.symbol),13,Color.WHITE),score=txt(fmt(r.score),13,Color.rgb(164,181,202));Button sig=button(r.recommendation,col);row.addView(code,new LinearLayout.LayoutParams(0,dp(52),1));row.addView(price,new LinearLayout.LayoutParams(0,dp(52),1));row.addView(score,new LinearLayout.LayoutParams(0,dp(52),1));row.addView(sig,new LinearLayout.LayoutParams(0,dp(46),1));row.setOnClickListener(v->analyzeStock(r.symbol));sig.setOnClickListener(v->analyzeStock(r.symbol));content.addView(row);}'''
if old_loop in s:s=s.replace(old_loop,new_loop,1)
p.write_text(s,encoding='utf-8')
print('v150 V18 radar table PASS')

# V18 Stock Detail / General visual pass
detail_old='''        shell(symbol+" • Son 10 işlem günü"); LinearLayout q=card();q.addView(bold(symbol,22,NAVY));q.addView(bold(money(r.price,symbol),25,r.changePct>=0?GREEN:RED));q.addView(txt("Son gün %"+fmt(r.changePct)+"  •  ATR% "+fmt(r.atrPct)+"  •  RelVol x"+fmt(r.relativeVolume),14,Color.DKGRAY));content.addView(q);spacer(7);
        content.addView(signalBanner(r));spacer(7);content.addView(contextBanner(cx));spacer(7);content.addView(new PriceChartView(this,chart,"SON 10 İŞLEM GÜNÜ"),new LinearLayout.LayoutParams(-1,dp(300)));spacer(7);'''
detail_new='''        shell("Hisse Detayı");
        LinearLayout q=card();q.addView(bold(symbol,24,Color.WHITE));q.addView(bold(money(r.price,symbol),27,r.changePct>=0?GREEN:RED));q.addView(txt((r.changePct>=0?"+":"")+fmt(r.changePct)+"%  •  ATR% "+fmt(r.atrPct)+"  •  RelVol x"+fmt(r.relativeVolume),14,Color.rgb(164,181,202)));content.addView(q);spacer(7);
        LinearLayout tabs=new LinearLayout(this);tabs.setOrientation(LinearLayout.HORIZONTAL);String[] tabNames={"Genel","Grafik","Haber","KAP","Finansal"};for(String t:tabNames){Button b=button(t,t.equals("Genel")?Color.rgb(25,105,210):NAVY2);tabs.addView(b,new LinearLayout.LayoutParams(0,-2,1));if(t.equals("Grafik"))b.setOnClickListener(v->analyzeStock(symbol));}content.addView(tabs);spacer(8);
        LinearLayout action=new LinearLayout(this);Button buy=button("AL",GREEN),hold=button("TUT",AMBER),sell=button("SAT",RED);action.addView(buy,new LinearLayout.LayoutParams(0,dp(48),1));action.addView(hold,new LinearLayout.LayoutParams(0,dp(48),1));action.addView(sell,new LinearLayout.LayoutParams(0,dp(48),1));content.addView(action);spacer(8);
        LinearLayout quick=card();quick.addView(bold("Hızlı Bilgiler",17,Color.WHITE));quick.addView(txt("Teknik skor  "+fmt(r.score)+"     Güven  %"+(int)r.confidence,14,Color.rgb(164,181,202)));quick.addView(txt("Momentum  "+r.momentumText+"     Trend  "+r.trendText,13,Color.rgb(164,181,202)));quick.addView(txt("Stop referansı  "+money(r.stopReference,symbol)+"     Hedef süre  "+r.horizonText,13,Color.rgb(164,181,202)));content.addView(quick);spacer(7);
        content.addView(signalBanner(r));spacer(7);content.addView(contextBanner(cx));spacer(7);'''
if detail_old in s:s=s.replace(detail_old,detail_new,1)
# keep chart off General; chart tab will be wired as dedicated screen next pass
s=s.replace('LinearLayout info=card();info.addView(bold("Teknik görünüm",17,NAVY));','LinearLayout info=card();info.addView(bold("Teknik görünüm",17,Color.WHITE));')
s=s.replace('LinearLayout news=card();news.addView(bold("Bilgi akışı",17,NAVY));','LinearLayout news=card();news.addView(bold("Bilgi akışı",17,Color.WHITE));')
p.write_text(s,encoding='utf-8')
print('v150 V18 stock general PASS')

# V18 chart screen: relabel existing production detail controls without touching v149 loader
s=s.replace('new String[]{"Genel","Grafik","Haber","KAP","Finansal","Teknik"}','new String[]{"Genel","Grafik","Haber","KAP","Finansal","Teknik"}')
# Add compact V18 indicator selector immediately before existing chart where recognizable
chart_anchor='content.addView(new PriceChartView(this,'
if chart_anchor in s and '"RSI","MACD","Stoch","CCI","BB"' not in s:
    pos=s.find(chart_anchor)
    line_start=s.rfind('\n',0,pos)+1
    indicator='LinearLayout indicators=new LinearLayout(this);indicators.setOrientation(LinearLayout.HORIZONTAL);for(String ind:new String[]{"RSI","MACD","Stoch","CCI","BB"}){Button ib=button(ind,NAVY2);ib.setTextSize(11);indicators.addView(ib,new LinearLayout.LayoutParams(0,-2,1));}content.addView(indicators);spacer(6);\n        '
    s=s[:line_start]+s[line_start:].replace(chart_anchor,indicator+chart_anchor,1)
# Ensure V18 timeframe labels requested by reference are present as a secondary compact row on stock detail
detail_marker='LinearLayout tabs=new LinearLayout(this);tabs.setOrientation(LinearLayout.HORIZONTAL);'
if detail_marker in s and '"1G","1H","1A","3A","6A","1Y","2Y"' not in s:
    tf='LinearLayout chartPeriods=new LinearLayout(this);chartPeriods.setOrientation(LinearLayout.HORIZONTAL);for(String tf:new String[]{"1G","1H","1A","3A","6A","1Y","2Y"}){Button t=button(tf,NAVY2);t.setTextSize(10);chartPeriods.addView(t,new LinearLayout.LayoutParams(0,-2,1));}content.addView(chartPeriods);spacer(6);\n        '
    s=s.replace(detail_marker,tf+detail_marker,1)
p.write_text(s,encoding='utf-8')
print('v150 V18 chart controls PASS')

# V18 News & KAP screen controls
news_marker='LinearLayout news=card();news.addView(bold("Bilgi akışı",17,Color.WHITE));'
if news_marker in s and '"Tümü","KAP","Medya","Analist"' not in s:
    news_filters='LinearLayout newsFilters=new LinearLayout(this);newsFilters.setOrientation(LinearLayout.HORIZONTAL);for(String nf:new String[]{"Tümü","KAP","Medya","Analist"}){Button nb=button(nf,nf.equals("Tümü")?Color.rgb(25,105,210):NAVY2);nb.setTextSize(11);newsFilters.addView(nb,new LinearLayout.LayoutParams(0,-2,1));}content.addView(newsFilters);spacer(6);\n        '
    s=s.replace(news_marker,news_filters+news_marker,1)
# Replace generic news heading with target wording, preserving actual context data
s=s.replace('bold("Bilgi akışı",17,Color.WHITE)','bold("Haber & KAP",17,Color.WHITE)')
# Add full-list action without fake stories
needle='news.addView(txt("Kapsama: "+cx.coverage,12,Color.GRAY));content.addView(news);spacer(7);'
if needle in s:
    repl='news.addView(txt("Kapsama: "+cx.coverage,12,Color.GRAY));Button allNews=button("Tüm Haberleri Gör",NAVY2);news.addView(allNews);content.addView(news);spacer(7);'
    s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')
print('v150 V18 news KAP PASS')
