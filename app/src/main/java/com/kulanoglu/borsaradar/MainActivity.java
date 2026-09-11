package com.kulanoglu.borsaradar;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.text.InputType;
import android.view.Gravity;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Space;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final String PREFS = "borsaradar_final";
    private static final int NAVY = Color.rgb(9, 30, 54);
    private static final int NAVY2 = Color.rgb(17, 50, 82);
    private static final int GREEN = Color.rgb(0, 135, 92);
    private static final int RED = Color.rgb(205, 42, 55);
    private static final int AMBER = Color.rgb(225, 145, 0);
    private static final int PURPLE = Color.rgb(104, 76, 190);
    private static final int BG = Color.rgb(244, 247, 251);
    private static final String[] ALL_SYMBOLS = BistUniverse.symbols(true);
    private static final String[] DIVIDEND_POOL = {
            "AKBNK","ANHYT","AYGAZ","BIMAS","CCOLA","DOAS","ENJSA","ENKAI","EREGL",
            "FROTO","GARAN","ISCTR","ISDMR","KCHOL","MGROS","SAHOL","SISE","TCELL",
            "THYAO","TOASO","TTKOM","TTRAK","TUPRS","ULKER","YKBNK"
    };

    static final class Holding {
        String symbol; int qty; double cost;
        Holding(String s, int q, double c) { symbol=s; qty=q; cost=c; }
    }

    static final class RadarItem {
        String symbol, recommendation, why, horizon;
        double price, score, confidence;
        RadarItem(String s, ShortPulseEngine.Result r) {
            symbol=s; recommendation=r.recommendation; why=r.explanation; horizon=r.horizonText;
            price=r.price; score=r.score; confidence=r.confidence;
        }
    }

    private LinearLayout content;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService io = Executors.newFixedThreadPool(5);
    private final List<Holding> holdings = new ArrayList<>();
    private final Map<String, ShortPulseEngine.Result> holdingSignals = new HashMap<>();
    private final List<RadarItem> radarResults = Collections.synchronizedList(new ArrayList<>());
    private volatile boolean scanRunning=false;
    private volatile int scanDone=0, scanFailed=0;

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        loadPortfolio();
        loadRadarCache();
        showPortfolio();
    }

    @Override protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }

    private int dp(int x) { return Math.round(x * getResources().getDisplayMetrics().density); }

    private TextView txt(String text, int sp, int color) {
        TextView v=new TextView(this);
        v.setText(text); v.setTextSize(sp); v.setTextColor(color);
        v.setPadding(dp(14),dp(8),dp(14),dp(8));
        return v;
    }

    private TextView bold(String text, int sp, int color) {
        TextView v=txt(text,sp,color); v.setTypeface(null, Typeface.BOLD); return v;
    }

    private Button button(String text, int color) {
        Button b=new Button(this);
        b.setText(text); b.setAllCaps(false); b.setTextColor(Color.WHITE); b.setTextSize(14);
        b.setBackgroundColor(color); b.setPadding(dp(8),dp(7),dp(8),dp(7));
        return b;
    }

    private void spacer(int h) { Space s=new Space(this); content.addView(s,new LinearLayout.LayoutParams(1,dp(h))); }

    private LinearLayout card() {
        LinearLayout c=new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setPadding(dp(12),dp(10),dp(12),dp(10));
        c.setBackgroundColor(Color.WHITE);
        return c;
    }

    private void shell(String page) {
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);

        LinearLayout head=new LinearLayout(this);
        head.setOrientation(LinearLayout.VERTICAL); head.setPadding(dp(16),dp(12),dp(16),dp(10)); head.setBackgroundColor(NAVY);
        TextView brand=bold("BORSA RADAR",23,Color.WHITE);
        brand.setPadding(0,0,0,0); head.addView(brand);
        TextView sub=txt(page,13,Color.rgb(190,207,224)); sub.setPadding(0,2,0,0); head.addView(sub);
        root.addView(head);

        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL);
        Button p=button("Portföy",NAVY2), r=button("Radar",GREEN), one=button("Tek Hisse",PURPLE), three=button("3 Sepet",AMBER);
        nav.addView(p,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(r,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(one,new LinearLayout.LayoutParams(0,-2,1));
        nav.addView(three,new LinearLayout.LayoutParams(0,-2,1));
        p.setOnClickListener(v->showPortfolio()); r.setOnClickListener(v->showRadar());
        one.setOnClickListener(v->singleStockDialog()); three.setOnClickListener(v->showBaskets());
        root.addView(nav);

        ScrollView sv=new ScrollView(this);
        content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(10),dp(8),dp(10),dp(14));
        sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));

        TextView foot=txt("BorsaRadar • 1–10 işlem günü odaklı teknik karar destek",11,Color.rgb(100,110,124));
        foot.setGravity(Gravity.CENTER); root.addView(foot);
        setContentView(root);
    }

    private void showPortfolio() {
        shell("Portföyüm");
        LinearLayout actions=new LinearLayout(this);
        Button add=button("+ Hisse Ekle",GREEN), refresh=button("Tümünü Güncelle",NAVY2);
        actions.addView(add,new LinearLayout.LayoutParams(0,-2,1)); actions.addView(refresh,new LinearLayout.LayoutParams(0,-2,1));
        content.addView(actions);
        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setOnClickListener(v->refreshPortfolio());
        spacer(8);
        if(holdings.isEmpty()) {
            LinearLayout c=card(); c.addView(bold("Portföy boş",19,NAVY)); c.addView(txt("Hisse ekleyince maliyet, güncel fiyat, kâr/zarar ve AL–TUT–SAT değerlendirmesi burada görünür.",14,Color.DKGRAY)); content.addView(c); return;
        }
        for(Holding h:new ArrayList<>(holdings)) renderHolding(h);
    }

    private void renderHolding(Holding h) {
        LinearLayout c=card();
        c.addView(bold(h.symbol+"  •  "+h.qty+" lot",20,NAVY));
        c.addView(txt("Ortalama maliyet  "+money(h.cost),14,Color.DKGRAY));
        ShortPulseEngine.Result s=holdingSignals.get(h.symbol);
        if(s==null) c.addView(txt("Güncel değerlendirme için 'Tümünü Güncelle'ye bas.",13,Color.GRAY));
        else {
            double pnl=(s.price-h.cost)*h.qty, pct=h.cost>0?(s.price/h.cost-1)*100:0;
            c.addView(bold("Son  "+money(s.price)+"   P/L  "+money(pnl)+"  (%"+fmt(pct)+")",16,pnl>=0?GREEN:RED));
            c.addView(signalBanner(s));
            c.addView(txt(s.explanation,13,Color.DKGRAY));
            c.addView(txt("Hedef süre: "+s.horizonText+"  •  Güven %"+(int)s.confidence+"  •  Stop ref. "+money(s.stopReference),13,NAVY2));
        }
        LinearLayout row=new LinearLayout(this);
        Button detail=button("Grafik / Tavsiye",NAVY2), edit=button("Düzenle",AMBER), del=button("Sil",RED);
        row.addView(detail,new LinearLayout.LayoutParams(0,-2,1.2f)); row.addView(edit,new LinearLayout.LayoutParams(0,-2,1)); row.addView(del,new LinearLayout.LayoutParams(0,-2,.7f));
        c.addView(row);
        detail.setOnClickListener(v->analyzeStock(h.symbol)); edit.setOnClickListener(v->portfolioDialog(h,h.symbol));
        del.setOnClickListener(v->{holdings.remove(h); savePortfolio(); showPortfolio();});
        content.addView(c); spacer(8);
    }

    private TextView signalBanner(ShortPulseEngine.Result s) {
        int color=s.recommendation.contains("SAT")||s.recommendation.contains("RİSK")||s.recommendation.contains("KOVALAMA")?RED:
                s.recommendation.contains("AL")?GREEN:AMBER;
        TextView v=bold(s.recommendation+"  •  Pulse "+fmt(s.score),20,Color.WHITE);
        v.setGravity(Gravity.CENTER); v.setBackgroundColor(color); v.setPadding(dp(12),dp(12),dp(12),dp(12)); return v;
    }

    private void refreshPortfolio() {
        if(holdings.isEmpty()){Toast.makeText(this,"Önce hisse ekle",Toast.LENGTH_SHORT).show();return;}
        shell("Portföy güncelleniyor");
        ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal); bar.setMax(holdings.size()); content.addView(bar);
        TextView st=txt("0/"+holdings.size(),15,NAVY); content.addView(st);
        final int[] done={0};
        for(Holding h:new ArrayList<>(holdings)) io.execute(()->{
            try { List<MarketDataService.Candle> d=MarketDataService.fetchDaily(h.symbol,"1mo"); holdingSignals.put(h.symbol,ShortPulseEngine.analyze(d)); } catch(Exception ignored){}
            main.post(()->{ done[0]++; bar.setProgress(done[0]); st.setText(done[0]+"/"+holdings.size()); if(done[0]>=holdings.size()) showPortfolio(); });
        });
    }

    private void portfolioDialog(Holding edit,String preset) {
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(6),dp(18),0);
        AutoCompleteTextView sym=new AutoCompleteTextView(this); sym.setHint("Hisse kodu / şirket adı"); sym.setThreshold(1); sym.setSingleLine(true);
        sym.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,BistUniverse.ENTRIES));
        EditText qty=new EditText(this); qty.setHint("Lot"); qty.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText cost=new EditText(this); cost.setHint("Alış fiyatı"); cost.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        if(edit!=null){sym.setText(edit.symbol,false);qty.setText(String.valueOf(edit.qty));cost.setText(String.valueOf(edit.cost));}
        else if(preset!=null) sym.setText(preset,false);
        box.addView(sym);box.addView(qty);box.addView(cost);
        new AlertDialog.Builder(this).setTitle(edit==null?"Portföye ekle":"Pozisyonu düzenle").setView(box)
                .setPositiveButton("Kaydet",(d,w)->{
                    try{
                        String s=BistUniverse.symbolFromEntry(sym.getText().toString().trim().toUpperCase(Locale.ROOT));
                        if(s.length()<2) throw new Exception();
                        int q=Integer.parseInt(qty.getText().toString()); double c=Double.parseDouble(cost.getText().toString().replace(',','.'));
                        if(q<=0||c<=0)throw new Exception();
                        if(edit==null)holdings.add(new Holding(s,q,c));else{edit.symbol=s;edit.qty=q;edit.cost=c;}
                        savePortfolio();showPortfolio();
                    }catch(Exception ex){Toast.makeText(this,"Hisse / lot / fiyatı kontrol et",Toast.LENGTH_LONG).show();}
                }).setNegativeButton("İptal",null).show();
    }

    private void showRadar() {
        shell("Tüm Borsa İstanbul Radarı");
        LinearLayout top=card();
        top.addView(bold("Tüm hisseler • hafif tarama",19,NAVY));
        top.addView(txt("Telefon her hisse için yalnızca yaklaşık 1 aylık günlük veri çeker; karar motoru son 10–12 işlem gününe ağırlık verir.",13,Color.DKGRAY));
        Button scan=button(scanRunning?"Tarama devam ediyor…":"Tüm BIST'i Tara",GREEN); top.addView(scan); scan.setEnabled(!scanRunning); scan.setOnClickListener(v->scanRadar());
        content.addView(top); spacer(8);
        if(scanRunning){
            ProgressBar pb=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal); pb.setMax(ALL_SYMBOLS.length);pb.setProgress(scanDone);content.addView(pb);
            content.addView(txt(scanDone+"/"+ALL_SYMBOLS.length+" • başarısız "+scanFailed,14,NAVY));
        }
        if(!radarResults.isEmpty()) renderRadarList(new ArrayList<>(radarResults),30);
        else content.addView(txt("Henüz radar sonucu yok.",14,Color.GRAY));
    }

    private void scanRadar() {
        if(scanRunning)return;
        scanRunning=true;scanDone=0;scanFailed=0;radarResults.clear();showRadar();
        for(String sym:ALL_SYMBOLS) io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"1mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                radarResults.add(new RadarItem(sym,r));
            }catch(Exception e){scanFailed++;}
            scanDone++;
            if(scanDone>=ALL_SYMBOLS.length){
                scanRunning=false;
                List<RadarItem> sorted=new ArrayList<>(radarResults); sorted.sort((a,b)->Double.compare(b.score,a.score));
                radarResults.clear(); radarResults.addAll(sorted); saveRadarCache();
                main.post(this::showRadar);
            } else if(scanDone%25==0) main.post(this::showRadar);
        });
    }

    private void renderRadarList(List<RadarItem> items,int max) {
        items.sort((a,b)->Double.compare(b.score,a.score));
        TextView h=bold("En güçlü adaylar",18,NAVY);content.addView(h);
        int n=Math.min(max,items.size());
        for(int i=0;i<n;i++){
            RadarItem r=items.get(i); LinearLayout c=card();
            int col=r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:r.recommendation.contains("AL")?GREEN:AMBER;
            c.addView(bold((i+1)+". "+r.symbol+"   "+r.recommendation,18,col));
            c.addView(txt("Fiyat "+money(r.price)+"  •  Pulse "+fmt(r.score)+"  •  Güven %"+(int)r.confidence+"  •  "+r.horizon,13,Color.DKGRAY));
            c.addView(txt(r.why,12,Color.GRAY));
            Button d=button("Grafik / Detay",NAVY2); c.addView(d); d.setOnClickListener(v->analyzeStock(r.symbol));
            content.addView(c);spacer(6);
        }
    }

    private void singleStockDialog() {
        AutoCompleteTextView s=new AutoCompleteTextView(this); s.setHint("Örn. KTLEV, THYAO, TUPRS"); s.setThreshold(1);
        s.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,BistUniverse.ENTRIES));
        new AlertDialog.Builder(this).setTitle("Tek hisse analiz / tavsiye").setView(s)
                .setPositiveButton("Analiz et",(d,w)->{String sym=BistUniverse.symbolFromEntry(s.getText().toString().trim().toUpperCase(Locale.ROOT)); if(sym.length()>=2)analyzeStock(sym);})
                .setNegativeButton("İptal",null).show();
    }

    private void analyzeStock(String symbol) {
        shell(symbol+" • analiz");
        ProgressBar p=new ProgressBar(this);content.addView(p);content.addView(txt("Son veriler alınıyor…",15,NAVY));
        io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(symbol,"1mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                List<MarketDataService.Candle> chart=d.subList(Math.max(0,d.size()-10),d.size());
                main.post(()->renderStockDetail(symbol,r,chart));
            }catch(Exception e){main.post(()->{shell(symbol+" • analiz");content.addView(txt("Veri alınamadı: "+e.getMessage(),15,RED));});}
        });
    }

    private void renderStockDetail(String symbol,ShortPulseEngine.Result r,List<MarketDataService.Candle> chart) {
        shell(symbol+" • Son 10 işlem günü");
        LinearLayout q=card();q.addView(bold(symbol,22,NAVY));q.addView(bold(money(r.price),25,r.changePct>=0?GREEN:RED));
        q.addView(txt("Son gün %"+fmt(r.changePct)+"  •  ATR% "+fmt(r.atrPct)+"  •  RelVol x"+fmt(r.relativeVolume),14,Color.DKGRAY));content.addView(q);spacer(7);
        content.addView(signalBanner(r));spacer(7);
        content.addView(new PriceChartView(this,chart,"SON 10 İŞLEM GÜNÜ"),new LinearLayout.LayoutParams(-1,dp(300)));spacer(7);
        LinearLayout info=card();info.addView(bold("Neye göre?",17,NAVY));info.addView(txt(r.explanation,14,Color.DKGRAY));
        info.addView(txt("Momentum: "+r.momentumText+"  •  Para/hacim: "+r.flowText+"  •  Trend: "+r.trendText,13,Color.DKGRAY));
        info.addView(txt("Hedef: "+r.horizonText+"  •  Güven %"+(int)r.confidence+"  •  Stop ref. "+money(r.stopReference),13,NAVY2));content.addView(info);
        Button add=button("Portföye Ekle",GREEN);content.addView(add);add.setOnClickListener(v->portfolioDialog(null,symbol));
    }

    private void showBaskets() {
        shell("100.000 TL • 3 Sepet");
        if(radarResults.isEmpty()){
            LinearLayout c=card();c.addView(bold("Önce radar taraması gerekiyor",18,NAVY));c.addView(txt("Tarama bir kez tamamlanınca sonuç kaydedilir; ekrandan çıksan da kaybolmaz.",13,Color.DKGRAY));
            Button go=button("Radarı Aç",GREEN);c.addView(go);go.setOnClickListener(v->showRadar());content.addView(c);return;
        }
        List<RadarItem> all=new ArrayList<>(radarResults);all.sort((a,b)->Double.compare(b.score,a.score));
        List<RadarItem> fast=new ArrayList<>(), twoWeek=new ArrayList<>(), div=new ArrayList<>();
        List<String> dp=Arrays.asList(DIVIDEND_POOL);
        for(RadarItem r:all){
            if(r.score>=5.2 && r.confidence>=60)fast.add(r);
            if(r.score>=3.7 && !r.recommendation.contains("SAT") && !r.recommendation.contains("RİSK"))twoWeek.add(r);
            if(dp.contains(r.symbol) && r.score>=1.5 && !r.recommendation.contains("SAT"))div.add(r);
        }
        basket("1 • HIZLI 1–3 GÜN",33333,fast,GREEN,"Güçlü momentum + hacim + kısa trend.");
        basket("2 • 4–10 İŞLEM GÜNÜ",33333,twoWeek,NAVY2,"Daha dengeli Pulse skoru; en fazla yaklaşık iki hafta.");
        basket("3 • TEMETTÜ + TEKNİK",33334,div,PURPLE,"Temettü geçmişi güçlü şirket havuzu içinden mevcut teknik görünümü zayıf olmayanlar.");
    }

    private void basket(String title,int budget,List<RadarItem> xs,int color,String note) {
        TextView h=bold(title+"  •  "+budget+" TL",18,Color.WHITE);h.setBackgroundColor(color);h.setPadding(dp(12),dp(12),dp(12),dp(12));content.addView(h);
        content.addView(txt(note,13,Color.DKGRAY));
        int n=Math.min(4,xs.size());
        if(n==0){content.addView(txt("Şu an filtreden geçen aday yok; nakitte bekleme sonucu üretildi.",14,RED));spacer(8);return;}
        int per=budget/n;
        for(int i=0;i<n;i++){
            RadarItem r=xs.get(i);int lots=Math.max(0,(int)Math.floor(per/r.price));
            LinearLayout c=card();c.addView(bold(r.symbol+"  •  "+r.recommendation,17,color));
            c.addView(txt(money(r.price)+"  •  yaklaşık "+lots+" lot  •  Pulse "+fmt(r.score)+"  •  Güven %"+(int)r.confidence,13,Color.DKGRAY));
            Button d=button("Grafik / Tavsiye",color);c.addView(d);d.setOnClickListener(v->analyzeStock(r.symbol));content.addView(c);spacer(5);
        }
        spacer(6);
    }

    private void savePortfolio() {
        JSONArray a=new JSONArray();try{for(Holding h:holdings){JSONObject o=new JSONObject();o.put("s",h.symbol);o.put("q",h.qty);o.put("c",h.cost);a.put(o);}}catch(Exception ignored){}
        getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("portfolio",a.toString()).apply();
    }

    private void loadPortfolio() {
        holdings.clear();try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("portfolio","[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);holdings.add(new Holding(o.getString("s"),o.getInt("q"),o.getDouble("c")));}}catch(Exception ignored){}
    }

    private void saveRadarCache() {
        JSONArray a=new JSONArray();try{int n=Math.min(80,radarResults.size());for(int i=0;i<n;i++){RadarItem r=radarResults.get(i);JSONObject o=new JSONObject();o.put("s",r.symbol);o.put("r",r.recommendation);o.put("w",r.why);o.put("h",r.horizon);o.put("p",r.price);o.put("sc",r.score);o.put("cf",r.confidence);a.put(o);}}catch(Exception ignored){}
        getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("radar",a.toString()).apply();
    }

    private void loadRadarCache() {
        radarResults.clear();try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("radar","[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);ShortPulseEngine.Result pr=new ShortPulseEngine.Result();pr.recommendation=o.getString("r");pr.explanation=o.getString("w");pr.horizonText=o.getString("h");pr.price=o.getDouble("p");pr.score=o.getDouble("sc");pr.confidence=o.getDouble("cf");radarResults.add(new RadarItem(o.getString("s"),pr));}}catch(Exception ignored){}
    }

    private String money(double x){return String.format(Locale.US,"%.2f ₺",x);} private String fmt(double x){return String.format(Locale.US,"%.2f",x);}
}
