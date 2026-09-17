from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MarketDataService.java')
s=p.read_text(encoding='utf-8')
old='''            String u="https://"+host+"/v8/finance/chart/"+symbol+"?range="+range+"&interval="+interval+"&includePrePost=false&events=div%2Csplits";'''
new='''            String encodedSymbol=URLEncoder.encode(symbol, "UTF-8").replace("+", "%20");
            String u="https://"+host+"/v8/finance/chart/"+encodedSymbol+"?range="+range+"&interval="+interval+"&includePrePost=false&events=div%2Csplits";'''
if old not in s: raise SystemExit('Yahoo URL anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('v146 encoded Yahoo symbol path:', 'encodedSymbol' in s)
