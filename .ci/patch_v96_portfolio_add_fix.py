from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='if(edit==null)holdings.add(new Holding(s,q,c));else{edit.symbol=s;edit.qty=q;edit.cost=c;} savePortfolio();showPortfolio();'
new='if(edit==null){holdings.add(new Holding(s,q,c));savePortfolio();loadPortfolio();}else{edit.symbol=s;edit.qty=q;edit.cost=c;savePortfolio();loadPortfolio();}showPortfolio();'
if old not in s: raise SystemExit('portfolio add action missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
