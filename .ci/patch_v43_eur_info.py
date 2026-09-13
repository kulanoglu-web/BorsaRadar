from pathlib import Path
import re

mainp=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=mainp.read_text(encoding='utf-8')

# 1) Foreign portfolio values are presented in EUR. German quotes are already EUR;
# US quotes are converted from USD with EURUSD=X when portfolio refresh runs.
s=s.replace('private volatile boolean scanRunning=false;', 'private volatile boolean scanRunning=false;\n    private volatile double usdToEur=1.0;\n    private volatile long usdToEurAt=0L;')

helper='''\n    private double ensureUsdToEur(){
        long now=System.currentTimeMillis();
        if(usdToEurAt>0 && now-usdToEurAt<30*60*1000L) return usdToEur;
        synchronized(this){
            now=System.currentTimeMillis();
            if(usdToEurAt>0 && now-usdToEurAt<30*60*1000L) return usdToEur;
            try{
                List<MarketDataService.Candle> fx=MarketDataService.fetchDaily("US:EURUSD=X","5d");
                if(fx!=null && !fx.isEmpty()){
                    double eurUsd=fx.get(fx.size()-1).close;
                    if(eurUsd>0.5 && eurUsd<2.5){ usdToEur=1.0/eurUsd; usdToEurAt=now; }
                }
            }catch(Exception ignored){}
            return usdToEur;
        }
    }

    private double displayPrice(String symbol,double nativePrice){
        return MarketSymbol.marketIndex(symbol)==2 ? nativePrice*usdToEur : nativePrice;
    }
'''
anchor='    private int dp(int x) { return Math.round(x * getResources().getDisplayMetrics().density); }'
if helper.strip() not in s:
    s=s.replace(anchor,helper+'\n'+anchor)

# 2) Portfolio card: P/L and last price in EUR for both foreign markets.
s=s.replace('''            double pnl=(s.price-h.cost)*h.qty, pct=h.cost>0?(s.price/h.cost-1)*100:0;
            c.addView(bold("Son  "+String.format(Locale.US,"%.2f %s",s.price,MarketSymbol.currency(h.symbol))+"   P/L  "+String.format(Locale.US,"%.2f %s",pnl,MarketSymbol.currency(h.symbol))+"  (%"+fmt(pct)+")",16,pnl>=0?GREEN:RED));''','''            double shownPrice=displayPrice(h.symbol,s.price);
            double pnl=(shownPrice-h.cost)*h.qty, pct=h.cost>0?(shownPrice/h.cost-1)*100:0;
            c.addView(bold("Son  "+String.format(Locale.US,"%.2f %s",shownPrice,MarketSymbol.currency(h.symbol))+"   K/Z  "+String.format(Locale.US,"%.2f %s",pnl,MarketSymbol.currency(h.symbol))+"  (%"+fmt(pct)+")",16,pnl>=0?GREEN:RED));''')
s=s.replace('''"  •  Stop ref. "+money(s.stopReference)''','''"  •  Stop ref. "+String.format(Locale.US,"%.2f %s",displayPrice(h.symbol,s.stopReference),MarketSymbol.currency(h.symbol))''')

# 3) Make V35 holding cost comparison correct for US positions whose entered cost is EUR.
s=s.replace('''V35HybridEngine.Result v35=V35HybridEngine.analyze(d,h.cost);
                double pnlPct=h.cost>0?(v35.price/h.cost-1)*100:0;''','''double eurRate=MarketSymbol.marketIndex(h.symbol)==2?ensureUsdToEur():1.0;
                double nativeCost=MarketSymbol.marketIndex(h.symbol)==2 && eurRate>0?h.cost/eurRate:h.cost;
                V35HybridEngine.Result v35=V35HybridEngine.analyze(d,nativeCost);
                double shownV35Price=MarketSymbol.marketIndex(h.symbol)==2?v35.price*eurRate:v35.price;
                double pnlPct=h.cost>0?(shownV35Price/h.cost-1)*100:0;''')

# Ensure USD/EUR rate is available before US quote analysis even if patch38 text changed.
s=s.replace('''try { List<MarketDataService.Candle> d=MarketDataService.fetchDaily(h.symbol,"1mo");''','''try { if(MarketSymbol.marketIndex(h.symbol)==2) ensureUsdToEur(); List<MarketDataService.Candle> d=MarketDataService.fetchDaily(h.symbol,"1mo");''')

