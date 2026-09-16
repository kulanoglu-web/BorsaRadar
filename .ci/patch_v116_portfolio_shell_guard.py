from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v116: crash log shows showPortfolio() calling content.addView while content is null
# after exchange/profile switching. Make showPortfolio self-contained: shell must exist
# before any selector/action addView, regardless of which legacy switch path invoked it.
a=s.find('    private void showPortfolio()')
if a<0: raise SystemExit('showPortfolio missing')
b=s.find('\n    private void ',a+10)
if b<0:b=len(s)
block=s[a:b]
brace=block.find('{')+1
# Remove any selector/shell lines injected before a valid shell and rebuild deterministic prologue.
lines=block[brace:].splitlines()
clean=[]
for line in lines:
    if 'content.addView(portfolioMarketSelector())' in line: continue
    if 'shell("Portföyüm' in line: continue
    clean.append(line)
prologue='''
        shell("Portföyüm • "+(primaryMarket()==0?"BIST":primaryMarket()==1?"ALMANYA":"ABD"));
        if(content==null){Toast.makeText(this,"Portföy ekranı hazırlanamadı",Toast.LENGTH_LONG).show();return;}
        content.addView(portfolioMarketSelector());spacer(8);'''
block=block[:brace]+prologue+'\n'.join(clean)
s=s[:a]+block+s[b:]
# Legacy exchange profile switches may call showPortfolio synchronously from dialog callbacks.
# Route all direct calls in switchExchangeProfile through the main queue after preferences/load settle.
a=s.find('private void switchExchangeProfile')
if a>=0:
    b=s.find('\n    private void ',a+10)
    if b<0:b=len(s)
    q=s[a:b]
    q=q.replace('showPortfolio();','main.post(this::showPortfolio);')
    s=s[:a]+q+s[b:]
p.write_text(s,encoding='utf-8')
