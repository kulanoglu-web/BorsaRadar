from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v112: keep v111 stable startup. Single-stock gets immediate shell/cache rendering and
# portfolio add writes directly to the correct market bucket without switching screens/profiles.
# Ensure a dedicated detail executor so a full radar scan cannot starve a single-stock request.
field='    private final Handler main = new Handler(Looper.getMainLooper());'
if 'detailIo' not in s:
    s=s.replace(field,field+'\n    private final ExecutorService detailIo = Executors.newFixedThreadPool(2);',1)
s=s.replace('''        io.shutdownNow();
        super.onDestroy();''','''        io.shutdownNow();
        detailIo.shutdownNow();
        super.onDestroy();''',1)
# Route analyzeStock background work to the dedicated executor. Later v101/v107 patches may
# replace the method body, so also replace the first executor call inside that method generically.
a=s.find('private void analyzeStock(String symbol)')
if a>=0:
    b=s.find('\n    private void ',a+10)
    if b<0:b=len(s)
    block=s[a:b].replace('io.execute(()->','detailIo.execute(()->',1)
    s=s[:a]+block+s[b:]
# Add robust direct portfolio dialog helper. It persists to target market and never changes active profile.
marker='    private void showBaskets()'
helper='''    private int marketForSymbol(String symbol){
        String n=MarketDataService.normalizeSymbol(symbol);
        if(n.endsWith(".DE"))return 1;
        if(n.endsWith(".IS"))return 0;
        return 2;
    }
    private void addAnalyzedStockToPortfolio(String symbol,double price){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(18),dp(6),dp(18),0);
        EditText qty=new EditText(this);qty.setHint("Lot/Adet");qty.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText cost=new EditText(this);cost.setHint("Alış fiyatı");cost.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);if(price>0)cost.setText(String.format(Locale.US,"%.2f",price));
        box.addView(qty);box.addView(cost);
        new AlertDialog.Builder(this).setTitle(symbol+" • Portföye ekle").setView(box).setPositiveButton("Kaydet",(d,w)->{
            try{
                int q=Integer.parseInt(qty.getText().toString().trim());double c=Double.parseDouble(cost.getText().toString().trim().replace(',','.'));if(q<=0||c<=0)throw new Exception();
                int m=marketForSymbol(symbol);android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);JSONArray a;
                try{a=new JSONArray(sp.getString("portfolio_"+m,"[]"));}catch(Exception e){a=new JSONArray();}
                JSONArray out=new JSONArray();boolean updated=false;
                for(int i=0;i<a.length();i++){JSONObject o=a.optJSONObject(i);if(o==null)continue;if(symbol.equals(o.optString("s"))){o=new JSONObject();o.put("s",symbol);o.put("q",q);o.put("c",c);updated=true;}out.put(o);}
                if(!updated){JSONObject o=new JSONObject();o.put("s",symbol);o.put("q",q);o.put("c",c);out.put(o);}
                sp.edit().putString("portfolio_"+m,out.toString()).commit();
                if(m==primaryMarket())loadPortfolio();
                Toast.makeText(this,symbol+" portföye kaydedildi",Toast.LENGTH_SHORT).show();
            }catch(Exception e){Toast.makeText(this,"Adet ve alış fiyatını kontrol et",Toast.LENGTH_LONG).show();}
        }).setNegativeButton("İptal",null).show();
    }

'''
if 'private void addAnalyzedStockToPortfolio' not in s and marker in s:s=s.replace(marker,helper+marker,1)
# Route detail portfolio buttons to direct persistence helper; handle both base and patched variants.
s=s.replace('add.setOnClickListener(v->portfolioDialog(null,symbol));','add.setOnClickListener(v->addAnalyzedStockToPortfolio(symbol,r.price));')
s=s.replace('add.setOnClickListener(v->paperPortfolioDialog(symbol,r.price));','add.setOnClickListener(v->addAnalyzedStockToPortfolio(symbol,r.price));')
# If v107 cache exists after patch chain, analyzeStock should render cache immediately and use detailIo.
a=s.find('private void analyzeStock(String symbol)')
if a>=0:
    b=s.find('\n    private void ',a+10)
    if b<0:b=len(s)
    block=s[a:b].replace('io.execute(()->','detailIo.execute(()->',1)
    s=s[:a]+block+s[b:]
p.write_text(s,encoding='utf-8')
