from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Cache the last successful candle set per symbol so reopening the same stock is instant.
field='    private final java.util.Map<String,java.util.List<MarketDataService.Candle>> singleStockCache = new java.util.concurrent.ConcurrentHashMap<>();\n    private final java.util.Set<String> singleStockLoading = java.util.Collections.newSetFromMap(new java.util.concurrent.ConcurrentHashMap<String,Boolean>());\n'
anchor='    private final ExecutorService detailIo = Executors.newFixedThreadPool(2);'
if anchor not in s: raise SystemExit('detail executor missing')
if 'singleStockCache' not in s:s=s.replace(anchor,anchor+'\n'+field,1)
# Cache every successful fast data set before rendering; this also gives one authoritative latest close.
needle='final List<MarketDataService.Candle> data=d;\n            main.post(()->renderFastTechnicalDetail(symbol,data));'
if needle not in s: raise SystemExit('fast data anchor missing')
s=s.replace(needle,'final List<MarketDataService.Candle> data=d;\n            singleStockCache.put(symbol,new java.util.ArrayList<>(data));\n            main.post(()->renderFastTechnicalDetail(symbol,data));',1)
# Always display price from the candle set shown on screen; no provider-result placeholder.
old='q.addView(bold(money(last.close,symbol),28,ch>=0?GREEN:RED));'
if old not in s: raise SystemExit('fast quote anchor missing')
s=s.replace(old,'q.addView(bold(last.close>0?money(last.close,symbol):"Fiyat bekleniyor",28,ch>=0?GREEN:RED));',1)
# v84 guessed an openSingleStock method. Replace refresh with a known analyzeStock path and clear cache only on explicit refresh.
s=s.replace('refresh.setOnClickListener(v->{ try{ openSingleStock(symbol); }catch(Throwable ignored){} });','refresh.setOnClickListener(v->{ singleStockCache.remove(symbol); singleStockLoading.remove(symbol); analyzeStock(symbol); });')
# At analyzeStock entry, immediately reuse cached result and prevent duplicate concurrent requests.
start=s.find('private void analyzeStock(String symbol)')
if start<0: raise SystemExit('analyzeStock missing')
brace=s.find('{',start)
insert='\n        java.util.List<MarketDataService.Candle> cached=singleStockCache.get(symbol);\n        if(cached!=null&&!cached.isEmpty()){ renderFastTechnicalDetail(symbol,cached); return; }\n        if(!singleStockLoading.add(symbol)) return;\n'
if 'singleStockLoading.add(symbol)' not in s:s=s[:brace+1]+insert+s[brace+1:]
# Release loading lock as soon as fast data is available; explicit refresh can then work normally.
s=s.replace('singleStockCache.put(symbol,new java.util.ArrayList<>(data));','singleStockCache.put(symbol,new java.util.ArrayList<>(data));\n            singleStockLoading.remove(symbol);',1)
# Ensure failures do not permanently lock a symbol. Add to catch blocks in analyzeStock region only where possible.
start=s.find('private void analyzeStock(String symbol)'); end=s.find('private void renderFastTechnicalDetail',start)
if end<0:end=s.find('private void renderStockDetail',start)
block=s[start:end]
block=block.replace('catch(Exception e){','catch(Exception e){ singleStockLoading.remove(symbol);',1)
s=s[:start]+block+s[end:]
p.write_text(s,encoding='utf-8')
