from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v108: explicit portfolio profile switcher. Save current bucket, change market, load target bucket, repaint.
marker='    private void showPortfolio()'
helper='''    private LinearLayout portfolioMarketSelector(){
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
        String[] labels={"BIST","ALMANYA","ABD"}; final int current=primaryMarket();
        for(int i=0;i<3;i++){final int target=i;Button b=button(labels[i],current==i?GREEN:NAVY2);
            b.setOnClickListener(v->{
                if(target==primaryMarket()){showPortfolio();return;}
                savePortfolio();
                getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("primary_market",target).putInt("active_profile",target).commit();
                loadPortfolio();holdingSignals.clear();holdingContexts.clear();showPortfolio();
            });
            row.addView(b,new LinearLayout.LayoutParams(0,-2,1));
        }
        return row;
    }

'''
if 'private LinearLayout portfolioMarketSelector()' not in s:
    if marker not in s: raise SystemExit('showPortfolio missing')
    s=s.replace(marker,helper+marker,1)
# Add selector directly below portfolio shell so profile switching is always visible.
needle='''    private void showPortfolio() {
        shell("Portföyüm");'''
if needle in s and 'content.addView(portfolioMarketSelector())' not in s[s.find(needle):s.find(needle)+300]:
    s=s.replace(needle,'''    private void showPortfolio() {
        shell("Portföyüm • "+(primaryMarket()==0?"BIST":primaryMarket()==1?"ALMANYA":"ABD"));
        content.addView(portfolioMarketSelector());spacer(8);''',1)
# Patched/localized versions may no longer have exact original shell text.
if 'content.addView(portfolioMarketSelector())' not in s:
    a=s.find('private void showPortfolio()')
    if a>=0:
        brace=s.find('{',a)+1
        s=s[:brace]+'\n        content.addView(portfolioMarketSelector());spacer(8);'+s[brace:]
p.write_text(s,encoding='utf-8')
