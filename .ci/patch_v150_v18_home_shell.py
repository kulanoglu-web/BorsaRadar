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

# V18 Financial Data screen shell; placeholders only where no verified feed is available
financial_marker='Button add=button("Portföye Ekle",GREEN);content.addView(add);'
if financial_marker in s and '"Özet","Gelir Tablosu","Bilanço","Nakit Akışı"' not in s:
    financial='''LinearLayout financial=card();financial.addView(bold("Finansal Veriler",18,Color.WHITE));LinearLayout finTabs=new LinearLayout(this);finTabs.setOrientation(LinearLayout.HORIZONTAL);for(String ft:new String[]{"Özet","Gelir Tablosu","Bilanço","Nakit Akışı"}){Button fb=button(ft,ft.equals("Özet")?Color.rgb(25,105,210):NAVY2);fb.setTextSize(10);finTabs.addView(fb,new LinearLayout.LayoutParams(0,-2,1));}financial.addView(finTabs);financial.addView(txt("F/K                 —",13,Color.rgb(164,181,202)));financial.addView(txt("PD/DD               —",13,Color.rgb(164,181,202)));financial.addView(txt("FD/FAVÖK            —",13,Color.rgb(164,181,202)));financial.addView(txt("Hisse Başına Kâr    —",13,Color.rgb(164,181,202)));financial.addView(txt("Temettü Verimi      —",13,Color.rgb(164,181,202)));financial.addView(txt("Özsermaye Kârlılığı —",13,Color.rgb(164,181,202)));financial.addView(txt("Net Kâr             —",13,Color.rgb(164,181,202)));financial.addView(txt("Ciro                —",13,Color.rgb(164,181,202)));financial.addView(txt("Doğrulanmış finansal veri kaynağı bağlandığında değerler otomatik gösterilecek.",11,Color.GRAY));content.addView(financial);spacer(8);
        '''
    s=s.replace(financial_marker,financial+financial_marker,1)
p.write_text(s,encoding='utf-8')
print('v150 V18 financial screen PASS')

# V18 UI 7-11 and navigation pass
# 7 Technical Analysis
tech_anchor='LinearLayout financial=card();'
if tech_anchor in s and 'Genel Teknik Görünüm' not in s:
    tech='''LinearLayout technical=card();technical.addView(bold("Teknik Analiz",18,Color.WHITE));String[] techRows={"RSI","MACD","Stochastic","CCI","EMA20 / EMA50 / EMA200","Bollinger","ATR","SuperTrend","Fibonacci"};for(String tr:techRows)technical.addView(txt(tr+"                         —",13,Color.rgb(164,181,202)));technical.addView(bold("Genel Teknik Görünüm",15,Color.WHITE));technical.addView(txt("Kısa Vade  •  Orta Vade  •  Uzun Vade",12,Color.rgb(164,181,202)));content.addView(technical);spacer(8);
        '''
    s=s.replace(tech_anchor,tech+tech_anchor,1)
# 8 Target & Risk
if tech_anchor in s and 'Hedef Fiyat & Risk' not in s:
    risk='''LinearLayout risk=card();risk.addView(bold("Hedef Fiyat & Risk",18,Color.WHITE));for(String rr:new String[]{"Kısa Vade Hedef","Orta Vade Hedef","Uzun Vade Hedef","Destek","Direnç","Stop Loss","Getiri / Risk"})risk.addView(txt(rr+"                         —",13,Color.rgb(164,181,202)));content.addView(risk);spacer(8);
        '''
    s=s.replace(tech_anchor,risk+tech_anchor,1)
# 9 Portfolio heading / analysis action
s=s.replace('shell("Portföyüm");','shell("Portföy");',1)
s=s.replace('Button add=button("+ Hisse Ekle",GREEN), refresh=button("Tümünü Güncelle",NAVY2);','Button add=button("+ Hisse Ekle",GREEN), refresh=button("Portföy Analiz",NAVY2);',1)
# 10 Strategy screen method
portfolio_anchor='    private void showPortfolio() {'
if portfolio_anchor in s and 'private void showStrategySelection()' not in s:
    method='''    private void showStrategySelection() {
        shell("Strateji Seçimi");
        for(String st:new String[]{"Kısa Vade","Temettü","Uzun Vade"}){Button b=button(st,NAVY2);b.setTextSize(17);content.addView(b,new LinearLayout.LayoutParams(-1,dp(64)));spacer(6);}
        LinearLayout criteria=card();criteria.addView(bold("Tarama Kriterleri",18,Color.WHITE));for(String c:new String[]{"☑ Teknik Analiz","☑ Temel Analiz","☑ Haber Taraması","☑ Sektör Analizi","☑ Büyük Alıcı / Satıcı","☑ Finansal Güç","☑ Temettü Potansiyeli"})criteria.addView(txt(c,14,Color.rgb(210,220,232)));content.addView(criteria);spacer(8);Button start=button("Taramayı Başlat",GREEN);content.addView(start,new LinearLayout.LayoutParams(-1,dp(54)));start.setOnClickListener(v->showRadar());
    }

'''
    s=s.replace(portfolio_anchor,method+portfolio_anchor,1)
