from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v114: BIST/DE/US/ALL must never display another market's cached radar results.
# Switching market is display-only; explicit scan owns/replaces only that market's snapshot.
field='    private String shortScanMode="1S";'
if 'radarResultMarket' not in s:
    s=s.replace(field,field+'\n    private int radarResultMarket=-1;\n    private final java.util.HashMap<Integer,java.util.ArrayList<RadarResult>> radarResultsByMarket=new java.util.HashMap<>();',1)
marker='    private String radarMarketLabel()'
helper='''    private void saveRadarMarketSnapshot(int market){
        try{if(radarResults!=null)radarResultsByMarket.put(market,new java.util.ArrayList<>(radarResults));}catch(Throwable ignored){}
    }
    private void restoreRadarMarketSnapshot(int market){
        try{radarResults.clear();java.util.ArrayList<RadarResult> a=radarResultsByMarket.get(market);if(a!=null)radarResults.addAll(a);radarResultMarket=market;}catch(Throwable ignored){}
    }
    private void selectRadarMarket(int pick,boolean hourly){
        int old=radarMarketChoice;saveRadarMarketSnapshot(old);radarMarketChoice=pick;restoreRadarMarketSnapshot(pick);
        if(hourly)showHourlyRadar();else showRadar();
    }

'''
if marker in s and 'private void selectRadarMarket' not in s:s=s.replace(marker,helper+marker,1)
s=s.replace('radarMarketChoice=pick;if(hourly)showHourlyRadar();else showRadar();','selectRadarMarket(pick,hourly);')
s=s.replace('radarMarketChoice=pick;showRadar();','selectRadarMarket(pick,false);')
s=s.replace('radarMarketChoice=pick;showHourlyRadar();','selectRadarMarket(pick,true);')
a=s.find('private void scanRadar()')
if a>=0:
    brace=s.find('{',a)+1
    if 'radarResultMarket=radarMarketChoice' not in s[brace:brace+220]:s=s[:brace]+'\n        radarResultMarket=radarMarketChoice;radarResultsByMarket.remove(radarMarketChoice);'+s[brace:]
# Do not rewrite the if-condition with an extra brace: earlier versions produced `else without if`.
# Save the market snapshot immediately before the existing completion refresh call instead.
needle='main.post(this::refreshRadarUiIfVisible);'
if needle in s and 'saveRadarMarketSnapshot(radarMarketChoice);'+needle not in s:
    s=s.replace(needle,'saveRadarMarketSnapshot(radarMarketChoice);'+needle,1)
s=s.replace('Türkiye / BIST • öncelikli tarama','"+radarMarketLabel()+" • öncelikli tarama')
s=s.replace('Borsa İstanbul evreni taranır.','Seçili piyasa evreni yalnız Tara/Ara düğmesine basınca taranır.')
p.write_text(s,encoding='utf-8')
