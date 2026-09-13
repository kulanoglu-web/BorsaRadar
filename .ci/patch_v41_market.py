from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MarketDataService.java')
s=p.read_text(encoding='utf-8')
s=s.replace('String symbol=bistSymbol.endsWith(".IS")?bistSymbol:bistSymbol+".IS"; Exception last=null;', 'String symbol=MarketSymbol.yahoo(bistSymbol); Exception last=null;')
p.write_text(s,encoding='utf-8')
