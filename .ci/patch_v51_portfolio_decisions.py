from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='''            CatalystContextEngine.Result cx=holdingContexts.get(h.symbol); if(cx!=null)c.addView(contextBanner(cx));
            c.addView(txt("Hedef süre: "+s.horizonText+"  •  Güven %"+(int)s.confidence+"  •  Stop ref. "+money(s.stopReference,h.symbol),13,NAVY2));'''
new='''            CatalystContextEngine.Result cx=holdingContexts.get(h.symbol); if(cx!=null)c.addView(contextBanner(cx));
            PortfolioRiskEngine.Result pr=PortfolioRiskEngine.evaluate(h.cost,h.qty,s,cx);
            String act=PositionActionLabelEngine.label(s,cx,h.cost);
            int ac=act.contains("AZALT")?RED:act.contains("BEKLE")?AMBER:GREEN;
            c.addView(bold(act+"  •  Risk "+fmt(pr.riskScore)+"/100",14,ac));
            c.addView(txt(pr.note,12,Color.DKGRAY));
            c.addView(txt("Hedef süre: "+s.horizonText+"  •  Güven %"+(int)s.confidence+"  •  Stop ref. "+money(s.stopReference,h.symbol),13,NAVY2));'''
if old not in s: raise SystemExit('portfolio decision patch failed')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
