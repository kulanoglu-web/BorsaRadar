from pathlib import Path
import re
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# RadarItem: teknik skor korunur, ikinci asamada baglamla ayrica yeniden siralanir.
s=s.replace('''    static final class RadarItem {
        String symbol, recommendation, why, horizon;
        double price, score, confidence;
        RadarItem(String s, ShortPulseEngine.Result r) {
            symbol=s; recommendation=r.recommendation; why=r.explanation; horizon=r.horizonText;
            price=r.price; score=r.score; confidence=r.confidence;
        }
    }''','''    static final class RadarItem {
        String symbol, recommendation, why, horizon, contextLabel="";
        double price, score, confidence, rankedScore, contextScore, informationStrength;
        boolean contextLoaded=false;
        RadarItem(String s, ShortPulseEngine.Result r) {
            symbol=s; recommendation=r.recommendation; why=r.explanation; horizon=r.horizonText;
            price=r.price; score=r.score; confidence=r.confidence; rankedScore=r.score;
        }
    }''')

# Radar ekran aciklamasi: iki asamali tarama.
s=s.replace('''top.addView(bold("Tüm hisseler • hafif tarama",19,NAVY)); top.addView(txt("İlk tarama teknik olarak hızlı yapılır. Haber/katalizör bağlamı detay açıldığında yüklenir; böylece yüzlerce gereksiz ağ isteği yapılmaz.",13,Color.DKGRAY));''','''top.addView(bold("Tüm hisseler • iki aşamalı radar",19,NAVY)); top.addView(txt("1) Tüm BIST teknik olarak hızlı taranır. 2) En güçlü 25 aday için haber/KAP/makro bağlamı alınır ve liste yeniden sıralanır. Böylece yüzlerce gereksiz haber isteği yapılmaz.",13,Color.DKGRAY));''')

# Tarama tamamlaninca ilk 25 adayi baglamla zenginlestir.
pat=r'    private void scanRadar\(\) \{.*?\n    \}\n\n    private void renderRadarList'
rep='''    private void scanRadar() {
        if(scanRunning)return; scanRunning=true;scanDone.set(0);scanFailed.set(0);radarResults.clear();showRadar();
        for(String sym:ALL_SYMBOLS)io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"3mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                radarResults.add(new RadarItem(sym,r));
            }catch(Exception e){scanFailed.incrementAndGet();}
            int done=scanDone.incrementAndGet();
            if(done>=ALL_SYMBOLS.length){
                List<RadarItem>sorted=new ArrayList<>(radarResults);
                sorted.sort((a,b)->Double.compare(b.score,a.score));
                radarResults.clear();radarResults.addAll(sorted);
                main.post(this::showRadar);
                enrichRadarTopCandidates(25);
            }else if(done%25==0)main.post(this::showRadar);
        });
    }

    private void enrichRadarTopCandidates(int limit){
        List<RadarItem> candidates=new ArrayList<>(radarResults);
        candidates.sort((a,b)->Double.compare(b.score,a.score));
        int n=Math.min(limit,candidates.size());
        if(n==0){scanRunning=false;main.post(this::showRadar);return;}
        AtomicInteger finished=new AtomicInteger(0);
        for(int i=0;i<n;i++){
            RadarItem item=candidates.get(i);
            io.execute(()->{
                try{
                    UnifiedContextService.Result c=UnifiedContextService.analyze(item.symbol);
                    item.contextLoaded=true;
                    item.contextScore=c.combinedScore;
                    item.informationStrength=c.informationStrength;
                    item.contextLabel=c.strengthLabel+" • "+c.macroTag;
                    item.rankedScore=RadarContextRanker.score(item.score,c);
                }catch(Exception ignored){item.rankedScore=item.score;}
                int k=finished.incrementAndGet();
                if(k==n){
                    radarResults.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore));
                    saveRadarCache();scanRunning=false;
                    main.post(this::showRadar);
                }else if(k%5==0)main.post(this::showRadar);
            });
        }
    }

    private void renderRadarList'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('scanRadar patch failed')

# Listeyi ikinci asama puanina gore sirala ve baglam rozetini goster.
pat=r'    private void renderRadarList\(List<RadarItem> items,int max\) \{.*?\n    \}\n\n    private void singleStockDialog'
rep='''    private void renderRadarList(List<RadarItem> items,int max) {
        items.sort((a,b)->Double.compare(b.rankedScore,a.rankedScore)); content.addView(bold("En güçlü adaylar",18,NAVY)); int n=Math.min(max,items.size());
        for(int i=0;i<n;i++){
            RadarItem r=items.get(i);LinearLayout c=card();
            int col=r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:r.recommendation.contains("AL")?GREEN:AMBER;
            c.addView(bold((i+1)+". "+r.symbol+"   "+r.recommendation,18,col));
            c.addView(txt("Fiyat "+money(r.price,r.symbol)+"  •  Teknik "+fmt(r.score)+"  •  Radar "+fmt(r.rankedScore)+"  •  Güven %"+(int)r.confidence,13,Color.DKGRAY));
            if(r.contextLoaded)c.addView(txt("Bağlam "+fmt(r.contextScore)+"/8 • bilgi "+fmt(r.informationStrength)+"/100 • "+r.contextLabel,12,PURPLE));
            else if(scanRunning&&i<25)c.addView(txt("Haber/KAP ikinci aşama yükleniyor…",12,Color.GRAY));
            c.addView(txt(r.why+" • "+r.horizon,12,Color.GRAY));
            Button d=button("Grafik / Detay + Haber",NAVY2);c.addView(d);d.setOnClickListener(v->analyzeStock(r.symbol));content.addView(c);spacer(6);
        }
    }

    private void singleStockDialog'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: raise SystemExit('renderRadarList patch failed')

# Cache ikinci asama skorlarini da saklasin.
s=s.replace('''o.put("p",r.price);o.put("sc",r.score);o.put("cf",r.confidence);a.put(o);''','''o.put("p",r.price);o.put("sc",r.score);o.put("cf",r.confidence);o.put("rs",r.rankedScore);o.put("cs",r.contextScore);o.put("is",r.informationStrength);o.put("cl",r.contextLabel);o.put("cx",r.contextLoaded);a.put(o);''')
s=s.replace('''pr.confidence=o.getDouble("cf");radarResults.add(new RadarItem(o.getString("s"),pr));''','''pr.confidence=o.getDouble("cf");RadarItem ri=new RadarItem(o.getString("s"),pr);ri.rankedScore=o.has("rs")?o.getDouble("rs"):ri.score;ri.contextScore=o.optDouble("cs",0);ri.informationStrength=o.optDouble("is",0);ri.contextLabel=o.optString("cl","");ri.contextLoaded=o.optBoolean("cx",false);radarResults.add(ri);''')

p.write_text(s,encoding='utf-8')
