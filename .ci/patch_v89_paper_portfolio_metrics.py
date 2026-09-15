from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v89: richer paper position storage and performance summary.
old='''    private void addPaperPosition(String symbol,double price,int qty){
        if(!Double.isFinite(price)||price<=0||qty<=0) return;
        getSharedPreferences("paper_portfolio",MODE_PRIVATE).edit().putString(symbol,price+"|"+qty+"|"+System.currentTimeMillis()).apply();
        Toast.makeText(this,"Fake portföye eklendi: "+symbol,Toast.LENGTH_SHORT).show();
    }'''
new='''    private void addPaperPosition(String symbol,double price,int qty){
        if(!Double.isFinite(price)||price<=0||qty<=0) return;
        getSharedPreferences("paper_portfolio",MODE_PRIVATE).edit().putString(symbol,price+"|"+qty+"|"+System.currentTimeMillis()).apply();
        Toast.makeText(this,"Fake portföye eklendi: "+symbol+" • "+qty+" adet @ "+money(price,symbol),Toast.LENGTH_SHORT).show();
    }
    private String paperPositionSummary(String symbol,double now){
        String raw=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getString(symbol,null); if(raw==null) return "Henüz Fake pozisyon yok";
        try{String[] z=raw.split("\\\\|"); double buy=Double.parseDouble(z[0]); int qty=Integer.parseInt(z[1]); long at=Long.parseLong(z[2]);
            double pnl=(now-buy)*qty, pct=buy>0?(now/buy-1.0)*100.0:0; long days=Math.max(0,(System.currentTimeMillis()-at)/86400000L);
            return "Fake: "+qty+" adet • Alış "+money(buy,symbol)+" • Güncel "+money(now,symbol)+" • K/Z "+money(pnl,symbol)+" ("+(pct>=0?"+":"")+fmt(pct)+"%) • "+days+" gün";
        }catch(Exception e){return "Fake portföy kaydı okunamadı";}
    }'''
if old not in s: raise SystemExit('paper helper missing')
s=s.replace(old,new,1)
needle='''        pfBody.addView(txt("Gerçek portföy: gerçekten aldığın hisseler • Fake portföy: sinyali para riske etmeden test et.",12,Color.GRAY));'''
repl='''        pfBody.addView(txt("Gerçek portföy: gerçekten aldığın hisseler • Fake portföy: sinyali para riske etmeden test et.",12,Color.GRAY));
        double paperNow=(chart!=null&&!chart.isEmpty())?chart.get(chart.size()-1).close:r.price;
        pfBody.addView(bold(paperPositionSummary(symbol,paperNow),13,Color.WHITE));'''
if needle not in s: raise SystemExit('paper body missing')
s=s.replace(needle,repl,1)
# avoid redeclaring paper price later
s=s.replace('double paperPrice=(chart!=null&&!chart.isEmpty())?chart.get(chart.size()-1).close:r.price;','double paperPrice=paperNow;',1)
p.write_text(s,encoding='utf-8')
