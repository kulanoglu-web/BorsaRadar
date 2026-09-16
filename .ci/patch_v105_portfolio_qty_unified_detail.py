from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v105: fake positions need user quantity instead of hard-coded 1.
anchor='''    private void addPaperPosition(String symbol,double price,int qty){'''
if anchor in s and 'private void paperPortfolioDialog(' not in s:
    pos=s.find(anchor)
    end=s.find('    }',pos)+5
    helper='''\n    private void paperPortfolioDialog(String symbol,double price){\n        final EditText qtyInput=new EditText(this); qtyInput.setHint("Adet"); qtyInput.setInputType(android.text.InputType.TYPE_CLASS_NUMBER); qtyInput.setText("1");\n        new AlertDialog.Builder(this).setTitle("Fake Portföye Ekle • "+symbol).setMessage("Alış fiyatı: "+money(price,symbol)+"\\nAdet gir:").setView(qtyInput)\n            .setNegativeButton("İptal",null).setPositiveButton("Ekle",(d,w)->{try{int q=Integer.parseInt(qtyInput.getText().toString().trim());if(q>0)addPaperPosition(symbol,price,q);else Toast.makeText(this,"Adet 1 veya daha büyük olmalı",Toast.LENGTH_SHORT).show();}catch(Exception ex){Toast.makeText(this,"Geçerli adet gir",Toast.LENGTH_SHORT).show();}}).show();\n    }\n'''
    s=s[:end]+helper+s[end:]
# Replace all hard-coded fake quantity actions in both fast/full detail.
s=s.replace('fakePf.setOnClickListener(v->addPaperPosition(symbol,paperPrice,1));','fakePf.setOnClickListener(v->paperPortfolioDialog(symbol,paperPrice));')
s=s.replace('quickFake.setOnClickListener(v->addPaperPosition(symbol,last.close,1));','quickFake.setOnClickListener(v->paperPortfolioDialog(symbol,last.close));')
# Real portfolio: force symbol's actual market into persistent target and do not rely on current profile.
# portfolioDialog still gathers qty/cost, but v99's target-market branch failed for BIST when active profile differed.
old='''                    }else{holdings.add(new Holding(s,q,c));savePortfolio();loadPortfolio();}\n                }else{edit.symbol=s;edit.qty=q;edit.cost=c;savePortfolio();loadPortfolio();}showPortfolio();'''
new='''                    }else{\n                        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);\n                        try{JSONArray a=new JSONArray(sp.getString("portfolio_"+targetMarket,"[]"));boolean found=false;for(int i=0;i<a.length();i++){JSONObject o=a.optJSONObject(i);if(o!=null&&s.equals(o.optString("s",""))){o.put("q",q);o.put("c",c);found=true;break;}}if(!found){JSONObject o=new JSONObject();o.put("s",s);o.put("q",q);o.put("c",c);a.put(o);}sp.edit().putString("portfolio_"+targetMarket,a.toString()).putInt("active_profile",targetMarket).putInt("primary_market",targetMarket).commit();loadPortfolio();Toast.makeText(this,s+" gerçek portföye eklendi",Toast.LENGTH_SHORT).show();}catch(Exception ex){Toast.makeText(this,"Portföye eklenemedi: "+ex.getMessage(),Toast.LENGTH_LONG).show();}\n                    }\n                }else{edit.symbol=s;edit.qty=q;edit.cost=c;savePortfolio();loadPortfolio();}showPortfolio();'''
if old in s:s=s.replace(old,new,1)
# Make fast detail identify itself as the same analysis, not a different screen.
s=s.replace('symbol+" • hızlı görünüm"','symbol+" • analiz"')
s=s.replace('"Güncel fiyat/grafik • Detay hazırlanırken ekran kullanılabilir"','"Güncel fiyat/grafik • Analiz bölümleri hazırlanıyor"')
p.write_text(s,encoding='utf-8')
