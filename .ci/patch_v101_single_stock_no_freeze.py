from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v103: single-stock must paint quickly, but full indicators need >=30 daily candles.
# Fetch 3mo once (normally ~60 trading days): no duplicate 6mo request and enough history.
s=s.replace('List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"1mo");\n            if(d==null||d.size()<12) d=MarketDataService.fetchDaily(symbol,"3mo");\n            if(d==null||d.size()<12)throw new Exception("yetersiz fiyat verisi");',
'''List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"3mo");
            if(d==null||d.size()<30) d=MarketDataService.fetchDaily(symbol,"6mo");
            if(d==null||d.size()<20)throw new Exception("yetersiz fiyat verisi");''',1)
old='''            // Keep deep analysis independent from the immutable fast-preview data.
            List<MarketDataService.Candle> deepTmp=MarketDataService.fetchDaily(symbol,"6mo");
            final List<MarketDataService.Candle> deep=(deepTmp!=null&&deepTmp.size()>=20)?deepTmp:data;
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,deep);'''
new='''            final List<MarketDataService.Candle> deep=data;
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,deep);'''
if old in s:s=s.replace(old,new,1)
# Also handle source already transformed by previous v101 wording.
old2='''            // Do not block single-stock UI on a second network request.
            // Reuse the already downloaded candles; 3mo fallback supplies enough history when 1mo is short.
            final List<MarketDataService.Candle> deep=data;
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,deep);'''
if old2 in s:s=s.replace(old2,new,1)
# A failed request must always release the per-symbol loading lock so retry cannot appear frozen.
oldcatch='''        }catch(Exception e){main.post(()->Toast.makeText(this,"Analiz hatası: "+e.getMessage(),Toast.LENGTH_LONG).show());}
    }'''
newcatch='''        }catch(Exception e){singleStockLoading.remove(symbol);main.post(()->Toast.makeText(this,"Analiz hatası: "+e.getMessage(),Toast.LENGTH_LONG).show());}
    }'''
if oldcatch in s:s=s.replace(oldcatch,newcatch,1)
needle='singleStockCache.put(symbol,new java.util.ArrayList<>(data));'
repl='if(singleStockCache.size()>24)singleStockCache.clear(); singleStockCache.put(symbol,new java.util.ArrayList<>(data));'
if needle in s and repl not in s:s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')
