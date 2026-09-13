from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Robust decision-data loader: retry broader daily windows before giving up.
helper='''
    private List<MarketDataService.Candle> fetchDecisionData(String symbol) throws Exception {
        Exception last=null;
        String[] ranges={"3mo","6mo","1y"};
        for(String range:ranges){
            try{
                List<MarketDataService.Candle> d=MarketDataService.fetchDaily(symbol,range);
                if(d!=null && d.size()>=20) return d;
                last=new Exception("Yetersiz karar verisi: "+(d==null?0:d.size())+" gün");
            }catch(Exception e){ last=e; }
        }
        throw last==null?new Exception("Karar verisi alınamadı"):last;
    }
'''
anchor='    private void analyzeStock(String symbol) {'
if 'private List<MarketDataService.Candle> fetchDecisionData' not in s:
    s=s.replace(anchor,helper+'\n'+anchor)

# Replace the direct 3mo fetch inside analyzeStock only.
old='''                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"3mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);'''
new='''                List<MarketDataService.Candle>d=fetchDecisionData(symbol);
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);'''
s=s.replace(old,new,1)

# If a previous formatting variant remains, normalize it too.
s=s.replace('List<MarketDataService.Candle> d=MarketDataService.fetchDaily(symbol,"3mo");\n                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);',
            'List<MarketDataService.Candle> d=fetchDecisionData(symbol);\n                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);',1)

# More useful error text instead of a generic failure.
s=s.replace('content.addView(txt("Veri alınamadı: "+e.getMessage(),15,RED));',
            'content.addView(txt("Karar verisi alınamadı ("+MarketSymbol.yahoo(symbol)+"): "+e.getMessage()+"\\nTekrar dene; bağlantı/veri kaynağı geçici olarak cevap vermiyor olabilir.",15,RED));')

# Foreign stock detail values should use the portfolio display currency too.
s=s.replace('''LinearLayout q=card();q.addView(bold(symbol,22,NAVY));q.addView(bold(money(r.price),25,r.changePct>=0?GREEN:RED));''',
'''LinearLayout q=card();q.addView(bold(MarketSymbol.label(symbol),22,NAVY));
        double detailRate=MarketSymbol.marketIndex(symbol)==2?ensureUsdToEur():1.0;
        double detailPrice=MarketSymbol.marketIndex(symbol)==2?r.price*detailRate:r.price;
        q.addView(bold(String.format(Locale.US,"%.2f %s",detailPrice,MarketSymbol.currency(symbol)),25,r.changePct>=0?GREEN:RED));''')

s=s.replace('''"  •  Stop ref. "+money(r.stopReference)''',
'''"  •  Stop ref. "+String.format(Locale.US,"%.2f %s",MarketSymbol.marketIndex(symbol)==2?r.stopReference*detailRate:r.stopReference,MarketSymbol.currency(symbol))''')

# Ziraat handoff is BIST-only; hiding it for foreign stocks prevents a misleading action path.
old_trade='''        LinearLayout tradeRow=new LinearLayout(this); tradeRow.setOrientation(LinearLayout.HORIZONTAL);
        Button buy=button("Ziraat'ta AL",GREEN), sell=button("Ziraat'ta SAT",RED);
        tradeRow.addView(buy,new LinearLayout.LayoutParams(0,-2,1));tradeRow.addView(sell,new LinearLayout.LayoutParams(0,-2,1));content.addView(tradeRow);
        buy.setOnClickListener(v->prepareOrder(symbol,r.price,"AL"));sell.setOnClickListener(v->prepareOrder(symbol,r.price,"SAT"));
        content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir. ← → ile diğer hisselere geçebilirsin.",12,Color.GRAY));'''
new_trade='''        if(MarketSymbol.isTurkey(symbol)){
            LinearLayout tradeRow=new LinearLayout(this); tradeRow.setOrientation(LinearLayout.HORIZONTAL);
            Button buy=button("Ziraat'ta AL",GREEN), sell=button("Ziraat'ta SAT",RED);
            tradeRow.addView(buy,new LinearLayout.LayoutParams(0,-2,1));tradeRow.addView(sell,new LinearLayout.LayoutParams(0,-2,1));content.addView(tradeRow);
            buy.setOnClickListener(v->prepareOrder(symbol,r.price,"AL"));sell.setOnClickListener(v->prepareOrder(symbol,r.price,"SAT"));
            content.addView(txt("Emir burada hazırlanır; nihai onay Ziraat Trader içinde verilir. ← → ile diğer hisselere geçebilirsin.",12,Color.GRAY));
        } else {
            content.addView(txt("Yurt dışı hisselerde emir aktarımı yoktur; analiz ve portföy takibi yapılır.",12,Color.GRAY));
        }'''
s=s.replace(old_trade,new_trade)

p.write_text(s,encoding='utf-8')

# v3.10.1
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 42',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.10.1'",g)
b.write_text(g,encoding='utf-8')
