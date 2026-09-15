from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Publish useful partial results continuously instead of leaving the user on Taranıyor until every symbol finishes.
old='''            int done=shortScanDone.incrementAndGet();
            if(done>=universe.length){
                List<RadarItem> sorted=new ArrayList<>(buffer);
                sorted.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
                if(!sorted.isEmpty()){shortRadarResults.clear();int n=Math.min(30,sorted.size());shortRadarResults.addAll(sorted.subList(0,n));saveShortRadarCache();}
                shortScanRunning=false;main.post(this::showHourlyRadar);
            }else if(done%20==0)main.post(this::showHourlyRadar);'''
new='''            int done=shortScanDone.incrementAndGet();
            // Every small batch, publish the best candidates found so far. The scan continues in background threads.
            if(done%8==0 || done>=universe.length){
                List<RadarItem> sorted=new ArrayList<>(buffer);
                sorted.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
                if(!sorted.isEmpty()){
                    synchronized(shortRadarResults){
                        shortRadarResults.clear();
                        int n=Math.min(30,sorted.size());
                        shortRadarResults.addAll(sorted.subList(0,n));
                    }
                    saveShortRadarCache();
                }
                if(done>=universe.length)shortScanRunning=false;
                main.post(this::showHourlyRadar);
            }'''
if old not in s: raise SystemExit('hourly completion block missing')
s=s.replace(old,new,1)
# Make the status explicit and keep old/partial results visible during a refresh.
old2='''Button b=button(shortScanRunning?"Taranıyor…":"Saatlik Taramayı Yenile",GREEN);b.setEnabled(!shortScanRunning);b.setOnClickListener(v->scanShortTerm("1S"));c.addView(b);content.addView(c);spacer(8);'''
new2='''int total=marketSymbols(primaryMarket()).length;
        String scanLabel=shortScanRunning?("Taranıyor • "+shortScanDone.get()+"/"+total+" • sonuçlar geldikçe gösteriliyor"):"Saatlik Taramayı Yenile";
        Button b=button(scanLabel,GREEN);b.setEnabled(!shortScanRunning);b.setOnClickListener(v->scanShortTerm("1S"));c.addView(b);content.addView(c);spacer(8);'''
if old2 not in s: raise SystemExit('hourly button block missing')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
