from pathlib import Path
import re
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# More parallelism for portfolio refresh / scan.
s=s.replace('Executors.newFixedThreadPool(5)','Executors.newFixedThreadPool(10)')

# Current portfolio market: 0 BIST, 1 Germany, 2 USA.
anchor='private volatile boolean scanRunning=false;'
if 'portfolioMarket' not in s:
    s=s.replace(anchor,'private int portfolioMarket=0;\n    '+anchor)

# Replace portfolio page so markets are real separate views.
pat=r'    private void showPortfolio\(\) \{.*?\n    \}\n\n    private void renderHolding'
rep='''    private void showPortfolio() {
        String marketName=portfolioMarket==0?"Türkiye / BIST":portfolioMarket==1?"Almanya / Xetra-Frankfurt":"ABD / Nasdaq-NYSE";
        shell("Portföyüm • "+marketName);
        LinearLayout markets=new LinearLayout(this);
        String[] names={"🇹🇷 BIST","🇩🇪 Almanya","🇺🇸 ABD"};
        for(int i=0;i<3;i++){ final int mi=i; Button b=button(names[i],i==portfolioMarket?GREEN:NAVY2); b.setOnClickListener(v->{portfolioMarket=mi;showPortfolio();}); markets.addView(b,new LinearLayout.LayoutParams(0,-2,1)); }
        content.addView(markets); spacer(6);
        LinearLayout actions=new LinearLayout(this); Button add=button("+ Hisse Ekle",GREEN), refresh=button("Bu Portföyü Güncelle",NAVY2);
        actions.addView(add,new LinearLayout.LayoutParams(0,-2,1)); actions.addView(refresh,new LinearLayout.LayoutParams(0,-2,1)); content.addView(actions);
        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setOnClickListener(v->refreshPortfolio()); spacer(8);
        int count=0;
        for(Holding h:new ArrayList<>(holdings)) if(MarketSymbol.marketIndex(h.symbol)==portfolioMarket){renderHolding(h);count++;}
        if(count==0){ LinearLayout c=card(); c.addView(bold(marketName+" portföyü boş",19,NAVY)); c.addView(txt("Bu piyasaya ait hisseleri ayrı olarak buraya ekleyebilirsin.",14,Color.DKGRAY)); content.addView(c); }
    }

    private void renderHolding'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('showPortfolio patch failed')

# Refresh only selected market, not every market.
pat=r'    private void refreshPortfolio\(\) \{.*?\n    \}\n\n    private void portfolioDialog'
rep='''    private void refreshPortfolio() {
        List<Holding> selected=new ArrayList<>();
        for(Holding h:new ArrayList<>(holdings)) if(MarketSymbol.marketIndex(h.symbol)==portfolioMarket) selected.add(h);
        if(selected.isEmpty()){Toast.makeText(this,"Bu portföyde önce hisse ekle",Toast.LENGTH_SHORT).show();return;}
        shell("Portföy hızlı güncelleniyor"); ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal); bar.setMax(selected.size()); content.addView(bar); TextView st=txt("0/"+selected.size(),15,NAVY); content.addView(st); final int[] done={0};
        for(Holding h:selected) io.execute(()->{
            try { List<MarketDataService.Candle> d=MarketDataService.fetchDaily(h.symbol,"1mo"); ShortPulseEngine.Result sr=ShortPulseEngine.analyze(d); holdingSignals.put(h.symbol,sr); } catch(Exception ignored){}
            main.post(()->{done[0]++;bar.setProgress(done[0]);st.setText(done[0]+"/"+selected.size());if(done[0]>=selected.size())showPortfolio();});
        });
    }

    private void portfolioDialog'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('refresh patch failed')

# Portfolio entry opens already on the currently selected market.
needle='market.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,markets));'
s=s.replace(needle,needle+'\n        if(edit==null && preset==null) market.setSelection(portfolioMarket);')

# If editing, preserve its market; after save switch to saved market.
s=s.replace('savePortfolio();showPortfolio();','savePortfolio(); portfolioMarket=MarketSymbol.marketIndex(code); showPortfolio();',1)

p.write_text(s,encoding='utf-8')

b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\\s+\\d+','versionCode 45',g)
g=re.sub(r"versionName\\s+['\\\"][^'\\\"]+['\\\"]","versionName '3.10.4'",g)
b.write_text(g,encoding='utf-8')
