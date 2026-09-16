from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v107: make detail re-entry safe and prefer cached candles so the UI does not wait on network again.
# Always release the loading guard after a successful full render/cache write.
needle='if(singleStockCache.size()>24)singleStockCache.clear(); singleStockCache.put(symbol,new java.util.ArrayList<>(data));'
if needle in s and 'singleStockLoading.remove(symbol);' not in s[s.find(needle):s.find(needle)+260]:
    s=s.replace(needle,needle+'\n            singleStockLoading.remove(symbol);',1)
# If cached candles exist, use them immediately instead of refetching 3/6 months on every detail entry.
old='''List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"3mo");
            if(d==null||d.size()<30) d=MarketDataService.fetchDaily(symbol,"6mo");
            if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi");'''
new='''List<MarketDataService.Candle>d=singleStockCache.get(symbol);
            if(d==null||d.size()<20){d=MarketDataService.fetchDaily(symbol,"3mo");if(d==null||d.size()<30)d=MarketDataService.fetchDaily(symbol,"6mo");}
            if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi");'''
if old in s:s=s.replace(old,new,1)
# A stale loading flag must never permanently block a user retry. Replace hard return with cache-first retry.
s=s.replace('if(singleStockLoading.contains(symbol))return;','if(singleStockLoading.contains(symbol)&&singleStockCache.containsKey(symbol)){renderFastTechnicalDetail(symbol,singleStockCache.get(symbol));return;}\n        singleStockLoading.remove(symbol);',1)
p.write_text(s,encoding='utf-8')
