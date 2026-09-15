from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Hourly radar: manual refresh must not stay blocked by a stale running flag.
old='''private void scanShortTerm(String mode){
        if(shortScanRunning)return;
        shortScanRunning=true;shortScanMode=mode;shortScanDone.set(0);shortScanFailed.set(0);'''
new='''private void scanShortTerm(String mode){
        if(shortScanRunning && shortScanDone.get()>0 && shortScanDone.get()<marketSymbols(primaryMarket()).length){shortScanRunning=false;}
        if(shortScanRunning)return;
        shortScanRunning=true;shortScanMode=mode;shortScanDone.set(0);shortScanFailed.set(0);'''
if old in s:s=s.replace(old,new,1)
s=s.replace('''b.setEnabled(!shortScanRunning);b.setOnClickListener(v->scanShortTerm("1S"));''','''b.setEnabled(true);b.setOnClickListener(v->{shortScanRunning=false;scanShortTerm("1S");});''',1)

# Dedicated Fake Portfolio navigation button.
nav='''        Button p=button('''
i=s.find(nav)
if i>=0 and 'Button fake=button("Fake"' not in s[max(0,i-500):i+900]:
    e=s.find('\n',i)
    s=s[:e+1]+'        Button fake=button("Fake",ORANGE);\n'+s[e+1:]
    s=s.replace('for(Button b:new Button[]{p,r,hour,one,three})','for(Button b:new Button[]{p,fake,r,hour,one,three})',1)
    s=s.replace('nav.addView(p,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(r','nav.addView(p,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(fake,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(r',1)
    s=s.replace('p.setOnClickListener(v->showPortfolio()); r.setOnClickListener','p.setOnClickListener(v->showPortfolio()); fake.setOnClickListener(v->showFakePortfolio()); r.setOnClickListener',1)

anchor=s.find('private void showBaskets()')
if anchor<0: raise SystemExit('basket anchor missing')
if 'private void showFakePortfolio()' not in s:
    method=r'''private void showFakePortfolio(){
        shell("Fake Portföy • Deneme");
        LinearLayout head=card();
        head.addView(bold("🧪 FAKE PORTFÖY",21,ORANGE));
        head.addView(txt("Gerçek portföyden tamamen ayrıdır • sanal pozisyon performansı",13,Color.DKGRAY));
        content.addView(head);spacer(8);
        java.util.Map<String,?> all=getSharedPreferences("paper_portfolio",MODE_PRIVATE).getAll();
        if(all==null||all.isEmpty()){
            LinearLayout empty=card();empty.addView(bold("Henüz Fake pozisyon yok",18,Color.LTGRAY));
            empty.addView(txt("Bir hissenin detayından Fake Portföye Ekle ile sanal pozisyon oluştur.",14,Color.GRAY));
            content.addView(empty);return;
        }
        double totalCost=0,totalNow=0; int valid=0;
        for(java.util.Map.Entry<String,?> en:all.entrySet()){
            try{
                final String symbol=en.getKey();String raw=String.valueOf(en.getValue());String[] z=raw.split("\\|");
                if(z.length<2)continue;double buy=Double.parseDouble(z[0]);int qty=Integer.parseInt(z[1]);
                if(!Double.isFinite(buy)||buy<=0||qty<=0)continue;
                double now=buy;
                synchronized(radarResults){for(RadarItem item:radarResults){if(item.symbol.equals(symbol)&&item.r!=null&&Double.isFinite(item.r.price)&&item.r.price>0){now=item.r.price;break;}}}
                if(now==buy){synchronized(shortRadarResults){for(RadarItem item:shortRadarResults){if(item.symbol.equals(symbol)&&item.r!=null&&Double.isFinite(item.r.price)&&item.r.price>0){now=item.r.price;break;}}}}
                double cost=buy*qty,val=now*qty,pnl=val-cost,pct=cost>0?100.0*pnl/cost:0;
                totalCost+=cost;totalNow+=val;valid++;
                LinearLayout c=card();c.addView(bold(symbol+"   "+(pnl>=0?"▲ ":"▼ ")+String.format(java.util.Locale.US,"%+.2f%%",pct),18,pnl>=0?GREEN:RED));
                c.addView(txt("Adet "+qty+" • Alış "+money(buy,symbol)+" • Güncel "+money(now,symbol),14,Color.LTGRAY));
                c.addView(txt("K/Z "+money(pnl,symbol)+" • Değer "+money(val,symbol),14,pnl>=0?GREEN:RED));
                c.setOnClickListener(v->analyzeStock(symbol));content.addView(c);spacer(6);
            }catch(Exception ignored){}
        }
        if(valid>0){double pnl=totalNow-totalCost,pct=totalCost>0?100*pnl/totalCost:0;LinearLayout sum=card();sum.addView(bold("TOPLAM FAKE PERFORMANS",16,Color.WHITE));sum.addView(bold((pnl>=0?"▲ ":"▼ ")+String.format(java.util.Locale.US,"%+.2f%% • ",pct)+String.format(java.util.Locale.US,"%.2f",pnl),20,pnl>=0?GREEN:RED));content.addView(sum,0);}
    }

    '''
    s=s[:anchor]+method+s[anchor:]

p.write_text(s,encoding='utf-8')