# 4) Close autocomplete list immediately after user selects a stock.
for var in ('sym','x'):
    needle=f'{var}.setThreshold(1); {var}.setSingleLine(true);'
    add=needle+f'''\n        {var}.setOnItemClickListener((p,v,pos,id)->{{ {var}.dismissDropDown(); {var}.clearFocus(); }});'''
    s=s.replace(needle,add)

# 5) Foreign buy price field explicitly says EUR and changes with market selection.
s=s.replace('EditText cost=new EditText(this); cost.setHint("Alış fiyatı");', 'EditText cost=new EditText(this); cost.setHint("Alış fiyatı (₺)");')
s=s.replace('''sym.setAdapter(new ArrayAdapter<>(MainActivity.this,android.R.layout.simple_dropdown_item_1line,a));
                if(sym.getText().length()>0) sym.post(sym::showDropDown);''','''sym.setAdapter(new ArrayAdapter<>(MainActivity.this,android.R.layout.simple_dropdown_item_1line,a));
                cost.setHint(pos==0?"Alış fiyatı (₺)":"Alış fiyatı (€)");
                if(sym.getText().length()>0) sym.post(sym::showDropDown);''')

# 6) Auto refresh after save so portfolio immediately gets P/L and recommendation.
s=s.replace('''savePortfolio();showPortfolio();
                    }catch(Exception ex){Toast.makeText(this,"Hisse kodu / adet / fiyatı kontrol et",Toast.LENGTH_LONG).show();}''','''savePortfolio();showPortfolio();
                        main.postDelayed(this::refreshPortfolio,180);
                    }catch(Exception ex){Toast.makeText(this,"Hisse kodu / adet / fiyatı kontrol et",Toast.LENGTH_LONG).show();}''')

# 7) Add Info button to navigation.
old='''Button p=button("Portföy",NAVY2), r=button("Radar",GREEN), one=button("Tek Hisse",PURPLE), three=button("3 Sepet",AMBER);
        nav.addView(p,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(r,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(one,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(three,new LinearLayout.LayoutParams(0,-2,1));
        p.setOnClickListener(v->showPortfolio()); r.setOnClickListener(v->showRadar());
        one.setOnClickListener(v->singleStockDialog()); three.setOnClickListener(v->showBaskets());'''
new='''Button p=button("Portföy",NAVY2), r=button("Radar",GREEN), one=button("Tek Hisse",PURPLE), three=button("3 Sepet",AMBER), info=button("ⓘ",Color.DKGRAY);
        nav.addView(p,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(r,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(one,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(three,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(info,new LinearLayout.LayoutParams(0,-2,.45f));
        p.setOnClickListener(v->showPortfolio()); r.setOnClickListener(v->showRadar());
        one.setOnClickListener(v->singleStockDialog()); three.setOnClickListener(v->showBaskets()); info.setOnClickListener(v->showInfo());'''
s=s.replace(old,new)

# 8) Copyright footer.
s=s.replace('BorsaRadar • 1–10 işlem günü odaklı teknik karar destek','© 2026 Erdoğan Kulanoğlu • BorsaRadar • Tüm hakları saklıdır')

