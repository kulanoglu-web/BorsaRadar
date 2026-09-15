from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v88 helpers: compact collapsible sections + separate paper portfolio storage.
anchor='    private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> chart,String frame) {'
helpers='''    private LinearLayout collapsible(String title, android.view.View body, boolean open){
        LinearLayout box=card(); Button h=button((open?"▾ ":"▸ ")+title,Color.rgb(49,55,63)); h.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL); box.addView(h);
        body.setVisibility(open?android.view.View.VISIBLE:android.view.View.GONE); box.addView(body);
        final boolean[] state={open}; h.setOnClickListener(v->{state[0]=!state[0]; body.setVisibility(state[0]?android.view.View.VISIBLE:android.view.View.GONE); h.setText((state[0]?"▾ ":"▸ ")+title);}); return box;
    }
    private void addPaperPosition(String symbol,double price,int qty){
        if(!Double.isFinite(price)||price<=0||qty<=0) return;
        getSharedPreferences("paper_portfolio",MODE_PRIVATE).edit().putString(symbol,price+"|"+qty+"|"+System.currentTimeMillis()).apply();
        Toast.makeText(this,"Fake portföye eklendi: "+symbol,Toast.LENGTH_SHORT).show();
    }
'''
if anchor not in s: raise SystemExit('framed renderStockDetail anchor missing')
s=s.replace(anchor,helpers+'\n'+anchor,1)
deep=s.find(anchor)
nav=s.find('        LinearLayout navRow=new LinearLayout(this); navRow.setOrientation(LinearLayout.HORIZONTAL);',deep)
if nav<0: raise SystemExit('deep nav anchor missing')
insert='''        LinearLayout riskBody=new LinearLayout(this); riskBody.setOrientation(LinearLayout.VERTICAL);
        riskBody.addView(txt("Zararı minimize et: teknik stop referansı "+money(r.stopReference,symbol)+" • hedef süre "+r.horizonText,13,Color.DKGRAY));
        riskBody.addView(txt("Stop seviyesi kırılırsa pozisyonu yeniden değerlendir; körlemesine zararda bekleme yok.",12,Color.GRAY));
        content.addView(collapsible("🛡 Risk Yönetimi / Zarar Minimize",riskBody,false)); spacer(7);
        LinearLayout pfBody=new LinearLayout(this); pfBody.setOrientation(LinearLayout.VERTICAL);
        pfBody.addView(txt("Gerçek portföy: gerçekten aldığın hisseler • Fake portföy: sinyali para riske etmeden test et.",12,Color.GRAY));
        LinearLayout pfBtns=new LinearLayout(this); pfBtns.setOrientation(LinearLayout.HORIZONTAL);
        Button realPf=button("Gerçek Portföye Ekle",GREEN), fakePf=button("Fake Portföye Ekle",Color.rgb(35,105,180));
        pfBtns.addView(realPf,new LinearLayout.LayoutParams(0,-2,1)); pfBtns.addView(fakePf,new LinearLayout.LayoutParams(0,-2,1)); pfBody.addView(pfBtns);
        realPf.setOnClickListener(v->portfolioDialog(null,symbol));
        double paperPrice=(chart!=null&&!chart.isEmpty())?chart.get(chart.size()-1).close:r.price;
        fakePf.setOnClickListener(v->addPaperPosition(symbol,paperPrice,1));
        content.addView(collapsible("🧪 Portföy / Fake Portföy",pfBody,false)); spacer(7);
'''
s=s[:nav]+insert+s[nav:]
if 'loadFullChartFrame' not in s: raise SystemExit('chart frame loader missing')
p.write_text(s,encoding='utf-8')
