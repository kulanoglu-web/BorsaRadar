from pathlib import Path
import re
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
s=s.replace('import android.widget.Space;','import android.widget.Space;\nimport android.widget.Spinner;')
s=s.replace('c.addView(bold(h.symbol+"  •  "+h.qty+" lot",20,NAVY));','c.addView(bold(MarketSymbol.label(h.symbol)+"  •  "+h.qty+" adet",20,NAVY));')
s=s.replace('c.addView(txt("Ortalama maliyet  "+money(h.cost),14,Color.DKGRAY));','c.addView(txt("Ortalama maliyet  "+String.format(Locale.US,"%.2f %s",h.cost,MarketSymbol.currency(h.symbol)),14,Color.DKGRAY));')
s=s.replace('c.addView(bold("Son  "+money(s.price)+"   P/L  "+money(pnl)+"  (%"+fmt(pct)+")",16,pnl>=0?GREEN:RED));','c.addView(bold("Son  "+String.format(Locale.US,"%.2f %s",s.price,MarketSymbol.currency(h.symbol))+"   P/L  "+String.format(Locale.US,"%.2f %s",pnl,MarketSymbol.currency(h.symbol))+"  (%"+fmt(pct)+")",16,pnl>=0?GREEN:RED));')
pattern=r'    private void portfolioDialog\(Holding edit,String preset\) \{.*?\n    \}\n\n    private void showRadar\(\)'
replacement='''    private void portfolioDialog(Holding edit,String preset) {
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(6),dp(18),0);
        Spinner market=new Spinner(this);
        String[] markets={"Türkiye / BIST","Almanya / Xetra-Frankfurt","ABD / Nasdaq-NYSE"};
        market.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,markets));
        AutoCompleteTextView sym=new AutoCompleteTextView(this); sym.setHint("Direkt kod: THYAO / SAP / NVDA"); sym.setThreshold(1); sym.setSingleLine(true);
        sym.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,BistUniverse.ENTRIES));
        EditText qty=new EditText(this); qty.setHint("Adet / lot"); qty.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText cost=new EditText(this); cost.setHint("Alış fiyatı"); cost.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        if(edit!=null){market.setSelection(MarketSymbol.marketIndex(edit.symbol));sym.setText(edit.symbol,false);qty.setText(String.valueOf(edit.qty));cost.setText(String.valueOf(edit.cost));}
        else if(preset!=null){market.setSelection(MarketSymbol.marketIndex(preset));sym.setText(preset,false);}
        box.addView(txt("Piyasa",12,Color.DKGRAY)); box.addView(market); box.addView(sym);box.addView(qty);box.addView(cost);
        box.addView(txt("Almanya ve ABD için toplu tarama yok; hisse kodunu doğrudan gir.",12,Color.GRAY));
        new AlertDialog.Builder(this).setTitle(edit==null?"Alış / portföy girişi":"Pozisyonu düzenle").setView(box)
                .setPositiveButton("Kaydet",(d,w)->{
                    try{
                        int mi=market.getSelectedItemPosition(); String raw=sym.getText().toString().trim().toUpperCase(Locale.ROOT); String code;
                        if(mi==0){code=BistUniverse.symbolFromEntry(raw);if(code.length()<2)code=raw;code=MarketSymbol.manual(code,0);}else code=MarketSymbol.manual(raw,mi);
                        if(code.length()<4)throw new Exception();
                        int q=Integer.parseInt(qty.getText().toString()); double c=Double.parseDouble(cost.getText().toString().replace(',','.'));
                        if(q<=0||c<=0)throw new Exception();
                        if(edit==null)holdings.add(new Holding(code,q,c));else{edit.symbol=code;edit.qty=q;edit.cost=c;}
                        savePortfolio();showPortfolio();
                    }catch(Exception ex){Toast.makeText(this,"Hisse kodu / adet / fiyatı kontrol et",Toast.LENGTH_LONG).show();}
                }).setNegativeButton("İptal",null).show();
    }

    private void showRadar()'''
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit('portfolio patch failed')
pattern=r'    private void singleStockDialog\(\) \{.*?\n    \}'
replacement='''    private void singleStockDialog() {
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(6),dp(18),0);
        Spinner market=new Spinner(this);
        market.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"Türkiye / BIST","Almanya / Xetra-Frankfurt","ABD / Nasdaq-NYSE"}));
        AutoCompleteTextView x=new AutoCompleteTextView(this); x.setHint("Direkt kod: THYAO / SAP / NVDA"); x.setThreshold(1); x.setSingleLine(true);
        x.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,BistUniverse.ENTRIES));
        box.addView(market); box.addView(x); box.addView(txt("Almanya ve ABD hisseleri direkt kod girişiyle analiz edilir.",12,Color.GRAY));
        new AlertDialog.Builder(this).setTitle("Tek hisse analiz").setView(box)
                .setPositiveButton("Analiz et",(d,w)->{int mi=market.getSelectedItemPosition();String raw=x.getText().toString().trim().toUpperCase(Locale.ROOT);String code;if(mi==0){code=BistUniverse.symbolFromEntry(raw);if(code.length()<2)code=raw;code=MarketSymbol.manual(code,0);}else code=MarketSymbol.manual(raw,mi);if(code.length()>=4)analyzeStock(code);else Toast.makeText(this,"Hisse kodunu kontrol et",Toast.LENGTH_SHORT).show();})
                .setNegativeButton("İptal",null).show();
    }'''
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit('single stock patch failed')
p.write_text(s,encoding='utf-8')
