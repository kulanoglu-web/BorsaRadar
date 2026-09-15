from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v85 must be tolerant of the generated source produced by earlier patches.
field='    private final java.util.Map<String,java.util.List<MarketDataService.Candle>> singleStockCache = new java.util.concurrent.ConcurrentHashMap<>();\n    private final java.util.Set<String> singleStockLoading = java.util.Collections.newSetFromMap(new java.util.concurrent.ConcurrentHashMap<String,Boolean>());\n'
anchor='    private final ExecutorService detailIo = Executors.newFixedThreadPool(2);'
if anchor in s and 'singleStockCache' not in s:
    s=s.replace(anchor,anchor+'\n'+field,1)
# Use the candle price anywhere the fast renderer already exposes last.close.
s=s.replace('q.addView(bold(money(last.close,symbol),28,ch>=0?GREEN:RED));','q.addView(bold(last.close>0?money(last.close,symbol):"Fiyat bekleniyor",28,ch>=0?GREEN:RED));')
# Repair the v84 refresh callback: the generated source has analyzeStock, not openSingleStock.
s=s.replace('refresh.setOnClickListener(v->{ try{ openSingleStock(symbol); }catch(Throwable ignored){} });','refresh.setOnClickListener(v->{ analyzeStock(symbol); });')
# Cache insertion is optional because earlier patches can reshape this exact statement.
patterns=[
 'final List<MarketDataService.Candle> data=d;\n            main.post(()->renderFastTechnicalDetail(symbol,data));',
 'final List<MarketDataService.Candle> data=d; main.post(()->renderFastTechnicalDetail(symbol,data));'
]
for needle in patterns:
    if needle in s and 'singleStockCache.put(symbol' not in s:
        repl=needle.replace('main.post','singleStockCache.put(symbol,new java.util.ArrayList<>(data));\n            main.post')
        s=s.replace(needle,repl,1)
        break
# Only add cache reuse when both the cache field and known entry method exist.
start=s.find('private void analyzeStock(String symbol)')
if start>=0 and 'singleStockCache' in s and 'singleStockLoading.add(symbol)' not in s:
    brace=s.find('{',start)
    insert='\n        java.util.List<MarketDataService.Candle> cached=singleStockCache.get(symbol);\n        if(cached!=null&&!cached.isEmpty()){ renderFastTechnicalDetail(symbol,cached); return; }\n        if(!singleStockLoading.add(symbol)) return;\n'
    s=s[:brace+1]+insert+s[brace+1:]
# Release lock after a successful cache write when available.
s=s.replace('singleStockCache.put(symbol,new java.util.ArrayList<>(data));\n            main.post','singleStockCache.put(symbol,new java.util.ArrayList<>(data));\n            singleStockLoading.remove(symbol);\n            main.post',1)
# Compile guard: never leave the obsolete guessed method behind.
if 'openSingleStock(symbol)' in s: raise SystemExit('obsolete openSingleStock remains')
p.write_text(s,encoding='utf-8')
