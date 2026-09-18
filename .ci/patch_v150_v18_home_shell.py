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