# 11 More screen
if portfolio_anchor in s and 'private void showMore()' not in s:
    more='''    private void showMore() {
        shell("Diğer");
        LinearLayout profile=card();profile.addView(bold("BorsaRadar",19,Color.WHITE));profile.addView(txt("Piyasa araçları ve uygulama seçenekleri",13,Color.rgb(164,181,202)));content.addView(profile);spacer(8);
        for(String m:new String[]{"Piyasa Takvimi","Sektörler","Favorilerim","Alarmlar","Hisse Karşılaştırma","Döviz / Altın / Emtia","Ekonomik Veriler","Ayarlar","Yardım & Destek","Hakkında","Çıkış Yap"}){Button b=button(m,NAVY2);b.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);content.addView(b,new LinearLayout.LayoutParams(-1,dp(50)));}
    }

'''
    s=s.replace(portfolio_anchor,more+portfolio_anchor,1)
# navigation corrections
s=s.replace('markets.setOnClickListener(v->showRadar());radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());more.setOnClickListener(v->showBaskets());','markets.setOnClickListener(v->showStrategySelection());radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());more.setOnClickListener(v->showMore());')
# Home strategy cards route to strategy selection instead of old baskets
s=s.replace('shortB.setOnClickListener(v->showBaskets());div.setOnClickListener(v->showBaskets());lng.setOnClickListener(v->showBaskets());','shortB.setOnClickListener(v->showStrategySelection());div.setOnClickListener(v->showStrategySelection());lng.setOnClickListener(v->showStrategySelection());')
# Dark text consistency in legacy detail cards
s=s.replace('Color.DKGRAY','Color.rgb(164,181,202)')
p.write_text(s,encoding='utf-8')
print('v150 V18 UI 7-11 + navigation PASS')

# V18 UI 7-11 + navigation/stability pass

# 7/11 Technical Analysis panel
tech_anchor='LinearLayout financial=card();'
if tech_anchor in s and 'Genel Teknik Görünüm' not in s:
    tech='''LinearLayout technical=card();technical.addView(bold("Teknik Analiz",18,Color.WHITE));String[][] ti={{"RSI","Momentum"},{"MACD","Trend"},{"Stochastic","Momentum"},{"CCI","Momentum"},{"EMA20 / 50 / 200","Trend"},{"Bollinger","Volatilite"},{"ATR","Risk"},{"SuperTrend","Trend"},{"Fibonacci","Seviye"}};for(String[] x:ti){technical.addView(txt(x[0]+"   •   "+x[1],13,Color.rgb(164,181,202)));}technical.addView(bold("Genel Teknik Görünüm",16,Color.WHITE));technical.addView(txt("Sinyal ve güven değerleri mevcut analiz motorundan hesaplanır.",12,Color.GRAY));content.addView(technical);spacer(8);
        '''
    s=s.replace(tech_anchor,tech+tech_anchor,1)

# 8/11 Target Price & Risk
risk_anchor='Button add=button("Portföye Ekle",GREEN);content.addView(add);'
if risk_anchor in s and 'Hedef Fiyat & Risk' not in s:
    risk='''LinearLayout risk=card();risk.addView(bold("Hedef Fiyat & Risk",18,Color.WHITE));risk.addView(txt("Kısa Vade Hedefi     —",13,Color.rgb(164,181,202)));risk.addView(txt("Orta Vade Hedefi     —",13,Color.rgb(164,181,202)));risk.addView(txt("Uzun Vade Hedefi     —",13,Color.rgb(164,181,202)));risk.addView(txt("Destek / Direnç      —",13,Color.rgb(164,181,202)));risk.addView(txt("Stop Referansı       "+money(r.stopReference,symbol),13,Color.rgb(164,181,202)));risk.addView(txt("Getiri / Risk        —",13,Color.rgb(164,181,202)));content.addView(risk);spacer(8);
        '''
    s=s.replace(risk_anchor,risk+risk_anchor,1)

