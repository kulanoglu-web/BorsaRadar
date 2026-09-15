from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='if(edit==null)holdings.add(new Holding(s,q,c));else{edit.symbol=s;edit.qty=q;edit.cost=c;} savePortfolio();showPortfolio();'
new='if(edit==null){holdings.add(new Holding(s,q,c));savePortfolio();loadPortfolio();}else{edit.symbol=s;edit.qty=q;edit.cost=c;savePortfolio();loadPortfolio();}showPortfolio();'
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    # v95 may already have inserted loadPortfolio between save and display.
    old2='if(edit==null)holdings.add(new Holding(s,q,c));else{edit.symbol=s;edit.qty=q;edit.cost=c;} savePortfolio(); loadPortfolio(); showPortfolio();'
    if old2 in s:s=s.replace(old2,new,1)
    else:print('portfolio add action already transformed; keeping current implementation')
p.write_text(s,encoding='utf-8')
