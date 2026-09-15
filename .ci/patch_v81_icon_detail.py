from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Add compact icon navigation to stock detail without removing existing chart/analysis content.
anchor='content.addView(quote); spacer(7);'
if anchor in s and '"📊 Genel"' not in s:
    ui='''content.addView(quote); spacer(7);
        LinearLayout iconRow=new LinearLayout(this); iconRow.setOrientation(LinearLayout.HORIZONTAL);
        String[] iconTabs={"📊 Genel","📈 Grafik","📰 Haber","🏛 KAP","🏦 Takas","🧪 Test","🎯 Tahmin"};
        for(String it:iconTabs){TextView ib=txt(it,11,Color.WHITE); ib.setGravity(Gravity.CENTER); ib.setPadding(dp(5),dp(10),dp(5),dp(10)); ib.setBackgroundColor(Color.rgb(43,49,57)); iconRow.addView(ib,new LinearLayout.LayoutParams(0,-2,1));}
        content.addView(iconRow); spacer(7);
        LinearLayout flow=card(); flow.addView(bold("🏦 Kurumsal Alım / Satım",17,Color.WHITE));
        flow.addView(txt("Banka • aracı kurum • fon • büyük yatırımcı akışı",12,Color.LTGRAY));
        flow.addView(txt("Gerçek takas/kurumsal veri geldiğinde: en çok alanlar, en çok satanlar, net değişim ve süreklilik burada gösterilecek.",12,Color.GRAY));
        flow.addView(txt("Veri yoksa AL/SAT puanına etki etmez; tahmini kurum hareketi üretilmez.",12,Color.GRAY));
        content.addView(flow); spacer(7);'''
    s=s.replace(anchor,ui,1)
p.write_text(s,encoding='utf-8')
