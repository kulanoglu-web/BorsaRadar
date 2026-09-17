from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MarketDataService.java')
s=p.read_text(encoding='utf-8')
if 'String encodedSymbol=URLEncoder.encode(symbol' in s:
    print('v146 encoded Yahoo symbol path: already applied')
else:
    old='''            String u="https://"+host+"/v8/finance/chart/"+symbol+"?range="+range+"&interval="+interval+"&includePrePost=false&events=div%2Csplits";'''
    new='''            String encodedSymbol=URLEncoder.encode(symbol, StandardCharsets.UTF_8.name()).replace("+", "%20");
            String u="https://"+host+"/v8/finance/chart/"+encodedSymbol+"?range="+range+"&interval="+interval+"&includePrePost=false&events=div%2Csplits";'''
    if old not in s: raise SystemExit('Yahoo URL anchor missing')
    s=s.replace(old,new,1)
    p.write_text(s,encoding='utf-8')
    print('v146 encoded Yahoo symbol path: applied')