# 9/11 Portfolio visual header
port_anchor='shell("Portföyüm");'
if port_anchor in s and 'Toplam Portföy' not in s:
    s=s.replace(port_anchor,port_anchor+''' LinearLayout summary=card();summary.addView(bold("Toplam Portföy",18,Color.WHITE));summary.addView(txt("Güncel değer ve günlük değişim, fiyatlar yenilendiğinde hesaplanır.",12,Color.rgb(164,181,202)));content.addView(summary);spacer(8);''',1)

# 10/11 Strategy Selection screen
basket_anchor='shell("100.000 TL • 3 Sepet");'
if basket_anchor in s and 'Strateji Seçimi' not in s:
    s=s.replace(basket_anchor,'''shell("Strateji Seçimi"); LinearLayout strategy=card();strategy.addView(bold("Strateji Seçimi",20,Color.WHITE));LinearLayout strategyButtons=new LinearLayout(this);for(String st:new String[]{"Kısa Vade","Temettü","Uzun Vade"}){Button sb=button(st,NAVY2);strategyButtons.addView(sb,new LinearLayout.LayoutParams(0,dp(64),1));}strategy.addView(strategyButtons);for(String criterion:new String[]{"✓ Teknik Analiz","✓ Temel Analiz","✓ Haber Taraması","✓ Sektör Analizi","✓ Büyük Alıcı / Satıcı","✓ Finansal Güç","✓ Temettü Potansiyeli"})strategy.addView(txt(criterion,14,Color.rgb(190,205,224)));Button startScan=button("Taramayı Başlat",GREEN);strategy.addView(startScan);startScan.setOnClickListener(v->showRadar());content.addView(strategy);spacer(8);''',1)

# 11/11 More screen
portfolio_method='    private void showPortfolio() {'
if portfolio_method in s and 'private void showMore()' not in s:
    more='''    private void showMore() {
        shell("Diğer"); LinearLayout profile=card();profile.addView(bold("BorsaRadar",20,Color.WHITE));profile.addView(txt("Piyasa araçları ve uygulama seçenekleri",13,Color.rgb(164,181,202)));content.addView(profile);spacer(8);
        for(String item:new String[]{"Piyasa Takvimi","Sektörler","Favorilerim","Alarmlar","Hisse Karşılaştırma","Döviz / Altın / Emtia","Ekonomik Veriler","Ayarlar","Yardım & Destek","Hakkında","Çıkış Yap"}){Button b=button(item,NAVY2);content.addView(b,new LinearLayout.LayoutParams(-1,dp(50)));spacer(4);}
    }

'''
    s=s.replace(portfolio_method,more+portfolio_method,1)

# Navigation: More must open More, Piyasalar remains non-scanning market view via radar screen
s=s.replace('more.setOnClickListener(v->showBaskets())','more.setOnClickListener(v->showMore())')

# Bottom-nav visual placement: move nav from above content to below scroll view
old='home.setOnClickListener(v->showHome());markets.setOnClickListener(v->showRadar());radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());more.setOnClickListener(v->showMore());root.addView(nav);'
new='home.setOnClickListener(v->showHome());markets.setOnClickListener(v->showRadar());radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());more.setOnClickListener(v->showMore());'
s=s.replace(old,new)
foot='TextView foot=txt("BorsaRadar • teknik + haber/katalizör bağlamı",11,Color.rgb(100,110,124)); foot.setGravity(Gravity.CENTER); root.addView(foot); setContentView(root);'
if foot in s:s=s.replace(foot,'root.addView(nav); setContentView(root);')

# Dark-card text cleanup for key legacy sections
s=s.replace('bold("Portföy boş",19,NAVY)','bold("Portföy boş",19,Color.WHITE)')
s=s.replace('bold("Tüm hisseler • hafif tarama",19,NAVY)','bold("Radar Taraması",19,Color.WHITE)')
s=s.replace('bold("En güçlü adaylar",18,NAVY)','bold("En güçlü adaylar",18,Color.WHITE)')

p.write_text(s,encoding='utf-8')
print('V18 UI 7-11 navigation stability PASS')

