from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v101: single-stock must paint quickly and never wait for a second 6mo network fetch.
# The fast 1mo/3mo candles are sufficient for immediate technical/target analysis;
# deeper sections can be refreshed explicitly from the detail screen later.
old='''            // Keep deep analysis independent from the immutable fast-preview data.
            List<MarketDataService.Candle> deepTmp=MarketDataService.fetchDaily(symbol,"6mo");
            final List<MarketDataService.Candle> deep=(deepTmp!=null&&deepTmp.size()>=20)?deepTmp:data;
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,deep);'''
new='''            // Do not block single-stock UI on a second network request.
            // Reuse the already downloaded candles; 3mo fallback supplies enough history when 1mo is short.
            final List<MarketDataService.Candle> deep=data;
            FullAnalysisEngine.Result a=FullAnalysisEngine.analyze(symbol,deep);'''
if old in s:s=s.replace(old,new,1)
# A failed request must always release the per-symbol loading lock so retry cannot appear frozen.
oldcatch='''        }catch(Exception e){main.post(()->Toast.makeText(this,"Analiz hatası: "+e.getMessage(),Toast.LENGTH_LONG).show());}
    }'''
newcatch='''        }catch(Exception e){singleStockLoading.remove(symbol);main.post(()->Toast.makeText(this,"Analiz hatası: "+e.getMessage(),Toast.LENGTH_LONG).show());}
    }'''
if oldcatch in s:s=s.replace(oldcatch,newcatch,1)
# Bound in-memory cache: avoid an ever-growing candle cache after browsing many symbols.
needle='singleStockCache.put(symbol,new java.util.ArrayList<>(data));'
repl='if(singleStockCache.size()>24)singleStockCache.clear(); singleStockCache.put(symbol,new java.util.ArrayList<>(data));'
if needle in s:s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')
