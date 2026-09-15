from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
anchor='    private LinearLayout collapsible(String title, android.view.View body, boolean open){'
helper='''    private android.view.View pnlBar(final double rawPct){
        double pct=Double.isFinite(rawPct)?rawPct:0.0;
        android.widget.ProgressBar b=new android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        b.setMax(200); double clipped=Math.max(-50.0,Math.min(50.0,pct)); b.setProgress((int)(100.0+clipped*2.0)); b.setMinimumHeight(dp(12)); return b;
    }
    private String realPositionSummary(String symbol,double now){
        if(!Double.isFinite(now)||now<=0) return "Gerçek: güncel fiyat bekleniyor";
        for(Holding h:holdings) if(h.symbol.equals(symbol)){
            double pnl=(now-h.cost)*h.qty, pct=h.cost>0?(now/h.cost-1)*100:0;
            return "Gerçek: "+h.qty+" adet • Maliyet "+money(h.cost,symbol)+" • Güncel "+money(now,symbol)+" • K/Z "+money(pnl,symbol)+" ("+(pct>=0?"+":"")+fmt(pct)+"%)";
        }
        return "Gerçek portföyde yok";
    }
'''
if anchor not in s: raise SystemExit('v90 collapsible anchor missing')
s=s.replace(anchor,helper+anchor,1)
# Replace v89's one-line fake summary by locating the call, independent of whitespace.
pos=s.find('pfBody.addView(bold(paperPositionSummary(symbol,paperNow)')
if pos<0: raise SystemExit('v90 paper summary call missing')
end=s.find(';',pos)
if end<0: raise SystemExit('v90 paper summary terminator missing')
repl='''String realSum=realPositionSummary(symbol,paperNow); String fakeSum=paperPositionSummary(symbol,paperNow);
        double realPct=0,fakePct=0;
        if(Double.isFinite(paperNow)&&paperNow>0){
            for(Holding hh:holdings) if(hh.symbol.equals(symbol)&&hh.cost>0) realPct=(paperNow/hh.cost-1)*100.0;
            try{String rr=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getString(symbol,null); if(rr!=null){String[] pp=rr.split("\\\\|"); if(pp.length>0){double bb=Double.parseDouble(pp[0]); if(Double.isFinite(bb)&&bb>0)fakePct=(paperNow/bb-1)*100.0;}}}catch(Exception ignored){}
        }
        pfBody.addView(bold(realSum,13,realPct>=0?GREEN:RED)); pfBody.addView(pnlBar(realPct));
        pfBody.addView(bold(fakeSum,13,fakePct>=0?GREEN:RED)); pfBody.addView(pnlBar(fakePct))'''
s=s[:pos]+repl+s[end:]
marker='PortfolioRiskEngine.Result pr=PortfolioRiskEngine.evaluate(h.cost,h.qty,s,cx);'
if marker in s:
    s=s.replace(marker,'''if(s!=null&&Double.isFinite(s.price)&&s.price>0){ double hpnl=(s.price-h.cost)*h.qty, hpct=h.cost>0?(s.price/h.cost-1)*100.0:0; c.addView(bold("K/Z "+money(hpnl,h.symbol)+" • "+(hpct>=0?"+":"")+fmt(hpct)+"%",16,hpct>=0?GREEN:RED)); c.addView(pnlBar(hpct)); }
            '''+marker,1)
p.write_text(s,encoding='utf-8')
