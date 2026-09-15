from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

start=s.find('    private void savePortfolio(){')
end=s.find('    private void loadPortfolio(){',start)
if start<0 or end<0: raise SystemExit('savePortfolio missing')
load_end=s.find('\n    private ',end+10)
if load_end<0: raise SystemExit('loadPortfolio end missing')
new='''    private void savePortfolio(){
        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        JSONArray[] buckets={new JSONArray(),new JSONArray(),new JSONArray()};
        try{
            for(int m=0;m<3;m++){
                try{JSONArray old=new JSONArray(sp.getString("portfolio_"+m,"[]"));for(int i=0;i<old.length();i++)buckets[m].put(old.getJSONObject(i));}catch(Exception ignored){}
            }
            buckets[primaryMarket()]=new JSONArray();
            for(Holding h:holdings){
                int m=primaryMarket();
                for(int k=0;k<3;k++)for(String x:marketSymbols(k))if(x.equals(h.symbol))m=k;
                JSONObject o=new JSONObject();o.put("s",h.symbol);o.put("q",h.qty);o.put("c",h.cost);buckets[m].put(o);
            }
            android.content.SharedPreferences.Editor e=sp.edit();
            for(int m=0;m<3;m++)e.putString("portfolio_"+m,buckets[m].toString());
            e.commit();
        }catch(Exception ex){Toast.makeText(this,"Portföy kaydedilemedi",Toast.LENGTH_LONG).show();}
    }
    private void loadPortfolio(){
        holdings.clear();
        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        try{
            migrateLegacyPortfolioProfiles();
            JSONArray a=new JSONArray(sp.getString("portfolio_"+primaryMarket(),"[]"));
            java.util.HashSet<String> seen=new java.util.HashSet<>();
            for(int i=0;i<a.length();i++){
                JSONObject o=a.optJSONObject(i); if(o==null)continue;
                String sym=o.optString("s",""); if(sym.length()==0||seen.contains(sym))continue;
                int q=o.optInt("q",0); double c=o.optDouble("c",0); if(q<=0||!Double.isFinite(c)||c<=0)continue;
                holdings.add(new Holding(sym,q,c));seen.add(sym);
            }
        }catch(Exception ex){Toast.makeText(this,"Portföy okunamadı",Toast.LENGTH_LONG).show();}
    }
'''
s=s[:start]+new+s[load_end:]
s=s.replace('savePortfolio();showPortfolio();','savePortfolio(); loadPortfolio(); showPortfolio();')
s=s.replace('savePortfolio(); showPortfolio();','savePortfolio(); loadPortfolio(); showPortfolio();')
p.write_text(s,encoding='utf-8')
