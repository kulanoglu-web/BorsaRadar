from pathlib import Path
import re

root=Path('build-v23/BorsaRadar')
pkg=root/'app/src/main/java/com/kulanoglu/borsaradar'

# Restore MarketDataService API expected by v2.0 screens, while keeping returned live history short.
p=pkg/'MarketDataService.java'
s=p.read_text(encoding='utf-8')
# Add FetchResult after Candle class.
marker='''    public static final class Candle {\n        public final long time;\n        public final double open, high, low, close, volume;\n        public Candle(long time,double open,double high,double low,double close,double volume){\n            this.time=time; this.open=open; this.high=high; this.low=low; this.close=close; this.volume=volume;\n        }\n    }\n'''
add=marker+'''\n    public static final class FetchResult {\n        public final List<Candle> candles;\n        public final String source;\n        public FetchResult(List<Candle> candles,String source){ this.candles=candles; this.source=source; }\n    }\n'''
s=s.replace(marker,add)
# Make fetchDaily use the detailed wrapper, then replace old implementation block.
start=s.index('    public static List<Candle> fetchDaily(')
end=s.index('    private static void throttle()', start)
api='''    public static List<Candle> fetchDaily(String bistSymbol,String ignoredRange) throws Exception {\n        return fetchDailyDetailed(bistSymbol,ignoredRange).candles;\n    }\n\n    public static FetchResult fetchDailyDetailed(String bistSymbol,String ignoredRange) throws Exception {\n        return fetchDetailed(bistSymbol,"1mo","1d",8);\n    }\n\n    public static FetchResult fetchDetailed(String bistSymbol,String range,String interval,int minCandles) throws Exception {\n        String raw=bistSymbol==null?"":bistSymbol.trim().toUpperCase();\n        if(raw.isEmpty()) throw new Exception("Hisse kodu boş");\n        String symbol=raw.endsWith(".IS")?raw:raw+".IS";\n        String safeInt=("15m".equals(interval)||"30m".equals(interval)||"1h".equals(interval)||"1d".equals(interval)||"1wk".equals(interval))?interval:"1d";\n        String safeRange;\n        if("1d".equals(safeInt)||"1wk".equals(safeInt)) safeRange="1mo";\n        else safeRange=("5d".equals(range)||"1mo".equals(range))?range:"1mo";\n        Exception last=null;\n        String[] hosts={"query1.finance.yahoo.com","query2.finance.yahoo.com"};\n        for(int attempt=0;attempt<4;attempt++){\n            String url="https://"+hosts[attempt%hosts.length]+"/v8/finance/chart/"+symbol+\n                    "?range="+safeRange+"&interval="+safeInt+"&includePrePost=false&events=div%2Csplits";\n            try{\n                throttle();\n                List<Candle> all=fetch(url);\n                int keep=("1d".equals(safeInt)||"1wk".equals(safeInt))?12:Math.min(160,all.size());\n                int from=Math.max(0,all.size()-keep);\n                List<Candle> out=new ArrayList<>(all.subList(from,all.size()));\n                if(out.size()<Math.min(8,minCandles)) throw new Exception("Yetersiz veri: "+out.size());\n                return new FetchResult(out,"Yahoo • 2W hafif mod");\n            }catch(Exception e){\n                last=e;\n                try{Thread.sleep(350L*(attempt+1));}catch(InterruptedException x){Thread.currentThread().interrupt();throw x;}\n            }\n        }\n        throw last==null?new Exception("Veri alınamadı"):last;\n    }\n\n'''
s=s[:start]+api+s[end:]
p.write_text(s,encoding='utf-8')

# Add compatibility fields required by adaptive/risk engines to the new short-horizon snapshot.
p=pkg/'IndicatorEngine.java'
s=p.read_text(encoding='utf-8')
s=s.replace('public double cci20, stochastic14, adx14;','public double cci20, stochastic14, adx14;\n        public double stochK14, roc10, obvSlope10, flowPulse;')
s=s.replace('s.stochastic14=stochastic(x,7,end);','''s.stochastic14=stochastic(x,7,end);\n        s.stochK14=s.stochastic14;''')
s=s.replace('s.volumePressure20=volumePressure(x,8,end);','''s.volumePressure20=volumePressure(x,8,end);\n        int rocBase=Math.max(0,end-5);\n        double baseClose=x.get(rocBase).close;\n        s.roc10=baseClose<=0?0:100.0*(s.close/baseClose-1.0);\n        s.obvSlope10=s.volumePressure20;\n        s.flowPulse=2.2*s.cmf20 + 0.12*s.obvSlope10 + 0.10*Math.max(-1.0,Math.min(2.0,s.relVolume-1.0));''')
p.write_text(s,encoding='utf-8')

# Final UI wording: no phone-side multi-year testing; show only short-horizon method and chart/detail.
p=pkg/'MainActivity.java'
m=p.read_text(encoding='utf-8')
m=m.replace('1Y backtest:', 'Geçmiş test:')
m=m.replace('Detaylı backtest yenile', 'Grafik / Detay')
m=m.replace('1 yıllık günlük veri indiriliyor ve strateji geriye dönük çalıştırılıyor...', 'Son 1–2 haftalık görünüm ve BorsaPulse sinyali hazırlanıyor...')
m=m.replace('1 yıllık', 'kısa dönem')
m=m.replace('2y','1mo').replace('1y','1mo').replace('6mo','1mo')
m=m.replace('Skor: EMA20/50 + RSI14 + MACD + RVOL + CMF + Bollinger + CCI + Stokastik + ADX + BRTV + BRM + BRH + breakout/trap + ATR', 'BorsaPulse-2W: hızlı/yavaş trend + RSI5 + hacim + para akışı + momentum + breakout/tuzak + ATR')
m=m.replace('Günlük Yahoo Finance verisini anahtarsız çeker; veri gecikmeli olabilir.', 'Telefon tarafında yalnızca kısa veri kullanır; veri gecikmeli olabilir.')
m=m.replace('yalnızca en güçlü 30 teknik aday', 'yalnızca en güçlü 30 kısa dönem aday')
# Remove visible historical backtest summary from radar cards and make detail action open the existing detail screen without implying 1Y.
m=m.replace('card.addView(title("Geçmiş test: " + r.bt.summary, 13));','')
m=m.replace('shell(symbol + " Backtest")','shell(symbol + " • Detay")')
m=m.replace('shell(symbol + " Backtest Sonucu")','shell(symbol + " • 2 Haftalık Detay")')
m=m.replace('content.addView(title(r.summary, 17));','content.addView(title("BorsaPulse-2W canlı değerlendirme • " + s.reason, 17));')
m=m.replace('Mantık: güçlü AL/ERKEN sinyaliyle giriş; ATR + EMA50 tabanlı ilk stop; ATR trailing ve trend/MACD bozulmasında çıkış.', 'Mantık: son 1–2 haftada trend, momentum, para akışı, hacim ve tuzak filtresi birlikte değerlendirilir.')
# Make navigation visually closer to a trading terminal: navy header, green radar, amber plans.
m=m.replace('p.setBackgroundColor(RED);\n        r.setBackgroundColor(RED);\n        a.setBackgroundColor(RED);','p.setBackgroundColor(NAVY);\n        r.setBackgroundColor(GREEN);\n        a.setBackgroundColor(Color.rgb(198, 132, 0));')
p.write_text(m,encoding='utf-8')

print('v2.3 compatibility fix complete')
