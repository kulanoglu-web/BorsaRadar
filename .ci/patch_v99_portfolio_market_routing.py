from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# The stock detail can belong to another market than the active portfolio profile.
# Route the add directly to the symbol's own portfolio bucket and then display that profile.
old='if(edit==null){holdings.add(new Holding(s,q,c));savePortfolio();loadPortfolio();}else{edit.symbol=s;edit.qty=q;edit.cost=c;savePortfolio();loadPortfolio();}showPortfolio();'
new='''if(edit==null){
                    int targetMarket=MarketSymbol.marketIndex(s); if(targetMarket<0||targetMarket>2)targetMarket=primaryMarket();
                    if(targetMarket!=primaryMarket()){
                        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
                        try{
                            JSONArray a=new JSONArray(sp.getString("portfolio_"+targetMarket,"[]"));
                            boolean found=false;
                            for(int i=0;i<a.length();i++){JSONObject o=a.optJSONObject(i);if(o!=null&&s.equals(o.optString("s",""))){o.put("q",q);o.put("c",c);found=true;break;}}
                            if(!found){JSONObject o=new JSONObject();o.put("s",s);o.put("q",q);o.put("c",c);a.put(o);}
                            sp.edit().putString("portfolio_"+targetMarket,a.toString()).putInt("active_profile",targetMarket).putInt("primary_market",targetMarket).commit();
                            loadPortfolio();Toast.makeText(this,s+" portföye eklendi",Toast.LENGTH_SHORT).show();
                        }catch(Exception ex){Toast.makeText(this,"Portföye eklenemedi",Toast.LENGTH_LONG).show();}
                    }else{holdings.add(new Holding(s,q,c));savePortfolio();loadPortfolio();}
                }else{edit.symbol=s;edit.qty=q;edit.cost=c;savePortfolio();loadPortfolio();}showPortfolio();'''
if old not in s: raise SystemExit('v96 portfolio action missing')
s=s.replace(old,new,1)
# Do not lock the dialog to an unrelated active profile when opened from a stock detail.
old2='market.setSelection(primaryMarket());\n        market.setEnabled(false);'
new2='market.setSelection(preset!=null?Math.max(0,MarketSymbol.marketIndex(parseSymbol(preset))):primaryMarket());\n        market.setEnabled(edit==null&&preset==null);'
if old2 in s:s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