# V18 usability/stability pass: make added controls honest and actionable
# Exchange chips: explicit navigation only, never auto-scan
s=s.replace('content.addView(exchanges);','content.addView(exchanges);for(int i=0;i<exchanges.getChildCount();i++){final int mi=i;exchanges.getChildAt(i).setOnClickListener(v->{getSharedPreferences(PREFS,MODE_PRIVATE).edit().putInt("v18_market",mi).apply();Toast.makeText(this,"Piyasa seçildi — tarama yalnızca Tara ile başlar",Toast.LENGTH_SHORT).show();});}',1)
# Strategy criteria are labels, not fake checked checkboxes
s=s.replace('new String[]{"☑ Teknik Analiz","☑ Temel Analiz","☑ Haber Taraması","☑ Sektör Analizi","☑ Büyük Alıcı / Satıcı","☑ Finansal Güç","☑ Temettü Potansiyeli"}','new String[]{"Teknik Analiz","Temel Analiz","Haber Taraması","Sektör Analizi","Büyük Alıcı / Satıcı","Finansal Güç","Temettü Potansiyeli"}')
# Financial and technical placeholders clearly unavailable rather than invented
s=s.replace('technical.addView(txt(tr+"                         —",13','technical.addView(txt(tr+"                         Veri bekleniyor",13')
s=s.replace('risk.addView(txt(rr+"                         —",13','risk.addView(txt(rr+"                         Veri bekleniyor",13')
# Add persistent last-screen intent for core navigation
s=s.replace('home.setOnClickListener(v->showHome());','home.setOnClickListener(v->{getSharedPreferences(PREFS,MODE_PRIVATE).edit().putString("v18_screen","home").apply();showHome();});')
s=s.replace('radar.setOnClickListener(v->showRadar());','radar.setOnClickListener(v->{getSharedPreferences(PREFS,MODE_PRIVATE).edit().putString("v18_screen","radar").apply();showRadar();});')
s=s.replace('portfolio.setOnClickListener(v->showPortfolio());','portfolio.setOnClickListener(v->{getSharedPreferences(PREFS,MODE_PRIVATE).edit().putString("v18_screen","portfolio").apply();showPortfolio();});')
# Do not misrepresent Markets as Strategy: rename nav target until dedicated markets screen is wired
s=s.replace('markets.setOnClickListener(v->showStrategySelection());','markets.setOnClickListener(v->{Toast.makeText(this,"Piyasalar ekranı hazırlanıyor",Toast.LENGTH_SHORT).show();});')
p.write_text(s,encoding='utf-8')
print('v150 V18 usability pass PASS')

# Dedicated V18 Markets screen
anchor='    private void showStrategySelection() {'
if anchor in s and 'private void showMarkets()' not in s:
    method='''    private void showMarkets() {
        shell("Piyasalar");
        LinearLayout pick=card();pick.addView(bold("Piyasa Seçimi",18,Color.WHITE));LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);for(String x:new String[]{"BIST","Almanya","ABD","Tümü"}){Button b=button(x,NAVY2);row.addView(b,new LinearLayout.LayoutParams(0,dp(44),1));b.setOnClickListener(v->{getSharedPreferences(PREFS,MODE_PRIVATE).edit().putString("v18_market_name",x).apply();Toast.makeText(this,x+" seçildi",Toast.LENGTH_SHORT).show();});}pick.addView(row);content.addView(pick);spacer(8);
        LinearLayout summary=card();summary.addView(bold("Piyasa Özeti",18,Color.WHITE));for(String x:new String[]{"BIST 100","DAX","S&P 500","NASDAQ"})summary.addView(txt(x+"                         —",14,Color.rgb(164,181,202)));content.addView(summary);spacer(8);
        Button scan=button("Radar Taramasına Git",GREEN);scan.setOnClickListener(v->showRadar());content.addView(scan,new LinearLayout.LayoutParams(-1,dp(52)));
    }

'''
    s=s.replace(anchor,method+anchor,1)
s=s.replace('markets.setOnClickListener(v->{Toast.makeText(this,"Piyasalar ekranı hazırlanıyor",Toast.LENGTH_SHORT).show();});','markets.setOnClickListener(v->{getSharedPreferences(PREFS,MODE_PRIVATE).edit().putString("v18_screen","markets").apply();showMarkets();});')
p.write_text(s,encoding='utf-8')
print('V18 markets screen PASS')

