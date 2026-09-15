from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='''            List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"6mo");
            if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi");
            final List<MarketDataService.Candle> data=d;
            main.post(()->renderFastTechnicalDetail(symbol,data));
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,data);'''
new='''            // Fast first paint: fetch only recent data first.
            List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"1mo");
            if(d==null||d.size()<12) d=MarketDataService.fetchDaily(symbol,"3mo");
            if(d==null||d.size()<12)throw new Exception("yetersiz fiyat verisi");
            final List<MarketDataService.Candle> data=d;
            main.post(()->renderFastTechnicalDetail(symbol,data));
            // Keep deep analysis independent from the immutable fast-preview data.
            List<MarketDataService.Candle> deepTmp=MarketDataService.fetchDaily(symbol,"6mo");
            final List<MarketDataService.Candle> deep=(deepTmp!=null&&deepTmp.size()>=20)?deepTmp:data;
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,deep);'''
if old not in s: raise SystemExit('fast detail fetch anchor missing')
s=s.replace(old,new,1)
s=s.replace('''            CurrencyService.refreshIfNeeded();
            // Fast first paint:''','''            // Fast first paint:''',1)
# renderStockDetail must use the same immutable deep data, not a stale/mutated variable.
s=s.replace('''            List<MarketDataService.Candle>chart=data.subList(Math.max(0,data.size()-10),data.size());''','''            List<MarketDataService.Candle>chart=deep.subList(Math.max(0,deep.size()-10),deep.size());''',1)
p.write_text(s,encoding='utf-8')
