from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
s=s.replace('MarketDataService.fetchDaily(h.symbol, "6mo")','MarketDataService.fetchDaily(h.symbol, "3mo")')
s=s.replace('MarketDataService.fetchDaily(sym, "1y")','MarketDataService.fetchDaily(sym, "3mo")')
s=s.replace('MarketDataService.fetchDaily(symbol, "1y")','MarketDataService.fetchDaily(symbol, "3mo")')
s=s.replace('"1 yıllık günlük veri indiriliyor ve strateji geriye dönük çalıştırılıyor..."','"Güncel teknik veri alınıyor; grafik son 10 işlem gününü gösterir..."')
s=s.replace('"1Y Backtest"','"Grafik / Analiz"')
s=s.replace('"Detaylı backtest yenile"','"Grafik / Analiz"')
s=s.replace('"1Y backtest: " + r.bt.summary','"BorsaRadar yöntem sonucu: " + MethodEngine.analyze(r.s).summary')
s=s.replace('shell(symbol + " Backtest")','shell(symbol + " Analiz")')
s=s.replace('shell(symbol + " Backtest Sonucu")','shell(symbol + " Analiz Sonucu")')
s=s.replace('"Teknik sinyal: " + s.signal + " • Teknik skor: " + s.score + " • Ölçek: -14…+15"','MethodEngine.analyze(s).label + " • " + MethodEngine.analyze(s).summary')
s=s.replace('"Mantık: güçlü AL/ERKEN sinyaliyle giriş; ATR + EMA50 tabanlı ilk stop; ATR trailing ve trend/MACD bozulmasında çıkış."','"Metodlar: BR-Pulse + FlowBreak + TrendGuard + BR-KarKoru. BR-KarKoru açık pozisyonda zirveden geri çekilme, ATR, momentum ve hacim baskısıyla stopu yükseltir."')

s=re.sub(r'    private String decision\(IndicatorEngine\.Snapshot s\) \{.*?\n    \}', '''    private String decision(IndicatorEngine.Snapshot s) {
        MethodEngine.Result m = MethodEngine.analyze(s);
        return m.label + " • %" + String.format(Locale.US, "%.0f", m.percent);
    }''', s, count=1, flags=re.S)
s=re.sub(r'    private int decisionColor\(IndicatorEngine\.Snapshot s\) \{.*?\n    \}', '''    private int decisionColor(IndicatorEngine.Snapshot s) {
        MethodEngine.Result m = MethodEngine.analyze(s);
        if (m.label.contains("AL")) return GREEN;
        if (m.label.contains("SAT") || m.label.contains("RİSK") || m.label.contains("AZALT")) return RED;
        return Color.rgb(225, 145, 0);
    }''', s, count=1, flags=re.S)

s=s.replace('return "Neye göre: " + android.text.TextUtils.join(" • ", why) + ".";', '''MethodEngine.Result m = MethodEngine.analyze(s);
        return "Neye göre: " + android.text.TextUtils.join(" • ", why) + ". • " + m.summary
                + " • Bu yüzde kazanç garantisi değil, indikatör/metod uyum gücüdür.";''')
s=s.replace('return "İndikatör uzlaşması: " + buy + " AL • " + neutral + " NÖTR • " + sell + " SAT";', '''MethodEngine.Result m = MethodEngine.analyze(s);
        return "Analiz %" + String.format(Locale.US, "%.0f", m.percent)
                + " • " + buy + " AL • " + neutral + " NÖTR • " + sell + " SAT";''')
s=s.replace('" • skor " + r.s.score + "/15"','" • analiz %" + String.format(Locale.US, "%.0f", MethodEngine.analyze(r.s).percent)')
s=s.replace('"Fiyat " + money(r.s.close) + " • " + r.s.reason','"Fiyat " + money(r.s.close) + " • " + MethodEngine.analyze(r.s).summary')
s=s.replace('if (r.s.score >= 5 && !r.s.trap) shortTerm.add(r);','if (MethodEngine.analyze(r.s).percent >= 62 && !r.s.trap) shortTerm.add(r);')
s=s.replace('if (r.s.trendUp && r.s.cmf20 > 0 && !r.s.trap) longTerm.add(r);','if (MethodEngine.analyze(r.s).percent >= 68 && r.s.trendUp && !r.s.trap) longTerm.add(r);')
s=s.replace('if (dividendWatch.contains(r.symbol) && r.s.score >= 2 && !r.s.trap) dividend.add(r);','if (dividendWatch.contains(r.symbol) && MethodEngine.analyze(r.s).percent >= 52 && !r.s.trap) dividend.add(r);')
s=s.replace('" • skor " + r.s.score + " (-14…+15)"','" • analiz %" + String.format(Locale.US, "%.0f", MethodEngine.analyze(r.s).percent)')
s=s.replace('new PriceChartView(this, data)', 'new PriceChartView(this, data, "1 GÜN • SON 10 İŞLEM GÜNÜ")')

# Portfolio: show BR-KarKoru for an owned position whenever its market data is loaded.
s=s.replace('String d = decision(s);', 'String d = decision(s);\n                    ProfitGuardEngine.Result pg = ProfitGuardEngine.analyze(data, h.avg);')
s=s.replace('explainDecision(s) + "\\n" + indicatorConsensus(s)', 'explainDecision(s) + "\\n" + indicatorConsensus(s) + "\\n" + pg.action + " • " + pg.reason')

p.write_text(s, encoding='utf-8')
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+', 'versionCode 32', g)
g=re.sub(r"versionName\s+'[^']+'", "versionName '3.2.0'", g)
b.write_text(g, encoding='utf-8')
