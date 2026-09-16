from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v111: startup must use the known-stable v107 portfolio screen. Do not construct the new
# market selector from showPortfolio(), because onCreate() calls showPortfolio immediately.
# Keep switching code available for later UI reintroduction after startup is proven stable.
s=s.replace('''        shell("Portföyüm • "+(primaryMarket()==0?"BIST":primaryMarket()==1?"ALMANYA":"ABD"));
        content.addView(portfolioMarketSelector());spacer(8);''','''        shell("Portföyüm");''',1)
s=s.replace('''        content.addView(portfolioMarketSelector());spacer(8);''','',1)
# Guard startup persistence/cache reads individually so damaged old app data cannot terminate Activity creation.
old='''        loadPortfolio();
        loadRadarCache();
        showPortfolio();'''
new='''        try{loadPortfolio();}catch(Throwable t){holdings.clear();}
        try{loadRadarCache();}catch(Throwable ignored){}
        try{showPortfolio();}catch(Throwable t){
            try{holdings.clear();shell("BorsaRadar");Toast.makeText(this,"Başlangıç verileri sıfırlandı",Toast.LENGTH_LONG).show();}
            catch(Throwable ignored){}
        }'''
if old in s:s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