# 9) Multilingual information, risk, privacy and usage-rights screen.
info_method='''
    private void showInfo(){
        ScrollView scroll=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(8),dp(18),dp(18));
        box.addView(bold("BorsaRadar • Bilgi / Info",20,NAVY));
        box.addView(txt("Kısa kullanım: Piyasa seç, hisse kodunun ilk harfini yaz, listeden hisseyi seç. Portföyde adet ve alış fiyatını gir. Türkiye ₺, Almanya ve ABD portföy değerleri € olarak gösterilir. ABD fiyatları güncel USD/EUR kuru ile Euro'ya çevrilir.",14,Color.DKGRAY));
        box.addView(bold("Türkçe — Risk ve sorumluluk",16,RED));
        box.addView(txt("Bu uygulama yatırım danışmanlığı değildir. AL, TUT, SAT, erken kırılım, hedef, stop, güven yüzdesi ve benzeri göstergeler yalnızca teknik karar desteğidir; doğruluk, kazanç veya sonuç garantisi yoktur. Hisse senetleri yüksek risk içerir ve yatırılan sermayenin bir kısmı veya tamamı kaybedilebilir. Yatırım kararları tamamen kullanıcıya aittir. Geliştirici, piyasa hareketleri, veri gecikmesi/yanlışlığı, bağlantı hatası, üçüncü taraf veri kaynakları veya uygulama kullanımından doğan mali kayıplardan sorumluluk kabul etmez.",13,Color.DKGRAY));
        box.addView(bold("Deutsch — Risiko & Haftung",16,RED));
        box.addView(txt("Diese App stellt keine Anlageberatung dar. Kauf-, Halte-, Verkaufs-, Breakout-, Ziel-, Stop- und Konfidenzsignale dienen ausschließlich als technische Entscheidungshilfe. Es gibt keine Garantie für Richtigkeit, Gewinn oder ein bestimmtes Ergebnis. Aktienanlagen sind mit erheblichen Risiken bis hin zum vollständigen Verlust des eingesetzten Kapitals verbunden. Anlageentscheidungen liegen allein beim Nutzer. Der Entwickler übernimmt keine Haftung für finanzielle Verluste infolge von Marktbewegungen, verzögerten/fehlerhaften Daten, Verbindungsproblemen, Drittanbieterdaten oder der Nutzung der App.",13,Color.DKGRAY));
        box.addView(bold("English — Risk & liability",16,RED));
        box.addView(txt("This app does not provide investment advice. Buy, hold, sell, breakout, target, stop and confidence signals are technical decision-support indicators only. No accuracy, profit or outcome is guaranteed. Investing in shares involves substantial risk, including loss of some or all invested capital. All investment decisions remain solely with the user. The developer accepts no liability for financial losses caused by market movements, delayed/inaccurate data, connectivity issues, third-party data or use of the app.",13,Color.DKGRAY));
        box.addView(bold("Gizlilik / Datenschutz / Privacy",16,NAVY));
        box.addView(txt("BorsaRadar geliştirici adına kişisel bilgi toplamaz, reklam profili oluşturmaz ve portföyünüzü geliştiriciye göndermez. Portföy kayıtları cihaz üzerinde tutulur. Piyasa verileri internet üzerinden üçüncü taraf servislerden alınır; bu servisler bağlantı sırasında IP adresi gibi teknik ağ verilerini kendi politikalarına göre işleyebilir. / BorsaRadar erhebt für den Entwickler keine personenbezogenen Daten und übermittelt Ihr Portfolio nicht an den Entwickler. Portfoliodaten bleiben auf dem Gerät. Marktdaten werden über Drittanbieter abgerufen; diese können technische Netzwerkdaten nach ihren eigenen Richtlinien verarbeiten. / BorsaRadar does not collect personal information on behalf of the developer or transmit your portfolio to the developer. Portfolio data remains on the device. Market data is obtained from third-party services, which may process technical network data under their own policies.",12,Color.DKGRAY));
        box.addView(bold("Kullanım hakları / Nutzungsrechte / Usage rights",16,NAVY));
        box.addView(txt("© 2026 Erdoğan Kulanoğlu. Tüm hakları saklıdır. BorsaRadar adı, uygulamaya özgü arayüz, açıklamalar ve geliştirilen karar destek yöntemleri izinsiz kopyalanamaz, yeniden yayımlanamaz veya ticari olarak dağıtılamaz. Üçüncü taraf kütüphane ve veri hizmetlerinin kendi lisans ve kullanım koşulları geçerlidir. / All rights reserved. App-specific content and methods may not be copied, republished or commercially distributed without permission. Third-party libraries and data services remain subject to their own terms and licenses.",12,Color.DKGRAY));
        box.addView(txt("Sürüm 3.10 • Teknik karar destek uygulaması",11,Color.GRAY));
        scroll.addView(box);
        new AlertDialog.Builder(this).setTitle("ⓘ BorsaRadar").setView(scroll).setPositiveButton("Tamam / OK",null).show();
    }
'''
marker='    private void showPortfolio() {'
if 'private void showInfo()' not in s:
    s=s.replace(marker,info_method+'\n'+marker)

mainp.write_text(s,encoding='utf-8')

# MarketSymbol: both foreign markets display EUR.
mp=Path('app/src/main/java/com/kulanoglu/borsaradar/MarketSymbol.java')
m=mp.read_text(encoding='utf-8')
m=m.replace('if(stored!=null && stored.startsWith("US:")) return "$";','if(stored!=null && stored.startsWith("US:")) return "€";')
mp.write_text(m,encoding='utf-8')

# Version 3.10.0
bp=Path('app/build.gradle')
b=bp.read_text(encoding='utf-8')
b=re.sub(r'versionCode\s+\d+','versionCode 41',b)
b=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.10.0'",b)
bp.write_text(b,encoding='utf-8')
