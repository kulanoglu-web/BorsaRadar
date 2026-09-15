from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='''            List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"6mo");
            if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi");
            final List<MarketDataService.Candle> data=d;
            main.post(()->renderFastTechnicalDetail(symbol,data));
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,data);'''
new='''            // Fast first paint: only fetch the recent window needed by the technical preview.
            // Deep analysis receives longer history separately and must never block the first card.
            List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"1mo");
            if(d==null||d.size()<12) d=MarketDataService.fetchDaily(symbol,"3mo");
            if(d==null||d.size()<12)throw new Exception("yetersiz fiyat verisi");
            final List<MarketDataService.Candle> data=d;
            main.post(()->renderFastTechnicalDetail(symbol,data));
            List<MarketDataService.Candle> deep=MarketDataService.fetchDaily(symbol,"6mo");
            if(deep==null||deep.size()<20) deep=data;
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,deep);'''
if old not in s: raise SystemExit('fast detail fetch anchor missing')
s=s.replace(old,new,1)
# Avoid waiting for FX network refresh before fetching the stock. Cached conversion can refresh later.
s=s.replace('''            CurrencyService.refreshIfNeeded();
            // Fast first paint:''','''            // Fast first paint:''',1)
p.write_text(s,encoding='utf-8')
