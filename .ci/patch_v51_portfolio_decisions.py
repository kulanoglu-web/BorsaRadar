from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Idempotent: if already applied, keep it.
if 'PortfolioRiskEngine.evaluate(h.cost,h.qty,s,cx)' not in s:
    marker='CatalystContextEngine.Result cx=holdingContexts.get(h.symbol); if(cx!=null)c.addView(contextBanner(cx));'
    if marker in s:
        inject=marker+'''\n            PortfolioRiskEngine.Result pr=PortfolioRiskEngine.evaluate(h.cost,h.qty,s,cx);\n            String act=PositionActionLabelEngine.label(s,cx,h.cost);\n            int ac=act.contains("AZALT")?RED:act.contains("BEKLE")?AMBER:GREEN;\n            c.addView(bold(act+"  •  Risk "+fmt(pr.riskScore)+"/100",14,ac));\n            c.addView(txt(pr.note,12,Color.DKGRAY));'''
        s=s.replace(marker,inject,1)
    else:
        # Older patches may reflow whitespace; inject before the first portfolio horizon line.
        pat=r'(\s+c\.addView\(txt\("Hedef süre: "\+s\.horizonText.*?NAVY2\)\);)'
        inject='''\n            CatalystContextEngine.Result cx=holdingContexts.get(h.symbol);\n            PortfolioRiskEngine.Result pr=PortfolioRiskEngine.evaluate(h.cost,h.qty,s,cx);\n            String act=PositionActionLabelEngine.label(s,cx,h.cost);\n            int ac=act.contains("AZALT")?RED:act.contains("BEKLE")?AMBER:GREEN;\n            c.addView(bold(act+"  •  Risk "+fmt(pr.riskScore)+"/100",14,ac));\n            c.addView(txt(pr.note,12,Color.DKGRAY));'''
        s,n=re.subn(pat,inject+r'\1',s,count=1,flags=re.S)
        if n!=1:
            print('portfolio decision UI marker not found; leaving build intact')

p.write_text(s,encoding='utf-8')
