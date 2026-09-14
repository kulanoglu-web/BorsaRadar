from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

pat=r'''    private String money\(double x,String symbol\)\{.*?\}\s*private String fmt\(double x\)\{return String\.format\(Locale\.US,"%\.2f",x\);\}'''
rep='''    private String money(double x,String symbol){
        String n=MarketDataService.normalizeSymbol(symbol);
        if(n.endsWith(".IS")) return String.format(Locale.US,"%.2f ₺",x);
        if(n.endsWith(".DE")) return String.format(Locale.US,"%.2f €",x);
        if(CurrencyService.isUsDollarInstrument(symbol)){
            double rate=CurrencyService.usdToEur();
            if(Double.isFinite(rate)) return String.format(Locale.US,"%.2f €",x*rate);
            return "— €";
        }
        return String.format(Locale.US,"%.2f €",x);
    }
    private String fmt(double x){return String.format(Locale.US,"%.2f",x);}'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('money formatter patch failed')

old='''        loadPortfolio();
        loadRadarCache();
        showPortfolio();'''
new='''        loadPortfolio();
        loadRadarCache();
        showPortfolio();
        io.execute(()->{CurrencyService.refreshIfNeeded();main.post(this::showPortfolio);});'''
if old in s:
    s=s.replace(old,new,1)

s=s.replace('cost.setHint("Alış fiyatı")','cost.setHint("Alış fiyatı (piyasa para birimi)")')

needle='''        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setOnClickListener(v->refreshPortfolio()); spacer(8);'''
replacement='''        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setOnClickListener(v->refreshPortfolio()); spacer(8);
        content.addView(txt("ABD hisseleri güncel USD/EUR kuru ile € olarak gösterilir.",12,Color.GRAY));'''
if needle in s:
    s=s.replace(needle,replacement,1)

p.write_text(s,encoding='utf-8')
