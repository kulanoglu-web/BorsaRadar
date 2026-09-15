from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v87: Never replace a known US stock price with a bare "— €" just because FX is still loading.
old='''        if(CurrencyService.isUsDollarInstrument(symbol)){
            double rate=CurrencyService.usdToEur();
            if(Double.isFinite(rate)) return String.format(Locale.US,"%.2f €",x*rate);
            return "— €";
        }'''
new='''        if(CurrencyService.isUsDollarInstrument(symbol)){
            double rate=CurrencyService.usdToEur();
            if(Double.isFinite(rate)&&rate>0) return String.format(Locale.US,"%.2f €",x*rate);
            return Double.isFinite(x)&&x>0 ? String.format(Locale.US,"%.2f $",x) : "Fiyat bekleniyor";
        }'''
if old not in s: raise SystemExit('money US branch missing')
s=s.replace(old,new,1)
# Before rendering a US single-stock result, refresh FX off the UI thread and repaint once available.
needle='final List<MarketDataService.Candle> data=d;'
if needle in s:
    s=s.replace(needle,'''final List<MarketDataService.Candle> data=d;
            if(CurrencyService.isUsDollarInstrument(symbol)&&!CurrencyService.hasRate()) CurrencyService.refreshIfNeeded();''',1)
# Same protection for deep result: if FX was unavailable during first paint, the visible native USD value remains meaningful.
if 'return "— €";' in s: raise SystemExit('bare euro placeholder still present')
p.write_text(s,encoding='utf-8')