# V18 20-step interaction pass
# Home exchange buttons: selected market state + explicit scan behavior
s=s.replace('Toast.makeText(this,"Piyasa seçildi — tarama yalnızca Tara ile başlar",Toast.LENGTH_SHORT).show();','Toast.makeText(this,"Piyasa seçildi — tarama yalnızca Tara ile başlar",Toast.LENGTH_SHORT).show();')
# Make strategy criteria actual toggles instead of decorative labels
old='for(String c:new String[]{"Teknik Analiz","Temel Analiz","Haber Taraması","Sektör Analizi","Büyük Alıcı / Satıcı","Finansal Güç","Temettü Potansiyeli"})criteria.addView(txt(c,14,Color.rgb(210,220,232)));'
new='for(String c:new String[]{"Teknik Analiz","Temel Analiz","Haber Taraması","Sektör Analizi","Büyük Alıcı / Satıcı","Finansal Güç","Temettü Potansiyeli"}){CheckBox cb=new CheckBox(this);cb.setText(c);cb.setTextColor(Color.rgb(210,220,232));cb.setChecked(true);criteria.addView(cb);}'
s=s.replace(old,new)
# Strategy cards remember selection
s=s.replace('for(String st:new String[]{"Kısa Vade","Temettü","Uzun Vade"}){Button b=button(st,NAVY2);b.setTextSize(17);content.addView(b,new LinearLayout.LayoutParams(-1,dp(64)));spacer(6);}','for(String st:new String[]{"Kısa Vade","Temettü","Uzun Vade"}){Button b=button(st,NAVY2);b.setTextSize(17);content.addView(b,new LinearLayout.LayoutParams(-1,dp(64)));spacer(6);b.setOnClickListener(v->{getSharedPreferences(PREFS,MODE_PRIVATE).edit().putString("v18_strategy",st).apply();Toast.makeText(this,st+" seçildi",Toast.LENGTH_SHORT).show();});}')
# More screen buttons get safe explicit feedback rather than dead taps
s=s.replace('b.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);content.addView(b,new LinearLayout.LayoutParams(-1,dp(50)));','b.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);content.addView(b,new LinearLayout.LayoutParams(-1,dp(50)));b.setOnClickListener(v->Toast.makeText(this,m+" — modül bağlantısı hazırlanıyor",Toast.LENGTH_SHORT).show());')
# Market selection persists and never scans
# Add compact data-source status to market screen
s=s.replace('LinearLayout summary=card();summary.addView(bold("Piyasa Özeti",18,Color.WHITE));','LinearLayout summary=card();summary.addView(bold("Piyasa Özeti",18,Color.WHITE));summary.addView(txt("Canlı veri yoksa değerler — olarak gösterilir.",11,Color.GRAY));')
# Search: Enter opens detail when symbol exists
search_marker='content.addView(search,new LinearLayout.LayoutParams(-1,dp(48)));'
if search_marker in s:
    s=s.replace(search_marker,search_marker+'search.setSingleLine(true);search.setOnEditorActionListener((v,a,e)->{String q=search.getText().toString().trim().toUpperCase();if(q.length()>0){renderStockDetail(q,null,null);}return true;});',1)
# Radar empty state copy
s=s.replace('Radar sonucu yok.','Radar sonucu yok. Taramayı başlatmak için Tara butonunu kullanın.')
# Add version/status card to More
s=s.replace('profile.addView(txt("Piyasa araçları ve uygulama seçenekleri",13,Color.rgb(164,181,202)));','profile.addView(txt("Piyasa araçları ve uygulama seçenekleri",13,Color.rgb(164,181,202)));profile.addView(txt("V18 UI • veri olmayan alanlarda tahmin gösterilmez",11,Color.GRAY));')
p.write_text(s,encoding='utf-8')
print('V18 20-step interaction pass PASS')

# V18 stability cleanup
s=s.replace('renderStockDetail(q,null,null);','analyzeStock(q);')
s=s.replace('more.setOnClickListener(v->showBaskets());','more.setOnClickListener(v->showMore());')
s=s.replace('markets.setOnClickListener(v->showRadar());','markets.setOnClickListener(v->showMarkets());')
s=s.replace('shell("Portföyüm");','shell("Portföy");')
s=s.replace('summary.addView(txt(x+"                         —",14','summary.addView(txt(x+"                         Veri bekleniyor",14')
p.write_text(s,encoding='utf-8')
print('V18 stability cleanup PASS')

# V18 generated-source verification
required=['showHome()','showMarkets()','showStrategySelection()','showMore()','Radar Sonuçları','Finansal Veriler','Teknik Analiz','Hedef Fiyat & Risk','Ana Sayfa','Piyasalar','Portföy']
missing=[x for x in required if x not in s]
if missing: raise SystemExit('V18 source missing: '+', '.join(missing))
if 'analyzeStock(String symbol)' not in s: raise SystemExit('analysis entry point missing')
if 'savePortfolio' not in s or 'loadPortfolio' not in s: raise SystemExit('portfolio persistence missing')
p.write_text(s,encoding='utf-8')
print('V18 source verification PASS')
