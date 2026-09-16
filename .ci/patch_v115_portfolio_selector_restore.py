from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v115: v111 removed the portfolio selector from showPortfolio to recover startup.
# Restore only the UI hook after all safe-switch/startup patches have run.
needle='''    private void showPortfolio() {
        shell("Portföyüm");'''
replacement='''    private void showPortfolio() {
        shell("Portföyüm • "+(primaryMarket()==0?"BIST":primaryMarket()==1?"ALMANYA":"ABD"));
        content.addView(portfolioMarketSelector());spacer(8);'''
if needle in s:
    s=s.replace(needle,replacement,1)
else:
    a=s.find('private void showPortfolio()')
    if a<0: raise SystemExit('showPortfolio missing')
    b=s.find('{',a)+1
    block=s[a:s.find('\n    private void ',b) if s.find('\n    private void ',b)>=0 else len(s)]
    if 'portfolioMarketSelector()' not in block:
        s=s[:b]+'\n        content.addView(portfolioMarketSelector());spacer(8);'+s[b:]
p.write_text(s,encoding='utf-8')
