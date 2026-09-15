from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v90: P/L in stock detail for both real and fake positions; total P/L visual on portfolio.
# Add a compact reusable P/L bar view without external chart dependency.
anchor='    private LinearLayout collapsible(String title, android.view.View body, boolean open){'
helper='''    private android.view.View pnlBar(final double pct){
        android.widget.ProgressBar b=new android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal); b.setMax(200); int v=(int)Math.max(0,Math.min(200,100+pct*2)); b.setProgress(v); b.setMinimumHeight(dp(12)); return b;
    }
    private String realPositionSummary(String symbol,double now){
        for(Holding h:holdings) if(h.symbol.equals(symbol)){
            double pnl=(now-h.cost)*h.qty, pct=h.cost>0?(now/h.cost-1)*100:0;
            return "Gerçek: "+h.qty+" adet • Maliyet "+money(h.cost,symbol)+" • Güncel "+money(now,symbol)+" • K/Z "+money(pnl,symbol)+" ("+(pct>=0?"+":"")+fmt(pct)+"%)";
        }
        return "Gerçek portföyde yok";
    }
'''
if anchor not in s: raise SystemExit('v88 anchor missing')
s=s.replace(anchor,helper+anchor,1)
# Detail portfolio section: show real and fake P/L together with visual bars.
needle='''        pfBody.addView(bold(paperPositionSummary(symbol,paperNow),13,Color.WHITE));'''
repl='''        String realSum=realPositionSummary(symbol,paperNow); String fakeSum=paperPositionSummary(symbol,paperNow);
        double realPct=0,fakePct=0;
        for(Holding hh:holdings) if(hh.symbol.equals(symbol)&&hh.cost>0) realPct=(paperNow/hh.cost-1)*100.0;
        try{String rr=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getString(symbol,null); if(rr!=null){double bb=Double.parseDouble(rr.split("\\\\|")[0]); if(bb>0)fakePct=(paperNow/bb-1)*100.0;}}catch(Exception ignored){}
        pfBody.addView(bold(realSum,13,realPct>=0?GREEN:RED)); pfBody.addView(pnlBar(realPct));
        pfBody.addView(bold(fakeSum,13,fakePct>=0?GREEN:RED)); pfBody.addView(pnlBar(fakePct));'''
if needle not in s: raise SystemExit('v89 detail summary missing')
s=s.replace(needle,repl,1)
# Portfolio screen: inject total real P/L after shell if known holdingSignals are available.
needle2='''        shell("Portföy");'''
if needle2 in s:
    repl2='''        shell("Portföy");
        double invested=0,current=0; int priced=0;
        for(Holding hh:holdings){ ShortPulseEngine.Result ss=holdingSignals.get(hh.symbol); if(ss!=null&&ss.price>0){invested+=hh.cost*hh.qty; current+=ss.price*hh.qty; priced++;} }
        if(priced>0&&invested>0){ double totalPnl=current-invested,totalPct=(current/invested-1)*100.0; LinearLayout total=card(); total.addView(bold("Gerçek Portföy • Toplam K/Z",18,Color.WHITE)); total.addView(bold(money(totalPnl)+"  •  "+(totalPct>=0?"+":"")+fmt(totalPct)+"%",24,totalPct>=0?GREEN:RED)); total.addView(txt("Maliyet "+money(invested)+" • Güncel değer "+money(current)+" • fiyatlanan "+priced+"/"+holdings.size(),12,Color.GRAY)); total.addView(pnlBar(totalPct)); content.addView(total); spacer(8); }'''
    s=s.replace(needle2,repl2,1)
# Per holding card: color current P/L line when the known portfolio signal is rendered.
marker='''            PortfolioRiskEngine.Result pr=PortfolioRiskEngine.evaluate(h.cost,h.qty,s,cx);'''
if marker in s:
    s=s.replace(marker,'''            double hpnl=(s.price-h.cost)*h.qty, hpct=h.cost>0?(s.price/h.cost-1)*100.0:0;
            c.addView(bold("K/Z "+money(hpnl,h.symbol)+" • "+(hpct>=0?"+":"")+fmt(hpct)+"%",16,hpct>=0?GREEN:RED)); c.addView(pnlBar(hpct));
            PortfolioRiskEngine.Result pr=PortfolioRiskEngine.evaluate(h.cost,h.qty,s,cx);''',1)
p.write_text(s,encoding='utf-8')
