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
import java.util.concurrent.atomic.AtomicInteger;

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
    private final ExecutorService io = Executors.newFixedThreadPool(12);
    private final List<Holding> holdings = new ArrayList<>();
    private final Map<String, ShortPulseEngine.Result> holdingSignals = new HashMap<>();
    private final Map<String, CatalystContextEngine.Result> holdingContexts = new HashMap<>();
    private final List<RadarItem> radarResults = Collections.synchronizedList(new ArrayList<>());
    private volatile boolean scanRunning=false;
    private final AtomicInteger scanDone=new AtomicInteger(0), scanFailed=new AtomicInteger(0);

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        loadPortfolio();
        showPortfolio();
    }

    private TextView txt(String s, int sp, int color) { TextView t=new TextView(this); t.setText(s); t.setTextSize(sp); t.setTextColor(color); t.setPadding(14,10,14,10); return t; }
    private TextView bold(String s,int sp,int color){TextView t=txt(s,sp,color);t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    private Button button(String s,int color){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);b.setBackgroundColor(color);return b;}
    private LinearLayout card(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(14,14,14,14);return l;}
    private void spacer(int h){Space s=new Space(this);content.addView(s,new LinearLayout.LayoutParams(1,h));}

    private void shell(String title){
        ScrollView scroll=new ScrollView(this); LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(BG);scroll.addView(root);
        TextView head=bold("BorsaRadar • "+title,22,Color.WHITE);head.setBackgroundColor(NAVY);root.addView(head);
        LinearLayout nav=new LinearLayout(this);Button p=button("Portföy",NAVY2),r=button("Radar",GREEN),m=button("Piyasa",PURPLE);nav.addView(p,new LinearLayout.LayoutParams(0,-2,1));nav.addView(r,new LinearLayout.LayoutParams(0,-2,1));nav.addView(m,new LinearLayout.LayoutParams(0,-2,1));root.addView(nav);
        p.setOnClickListener(v->showPortfolio());r.setOnClickListener(v->showRadar());m.setOnClickListener(v->showMarket());
        content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(12,12,12,30);root.addView(content);setContentView(scroll);
    }

    private void showPortfolio(){
        shell("Portföyüm");LinearLayout actions=new LinearLayout(this);Button add=button("+ Hisse Ekle",GREEN),refresh=button("Güncelle",NAVY2);actions.addView(add,new LinearLayout.LayoutParams(0,-2,1));actions.addView(refresh,new LinearLayout.LayoutParams(0,-2,1));content.addView(actions);add.setOnClickListener(v->portfolioDialog(null,null));refresh.setOnClickListener(v->refreshPortfolio());spacer(8);
        if(holdings.isEmpty()){LinearLayout c=card();c.addView(bold("Portföy boş",19,NAVY));c.addView(txt("Hisselerini eklediğinde güncel sinyal, kâr/zarar ve haber etkisi burada görünür.",14,Color.DKGRAY));content.addView(c);return;}
        for(Holding h:new ArrayList<>(holdings))renderHolding(h);
    }

    private void renderHolding(Holding h){
        LinearLayout c=card();c.addView(bold(h.symbol+" • "+h.qty+" lot",19,NAVY));ShortPulseEngine.Result s=holdingSignals.get(h.symbol);if(s==null)c.addView(txt("Maliyet: "+fmt(h.cost)+" TL • Güncelle ile canlı analiz",14,Color.DKGRAY));else{double pl=(s.price-h.cost)*h.qty,pct=h.cost==0?0:(s.price/h.cost-1)*100;c.addView(txt("Fiyat "+fmt(s.price)+" • Maliyet "+fmt(h.cost)+" • "+(pl>=0?"Kâr ":"Zarar ")+fmt(pl)+" TL ("+fmt(pct)+"%)",14,pl>=0?GREEN:RED));c.addView(bold(s.recommendation+" • skor "+fmt(s.score)+" • güven %"+Math.round(s.confidence*100),16,s.score>=1?GREEN:s.score<=-1?RED:AMBER));c.addView(txt(s.explanation,13,Color.DKGRAY));}CatalystContextEngine.Result ctx=holdingContexts.get(h.symbol);if(ctx!=null)c.addView(txt("Haber/KAP: "+ctx.summary,13,PURPLE));Button edit=button("Düzenle / Sil",NAVY2);edit.setOnClickListener(v->portfolioDialog(h,null));c.addView(edit);content.addView(c);spacer(6);
    }

    private void refreshPortfolio(){
        if(holdings.isEmpty())return;shell("Portföy güncelleniyor");ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(holdings.size());content.addView(bar);TextView st=txt("0/"+holdings.size(),15,NAVY);content.addView(st);AtomicInteger done=new AtomicInteger();
        for(Holding h:new ArrayList<>(holdings))io.execute(()->{try{List<MarketDataService.Candle>d=MarketDataService.fetchDaily(h.symbol,"3mo");ShortPulseEngine.Result sr=ShortPulseEngine.analyze(d);CatalystContextEngine.Result cr=CatalystContextEngine.analyze(h.symbol);synchronized(holdingSignals){holdingSignals.put(h.symbol,sr);holdingContexts.put(h.symbol,cr);}}catch(Exception ignored){}main.post(()->{int n=done.incrementAndGet();bar.setProgress(n);st.setText(n+"/"+holdings.size());if(n>=holdings.size())showPortfolio();});});
    }

    private void portfolioDialog(Holding edit,String preset){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);EditText sym=new EditText(this),qty=new EditText(this),cost=new EditText(this);sym.setHint("Hisse kodu, örn THYAO");qty.setHint("Lot");cost.setHint("Alış fiyatı");qty.setInputType(InputType.TYPE_CLASS_NUMBER);cost.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);if(edit!=null){sym.setText(edit.symbol);qty.setText(String.valueOf(edit.qty));cost.setText(String.valueOf(edit.cost));}else if(preset!=null)sym.setText(preset);box.addView(sym);box.addView(qty);box.addView(cost);AlertDialog.Builder b=new AlertDialog.Builder(this).setTitle(edit==null?"Portföye ekle":"Pozisyonu düzenle").setView(box).setPositiveButton("Kaydet",null).setNegativeButton("Vazgeç",null);if(edit!=null)b.setNeutralButton("Sil",(d,w)->{holdings.remove(edit);savePortfolio();showPortfolio();});AlertDialog d=b.create();d.setOnShowListener(x->d.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{try{String code=norm(sym.getText().toString());int q=Integer.parseInt(qty.getText().toString().trim());double c=Double.parseDouble(cost.getText().toString().trim().replace(',','.'));if(code.isEmpty()||q<=0||c<=0)throw new Exception();if(edit==null)holdings.add(new Holding(code,q,c));else{edit.symbol=code;edit.qty=q;edit.cost=c;}savePortfolio();d.dismiss();showPortfolio();}catch(Exception e){Toast.makeText(this,"Kod, lot ve alış fiyatını kontrol et",Toast.LENGTH_SHORT).show();}}));d.show();
    }

    private void showRadar(){
        shell("BIST Fırsat Radarı");TextView info=txt("Tüm BIST evreni taranır. Önce teknik motor, sonra en güçlü adaylarda haber/KAP doğrulaması yapılır.",14,Color.DKGRAY);content.addView(info);Button scan=button(scanRunning?"Tarama sürüyor…":"Taramayı Başlat",GREEN);scan.setEnabled(!scanRunning);scan.setOnClickListener(v->startScan());content.addView(scan);spacer(8);synchronized(radarResults){for(int i=0;i<Math.min(20,radarResults.size());i++){RadarItem x=radarResults.get(i);LinearLayout c=card();c.addView(bold(x.symbol+" • "+x.recommendation,18,x.score>=1?GREEN:x.score<=-1?RED:AMBER));c.addView(txt("Fiyat "+fmt(x.price)+" • skor "+fmt(x.score)+" • güven %"+Math.round(x.confidence*100),13,Color.DKGRAY));c.addView(txt(x.why,13,Color.DKGRAY));content.addView(c);}}
    }

    private void startScan(){
        if(scanRunning)return;scanRunning=true;scanDone.set(0);scanFailed.set(0);radarResults.clear();shell("BIST taranıyor");ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(ALL_SYMBOLS.length);content.addView(bar);TextView status=txt("0/"+ALL_SYMBOLS.length,15,NAVY);content.addView(status);
        for(String s:ALL_SYMBOLS)io.execute(()->{try{List<MarketDataService.Candle>d=MarketDataService.fetchDaily(s,"3mo");ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);if(r.confidence>=0.48 && r.score>-0.7)radarResults.add(new RadarItem(s,r));}catch(Exception e){scanFailed.incrementAndGet();}finally{int n=scanDone.incrementAndGet();main.post(()->{bar.setProgress(n);status.setText(n+"/"+ALL_SYMBOLS.length+" • hata "+scanFailed.get());if(n>=ALL_SYMBOLS.length)finishScan();});}});
    }

    private void finishScan(){
        synchronized(radarResults){Collections.sort(radarResults,(a,b)->Double.compare(b.score,a.score));}List<RadarItem> top; synchronized(radarResults){top=new ArrayList<>(radarResults.subList(0,Math.min(12,radarResults.size())));}AtomicInteger left=new AtomicInteger(top.size());if(top.isEmpty()){scanRunning=false;showRadar();return;}for(RadarItem r:top)io.execute(()->{try{CatalystContextEngine.Result c=CatalystContextEngine.analyze(r.symbol);r.score+=Math.max(-0.8,Math.min(0.8,c.score*0.22));r.why=r.why+" • "+c.summary;}catch(Exception ignored){}if(left.decrementAndGet()==0)main.post(()->{synchronized(radarResults){Collections.sort(radarResults,(a,b)->Double.compare(b.score,a.score));}scanRunning=false;showRadar();});});
    }

    private void showMarket(){
        shell("Piyasa");content.addView(txt("BIST genel eğilimi, gün içi risk, faiz/petrol/altın ve dış piyasa etkileri karar motoruna eklenir.",14,Color.DKGRAY));Button b=button("BIST100 Rejim Analizi",PURPLE);b.setOnClickListener(v->io.execute(()->{try{List<MarketDataService.Candle>d=MarketDataService.fetchDaily("XU100","6mo");MarketRegimeService.Regime r=MarketRegimeService.classify(d);main.post(()->{shell("Piyasa Rejimi");content.addView(bold(r.label,22,r.riskOff?RED:GREEN));content.addView(txt("Rejim skoru: "+fmt(r.score)+" • "+r.note,15,Color.DKGRAY));});}catch(Exception e){main.post(()->Toast.makeText(this,"Piyasa verisi alınamadı",Toast.LENGTH_SHORT).show());}}));content.addView(b);
    }

    private void savePortfolio(){JSONArray a=new JSONArray();try{for(Holding h:holdings){JSONObject o=new JSONObject();o.put("s",h.symbol);o.put("q",h.qty);o.put("c",h.cost);a.put(o);}}catch(Exception ignored){}getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("portfolio",a.toString()).apply();}
    private void loadPortfolio(){holdings.clear();try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("portfolio","[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);holdings.add(new Holding(o.getString("s"),o.getInt("q"),o.getDouble("c")));}}catch(Exception ignored){}}
    private static String norm(String s){if(s==null)return "";return s.toUpperCase(Locale.ROOT).replace(".IS","").replace(" ","");}
    private static String fmt(double d){return String.format(Locale.US,"%.2f",d);}
    @Override protected void onDestroy(){io.shutdownNow();super.onDestroy();}
}
