from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Display all stocks in their native market currency.
# BIST -> TRY, Germany -> EUR, USA -> USD. Do not convert US quotes to EUR.
pat=r'''    private String money\(double x,String symbol\)\{.*?\}\s*private String fmt\(double x\)\{return String\.format\(Locale\.US,"%\.2f",x\);\}'''
rep='''    private String money(double x,String symbol){
        String n=MarketDataService.normalizeSymbol(symbol);
        if(n.endsWith(".IS")) return String.format(Locale.US,"%.2f ₺",x);
        if(n.endsWith(".DE")) return String.format(Locale.US,"%.2f €",x);
        if(CurrencyService.isUsDollarInstrument(symbol)) return String.format(Locale.US,"%.2f $",x);
        return String.format(Locale.US,"%.2f",x);
    }
    private String fmt(double x){return String.format(Locale.US,"%.2f",x);}'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('money formatter patch failed')

# Input prices/costs are always entered in the stock's native market currency.
s=s.replace('cost.setHint("Alış fiyatı")','cost.setHint("Alış fiyatı (piyasa para birimi)")')

# Explain the convention once on the portfolio page.
needle='''        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setOnClickListener(v->refreshPortfolio()); spacer(8);'''
replacement='''        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setOnClickListener(v->refreshPortfolio()); spacer(8);
        content.addView(txt("Para birimi hisse piyasasına göre gösterilir: BIST ₺ • Almanya € • ABD $.",12,Color.GRAY));'''
if needle in s:
    s=s.replace(needle,replacement,1)

p.write_text(s,encoding='utf-8')
