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
import android.widget.HorizontalScrollView;
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
    private final ExecutorService io = Executors.newFixedThreadPool(5);
    private final List<Holding> holdings = new ArrayList<>();
    private final Map<String, ShortPulseEngine.Result> holdingSignals = new java.util.concurrent.ConcurrentHashMap<>();
    private final Map<String, CatalystContextEngine.Result> holdingContexts = new java.util.concurrent.ConcurrentHashMap<>();
    private volatile boolean portfolioRefreshing=false;
    private final List<RadarItem> radarResults = Collections.synchronizedList(new ArrayList<>());
    private final List<RadarItem> scanBuffer = Collections.synchronizedList(new ArrayList<>());
    private volatile boolean scanRunning=false;
    private int detailTimeframe=5; // default: 1 gün
    private String detailSymbol="";
    private ShortPulseEngine.Result detailResult=null;
    private CatalystContextEngine.Result detailContext=null;
    private final AtomicInteger scanDone=new AtomicInteger(0), scanFailed=new AtomicInteger(0);

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
        TextView brand=bold("BORSA RADAR",23,Color.WHITE); brand.setPadding(0,0,0,0); head.addView(brand);
        TextView sub=txt(page,13,Color.rgb(190,207,224)); sub.setPadding(0,2,0,0); head.addView(sub); root.addView(head);
        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL);
        Button home=button("Ana Sayfa",NAVY2), markets=button("Piyasalar",PURPLE), r=button("Radar",GREEN), p=button("Portföy",NAVY2), more=button("Diğer",AMBER);
        nav.addView(home,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(markets,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(r,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(p,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(more,new LinearLayout.LayoutParams(0,-2,1));
        home.setOnClickListener(v->showDashboard()); markets.setOnClickListener(v->singleStockDialog()); r.setOnClickListener(v->showRadar()); p.setOnClickListener(v->showPortfolio()); more.setOnClickListener(v->showBaskets()); root.addView(nav);
        ScrollView sv=new ScrollView(this); content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(10),dp(8),dp(10),dp(14)); sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));
        TextView foot=txt("BorsaRadar • teknik + haber/katalizör bağlamı",11,Color.rgb(100,110,124)); foot.setGravity(Gravity.CENTER); root.addView(foot); setContentView(root);
    }

    private void showDashboard() {
        shell("Ana Sayfa");
        LinearLayout hero=card();hero.addView(bold("Piyasa kontrol merkezi",20,NAVY));hero.addView(txt("Portföy, BIST radar ve 3 strateji tek akışta.",13,Color.DKGRAY));if(scanRunning){ProgressBar scanBar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);scanBar.setMax(ALL_SYMBOLS.length);scanBar.setProgress(scanDone.get());hero.addView(scanBar);hero.addView(txt("BIST taraması "+scanDone.get()+"/"+ALL_SYMBOLS.length+"  •  başarısız "+scanFailed.get(),12,Color.GRAY));}
        LinearLayout row=new LinearLayout(this);Button radar=button(scanRunning?"Tarama sürüyor":"BIST Radarı",GREEN),portfolio=button("Portföyüm",NAVY2),baskets=button("3 Sepet",PURPLE);row.addView(radar,new LinearLayout.LayoutParams(0,-2,1));row.addView(portfolio,new LinearLayout.LayoutParams(0,-2,1));row.addView(baskets,new LinearLayout.LayoutParams(0,-2,1));hero.addView(row);radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());baskets.setOnClickListener(v->showBaskets());content.addView(hero);spacer(7);
        LinearLayout status=card();status.addView(bold("Durum",17,NAVY));int buy=0,risk=0;for(RadarItem x:new ArrayList<>(radarResults)){if(x.recommendation.contains("AL"))buy++;if(x.recommendation.contains("SAT")||x.recommendation.contains("RİSK"))risk++;}status.addView(txt("Portföy: "+holdings.size()+" pozisyon  •  Radar: "+radarResults.size()+" sonuç"+(scanRunning?"  •  tarama sürüyor":""),13,Color.DKGRAY));if(!radarResults.isEmpty())status.addView(txt("Radar özeti: "+buy+" AL adayı  •  "+risk+" risk/sat",13,Color.DKGRAY));long rt=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("radar_ts",0),pt=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("portfolio_ts",0);if(rt>0)status.addView(txt("Radar güncelleme: "+new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(rt)),12,Color.GRAY));if(pt>0)status.addView(txt("Portföy güncelleme: "+new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(pt)),12,Color.GRAY));content.addView(status);spacer(7);
        if(!radarResults.isEmpty()){List<RadarItem> top=new ArrayList<>(radarResults);top.sort((a,b)->Double.compare(b.score,a.score));int n=Math.min(3,top.size());LinearLayout picks=card();picks.addView(bold("Radar ilk 3",17,NAVY));for(int i=0;i<n;i++){RadarItem x=top.get(i);Button pick=button((i+1)+". "+x.symbol+" • "+x.recommendation+" • %"+(int)x.confidence,x.recommendation.contains("AL")?GREEN:AMBER);picks.addView(pick);pick.setOnClickListener(v->analyzeStock(x.symbol));}content.addView(picks);spacer(7);}LinearLayout quick=new LinearLayout(this);Button stock=button("Tek Hisse Analizi",AMBER),refreshP=button(portfolioRefreshing?"Portföy yenileniyor":"Portföyü Güncelle",NAVY2);quick.addView(stock,new LinearLayout.LayoutParams(0,-2,1));quick.addView(refreshP,new LinearLayout.LayoutParams(0,-2,1));content.addView(quick);stock.setOnClickListener(v->singleStockDialog());refreshP.setEnabled(!portfolioRefreshing&&!holdings.isEmpty());refreshP.setOnClickListener(v->refreshPortfolio());
    }

    private void showPortfolio() {
        shell("Portföyüm");
        LinearLayout actions=new LinearLayout(this); Button add=button("+ Hisse Ekle",GREEN), refresh=button("Tümünü Güncelle",NAVY2);
        actions.addView(add,new LinearLayout.LayoutParams(0,-2,1)); actions.addView(refresh,new LinearLayout.LayoutParams(0,-2,1)); content.addView(actions);
        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setEnabled(!portfolioRefreshing); refresh.setText(portfolioRefreshing?"Güncelleniyor…":"Tümünü Güncelle"); refresh.setOnClickListener(v->refreshPortfolio()); spacer(8); long pts=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("portfolio_ts",0); if(pts>0)content.addView(txt("Son portföy güncellemesi: "+new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(pts)),12,Color.GRAY));
        if(holdings.isEmpty()) { LinearLayout c=card(); c.addView(bold("Portföy boş",19,NAVY)); c.addView(txt("Hisse ekleyince maliyet, güncel fiyat, teknik görünüm ve haber/katalizör bağlamı burada görünür.",14,Color.DKGRAY)); content.addView(c); return; }
        renderPortfolioSummary();
        for(Holding h:new ArrayList<>(holdings)) renderHolding(h);
    }

    private void renderPortfolioSummary(){
        double tlValue=0,tlCost=0,eurValue=0,eurCost=0,usdValue=0,usdCost=0;int priced=0,positive=0,negative=0;
        for(Holding h:new ArrayList<>(holdings)){
            ShortPulseEngine.Result s=holdingSignal(h.symbol);
            if(s==null||s.price<=0)continue;
            MarketDataService.Spot live=MarketDataService.latestSpot(h.symbol);double current=live!=null&&live.price>0?live.price:s.price;
            String n=MarketDataService.normalizeSymbol(h.symbol);double v=current*h.qty,k=h.cost*h.qty;
            if(n.endsWith(".IS")){tlValue+=v;tlCost+=k;}else if(n.endsWith(".DE")){eurValue+=v;eurCost+=k;}else{usdValue+=v;usdCost+=k;}
            priced++;if(current>=h.cost)positive++;else negative++;
        }
        LinearLayout box=card();box.addView(bold("Portföy özeti",18,NAVY));
        if(priced==0)box.addView(txt("Güncel toplam değer için Tümünü Güncelle'ye bas.",13,Color.GRAY));
        else{
            if(tlValue>0)addMarketSummary(box,"BIST",tlValue,tlCost,"₺");
            if(eurValue>0)addMarketSummary(box,"Avrupa",eurValue,eurCost,"€");
            if(usdValue>0){double rate=CurrencyService.usdToEur();if(Double.isFinite(rate))addMarketSummary(box,"ABD",usdValue*rate,usdCost*rate,"€");else addMarketSummary(box,"ABD",usdValue,usdCost,"$");}
            box.addView(txt("Fiyatlanan "+priced+"/"+holdings.size()+"  •  Artıda "+positive+"  •  Ekside "+negative,12,Color.DKGRAY));
        }
        content.addView(box);spacer(7);
    }

    private void addMarketSummary(LinearLayout box,String label,double value,double cost,String currency){
        double pnl=value-cost,pct=cost>0?pnl/cost*100:0;
        box.addView(bold(label+"  "+fmt(value)+" "+currency+"  •  P/L "+(pnl>=0?"+":"")+fmt(pnl)+" "+currency+"  •  "+String.format(Locale.US,"%+.2f%%",pct),15,pnl>=0?GREEN:RED));
    }

    private void renderHolding(Holding h) {
        LinearLayout c=card(); c.addView(bold(h.symbol+"  •  "+h.qty+" lot",20,NAVY)); c.addView(txt("Ortalama maliyet  "+money(h.cost,h.symbol),14,Color.DKGRAY));
        ShortPulseEngine.Result s=holdingSignal(h.symbol);
        if(s==null) c.addView(txt("Güncel değerlendirme için 'Tümünü Güncelle'ye bas.",13,Color.GRAY));
        else {
            MarketDataService.Spot live=MarketDataService.latestSpot(h.symbol); double current=live!=null&&live.price>0?live.price:s.price;
            double pnl=(current-h.cost)*h.qty, pct=h.cost>0?(current/h.cost-1)*100:0;
            c.addView(bold("Son  "+money(current,h.symbol)+"   P/L  "+money(pnl,h.symbol)+"  (%"+fmt(pct)+")",16,pnl>=0?GREEN:RED)); c.addView(txt("Pozisyon değeri  "+money(current*h.qty,h.symbol)+(live!=null?"  •  "+live.source:""),13,Color.DKGRAY)); c.addView(signalBanner(s)); c.addView(txt(s.explanation,13,Color.DKGRAY));
            CatalystContextEngine.Result cx=holdingContext(h.symbol); if(cx!=null)c.addView(contextBanner(cx));
            c.addView(txt("Hedef süre: "+s.horizonText+"  •  Güven %"+(int)s.confidence+"  •  Stop ref. "+money(s.stopReference,h.symbol),13,NAVY2));RadarItem radar=findRadarItem(h.symbol);if(radar!=null)c.addView(txt("Radar sıralaması: "+radar.recommendation+" • Pulse "+fmt(radar.score),12,NAVY2));
        }
        LinearLayout row=new LinearLayout(this); Button detail=button("Grafik / Tavsiye",NAVY2), edit=button("Düzenle",AMBER), del=button("Sil",RED);
        row.addView(detail,new LinearLayout.LayoutParams(0,-2,1.2f)); row.addView(edit,new LinearLayout.LayoutParams(0,-2,1)); row.addView(del,new LinearLayout.LayoutParams(0,-2,.7f)); c.addView(row);
        detail.setOnClickListener(v->{ShortPulseEngine.Result cached=holdingSignal(h.symbol);if(cached!=null)detailResult=cached;CatalystContextEngine.Result cc=holdingContext(h.symbol);if(cc!=null)detailContext=cc;analyzeStock(h.symbol);}); edit.setOnClickListener(v->portfolioDialog(h,h.symbol)); del.setOnClickListener(v->{String n=MarketDataService.normalizeSymbol(h.symbol);holdings.remove(h);holdingSignals.keySet().removeIf(k->MarketDataService.normalizeSymbol(k).equals(n));holdingContexts.keySet().removeIf(k->MarketDataService.normalizeSymbol(k).equals(n));savePortfolio();showPortfolio();}); content.addView(c); spacer(8);
    }

    private TextView signalBanner(ShortPulseEngine.Result s) {
        int color=s.recommendation.contains("SAT")||s.recommendation.contains("RİSK")||s.recommendation.contains("KOVALAMA")?RED:s.recommendation.contains("AL")?GREEN:AMBER;
        String confidence=s.confidence>=75?"Yüksek güven":s.confidence>=55?"Orta güven":"Düşük güven"; TextView v=bold(s.recommendation+"  •  Pulse "+fmt(s.score)+"\\n"+confidence+"  •  "+s.horizonText,18,Color.WHITE); v.setGravity(Gravity.CENTER); v.setBackgroundColor(color); v.setPadding(dp(12),dp(10),dp(12),dp(10)); return v;
    }

    private TextView contextBanner(CatalystContextEngine.Result c) {
        int color=!c.hasContext?Color.GRAY:c.technicalConflict?PURPLE:c.positiveCatalyst?GREEN:c.negativeCatalyst?RED:AMBER;
        String title=!c.hasContext?"BAĞLAM VERİSİ YETERSİZ":c.technicalConflict?"TEKNİK / HABER ÇELİŞKİSİ":c.positiveCatalyst?"POZİTİF KATALİZÖR":c.negativeCatalyst?"NEGATİF KATALİZÖR":"HABER BAĞLAMI NÖTR";
        TextView v=bold(title+"  •  Haber "+fmt(c.newsScore)+"/8\\n"+c.note+"\\n"+c.coverage,14,Color.WHITE); v.setBackgroundColor(color); v.setPadding(dp(12),dp(10),dp(12),dp(10)); return v;
    }

    private void refreshPortfolio() {
        if(holdings.isEmpty()){Toast.makeText(this,"Önce hisse ekle",Toast.LENGTH_SHORT).show();return;}
        if(portfolioRefreshing)return;
        portfolioRefreshing=true;
        final List<Holding> snapshot=new ArrayList<>(holdings);
        shell("Portföy güncelleniyor");
        ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(snapshot.size());content.addView(bar);
        TextView st=txt("0/"+snapshot.size(),15,NAVY);content.addView(st);
        final java.util.concurrent.atomic.AtomicInteger done=new java.util.concurrent.atomic.AtomicInteger(0);
        for(Holding h:snapshot)io.execute(()->{
            try{
                String key=MarketDataService.normalizeSymbol(h.symbol);
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(key,"1mo");
                ShortPulseEngine.Result signal=ShortPulseEngine.analyze(d);
                holdingSignals.put(key,signal);
                io.execute(()->{try{CatalystContextEngine.Result cx=CatalystContextEngine.analyze(key,signal.score);if(cx!=null)holdingContexts.put(key,cx);}catch(Exception ignored){}});
            }catch(Exception ignored){}
            int finished=done.incrementAndGet();
            main.post(()->{
                bar.setProgress(finished);st.setText(finished+"/"+snapshot.size());
                if(finished>=snapshot.size()){
                    portfolioRefreshing=false;
                    getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putLong("portfolio_ts",System.currentTimeMillis()).apply();
                    showPortfolio();
                }
            });
        });
    }

    private void portfolioDialog(Holding edit,String preset) {
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(6),dp(18),0);
        AutoCompleteTextView sym=new AutoCompleteTextView(this); sym.setHint("Hisse kodu / şirket adı"); sym.setThreshold(1); sym.setSingleLine(true);
        List<String> choices=new ArrayList<>(); choices.addAll(Arrays.asList(BistUniverse.ENTRIES)); choices.addAll(Arrays.asList(GlobalStockUniverse.USA)); choices.addAll(Arrays.asList(GlobalStockUniverse.GERMANY));
        sym.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,choices));
        EditText qty=new EditText(this); qty.setHint("Lot/Adet"); qty.setInputType(InputType.TYPE_CLASS_NUMBER); EditText cost=new EditText(this); cost.setHint("Alış fiyatı"); cost.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);
        if(edit!=null){sym.setText(edit.symbol,false);qty.setText(String.valueOf(edit.qty));cost.setText(String.valueOf(edit.cost));} else if(preset!=null)sym.setText(preset,false); box.addView(sym);box.addView(qty);box.addView(cost);
        new AlertDialog.Builder(this).setTitle(edit==null?"Portföye ekle":"Pozisyonu düzenle").setView(box).setPositiveButton("Kaydet",(d,w)->{
            try{String raw=sym.getText().toString().trim().toUpperCase(Locale.ROOT); String s=parseSymbol(raw); if(s.length()<2)throw new Exception(); int q=Integer.parseInt(qty.getText().toString()); double c=Double.parseDouble(cost.getText().toString().replace(',','.')); if(q<=0||c<=0)throw new Exception(); if(edit==null){Holding existing=findHolding(s);if(existing==null)holdings.add(new Holding(s,q,c));else{int total=existing.qty+q;existing.cost=(existing.cost*existing.qty+c*q)/total;existing.qty=total;}}else{Holding collision=findHolding(s);if(collision!=null&&collision!=edit){int total=collision.qty+q;collision.cost=(collision.cost*collision.qty+c*q)/total;collision.qty=total;holdings.remove(edit);}else{edit.symbol=s;edit.qty=q;edit.cost=c;}} savePortfolio();warmPortfolioSignal(s);showPortfolio();}catch(Exception ex){Toast.makeText(this,"Hisse / adet / fiyatı kontrol et",Toast.LENGTH_LONG).show();}
        }).setNegativeButton("İptal",null).show();
    }

    private void warmPortfolioSignal(String symbol){
        final String s=MarketDataService.normalizeSymbol(symbol);
        List<MarketDataService.Candle> cached=MarketDataService.cachedSeries(s,"1mo","1d");
        if(cached!=null&&cached.size()>=15)try{holdingSignals.put(s,ShortPulseEngine.analyze(cached));}catch(Exception ignored){}
        io.execute(()->{try{List<MarketDataService.Candle>d=MarketDataService.fetchDaily(s,"1mo");ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);holdingSignals.put(s,r);CatalystContextEngine.Result cx=null;try{cx=CatalystContextEngine.analyze(s,r.score);}catch(Exception ignored){}if(cx!=null)holdingContexts.put(s,cx);main.post(()->{if(findHolding(s)!=null)showPortfolio();});}catch(Exception ignored){}});
    }

    private String parseSymbol(String raw){
        if(raw==null)return ""; String s=raw.trim(); int cut=s.indexOf(" • "); if(cut>0)s=s.substring(0,cut).trim(); if(MarketDataService.isGlobalSymbol(s))return s; return BistUniverse.symbolFromEntry(s);
    }

    private void showRadar() {
        shell("Tüm Borsa İstanbul Radarı"); LinearLayout top=card(); top.addView(bold("Tüm hisseler • hafif tarama",19,NAVY)); top.addView(txt("İlk tarama teknik olarak hızlı yapılır. Haber/katalizör bağlamı detay açıldığında yüklenir; böylece yüzlerce gereksiz ağ isteği yapılmaz.",13,Color.DKGRAY));
        Button scan=button(scanRunning?"Tarama devam ediyor…":"Tüm BIST'i Tara",GREEN); if(!radarResults.isEmpty()&&!scanRunning)top.addView(txt("Mevcut sonuçlar korunur; yeni tarama yalnızca tamamlandığında listeyi yeniler.",12,Color.GRAY)); top.addView(scan); scan.setEnabled(!scanRunning); scan.setOnClickListener(v->scanRadar()); content.addView(top); spacer(8);
        if(scanRunning){int done=scanDone.get(),failed=scanFailed.get();ProgressBar pb=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);pb.setMax(ALL_SYMBOLS.length);pb.setProgress(done);content.addView(pb);content.addView(txt(done+"/"+ALL_SYMBOLS.length+" • başarısız "+failed,14,NAVY));}
        if(!radarResults.isEmpty()){List<RadarItem> snap=new ArrayList<>(radarResults);snap.sort((a,b)->Double.compare(b.score,a.score));LinearLayout summary=card();long radarTs=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("radar_ts",0);String radarAge=radarTs>0?new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(radarTs)):"önbellek";summary.addView(bold("Son tarama • "+snap.size()+" hisse",16,NAVY));summary.addView(txt("Güncelleme: "+radarAge+(scanRunning?" • yeni tarama sürüyor":""),12,Color.GRAY));int buy=0,hold=0,risk=0;for(RadarItem x:snap){if(x.recommendation.contains("AL"))buy++;else if(x.recommendation.contains("SAT")||x.recommendation.contains("RİSK"))risk++;else hold++;}summary.addView(txt("AL "+buy+"  •  TUT/İZLE "+hold+"  •  SAT/RİSK "+risk,13,Color.DKGRAY));Button baskets=button("3 Sepet Stratejisini Aç",PURPLE);summary.addView(baskets);baskets.setOnClickListener(v->showBaskets());content.addView(summary);spacer(6);renderRadarList(snap,30);}else content.addView(txt("Henüz radar sonucu yok.",14,Color.GRAY));
    }

    private void scanRadar() {
        if(scanRunning)return;
        scanRunning=true; scanDone.set(0); scanFailed.set(0); scanBuffer.clear();
        showRadar();
        for(String sym:ALL_SYMBOLS)io.execute(()->{
            try{
                List<MarketDataService.Candle>d=MarketDataService.fetchDaily(sym,"1mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);
                scanBuffer.add(new RadarItem(sym,r));
            }catch(Exception e){scanFailed.incrementAndGet();}
            int done=scanDone.incrementAndGet();
            if(done>=ALL_SYMBOLS.length){
                List<RadarItem> sorted;
                synchronized(scanBuffer){sorted=new ArrayList<>(scanBuffer);}
                sorted.sort((x,y)->Double.compare(y.score,x.score));
                if(!sorted.isEmpty()){synchronized(radarResults){radarResults.clear();radarResults.addAll(sorted);}saveRadarCache();getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putLong("radar_ts",System.currentTimeMillis()).apply();}
                scanRunning=false;main.post(()->{if(sorted.isEmpty())Toast.makeText(this,"Yeni tarama sonuç üretmedi; önceki radar sonuçları korundu.",Toast.LENGTH_LONG).show();showRadar();});
            }else if(done%50==0)main.post(this::showRadar);
        });
    }

    private void renderRadarList(List<RadarItem> items,int max) {
        items.sort((a,b)->Double.compare(b.score,a.score)); content.addView(bold("En güçlü adaylar",18,NAVY)); int n=Math.min(max,items.size());
        for(int i=0;i<n;i++){RadarItem r=items.get(i);LinearLayout c=card();int col=r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:r.recommendation.contains("AL")?GREEN:AMBER;LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);LinearLayout left=new LinearLayout(this);left.setOrientation(LinearLayout.VERTICAL);left.addView(bold((i+1)+". "+r.symbol,18,NAVY));left.addView(txt(r.recommendation+"  •  Pulse "+fmt(r.score),14,col));LinearLayout right=new LinearLayout(this);right.setOrientation(LinearLayout.VERTICAL);right.setGravity(Gravity.END);right.addView(bold(money(r.price,r.symbol),17,col));right.addView(txt("Güven %"+(int)r.confidence,12,Color.GRAY));row.addView(left,new LinearLayout.LayoutParams(0,-2,1));row.addView(right,new LinearLayout.LayoutParams(-2,-2));c.addView(row);c.addView(txt(r.horizon+"  •  "+r.why,12,Color.GRAY));LinearLayout actions=new LinearLayout(this);Button d=button("Grafik / Detay",NAVY2),add=button(findHolding(r.symbol)==null?"Portföye Ekle":"Portföyde",findHolding(r.symbol)==null?GREEN:AMBER);actions.addView(d,new LinearLayout.LayoutParams(0,-2,1));actions.addView(add,new LinearLayout.LayoutParams(0,-2,1));c.addView(actions);d.setOnClickListener(v->analyzeStock(r.symbol));add.setOnClickListener(v->portfolioDialog(findHolding(r.symbol),r.symbol));content.addView(c);spacer(6);}
    }

    private void singleStockDialog() {
        AutoCompleteTextView s=new AutoCompleteTextView(this);s.setHint("Örn. KTLEV, THYAO, NVDA, S92");s.setThreshold(1);List<String>choices=new ArrayList<>();choices.addAll(Arrays.asList(BistUniverse.ENTRIES));choices.addAll(Arrays.asList(GlobalStockUniverse.USA));choices.addAll(Arrays.asList(GlobalStockUniverse.GERMANY));s.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,choices));
        new AlertDialog.Builder(this).setTitle("Tek hisse analiz").setView(s).setPositiveButton("Analiz et",(d,w)->{String sym=parseSymbol(s.getText().toString().trim().toUpperCase(Locale.ROOT));if(sym.length()>=2)analyzeStock(sym);}).setNegativeButton("İptal",null).show();
    }

    private void analyzeStock(String symbol) { analyzeStock(symbol,detailTimeframe); }

    private void analyzeStock(String symbol,int timeframe) {
        if(symbol==null||symbol.trim().length()<2){Toast.makeText(this,"Geçerli hisse seç",Toast.LENGTH_SHORT).show();return;}
        symbol=parseSymbol(symbol.toUpperCase(Locale.ROOT));
        boolean sameSymbol=symbol.equals(detailSymbol);
        detailSymbol=symbol;
        detailTimeframe=ChartTimeframes.clamp(timeframe);
        if(!sameSymbol){detailResult=null;detailContext=null;}
        final String selectedSymbol=symbol;
        final int selectedTimeframe=detailTimeframe;
        shell(selectedSymbol+" • analiz");
        boolean instantRendered=false;
        List<MarketDataService.Candle> instantChart=DetailedChartController.cached(selectedSymbol,selectedTimeframe);
        if(sameSymbol && detailResult!=null && instantChart!=null && instantChart.size()>=2){
            renderStockDetail(selectedSymbol,detailResult,detailContext,instantChart);
            instantRendered=true;
        }
        if(!instantRendered){
            List<MarketDataService.Candle> instantAnalysis=MarketDataService.cachedSeries(selectedSymbol,"1mo","1d");
            if(instantAnalysis!=null && instantAnalysis.size()>=15){
                try{
                    ShortPulseEngine.Result cachedResult=ShortPulseEngine.analyze(instantAnalysis);
                    detailResult=cachedResult;
                    List<MarketDataService.Candle> shownChart=instantChart!=null&&instantChart.size()>=2?instantChart:instantAnalysis;
                    renderStockDetail(selectedSymbol,cachedResult,sameSymbol?detailContext:null,shownChart);
                    instantRendered=true;
                }catch(Exception ignored){}
            }
        }
        if(!instantRendered)content.addView(txt("Fiyat ve teknik görünüm yükleniyor…",15,NAVY));
        final boolean hadInstant=instantRendered;
        io.execute(()->{
            try{
                // Hızlı ilk çizim: yalnızca kısa günlük seri. Haber ve seçili grafik bekletmez.
                List<MarketDataService.Candle> base=MarketDataService.fetchDaily(selectedSymbol,"1mo");
                ShortPulseEngine.Result r=ShortPulseEngine.analyze(base);
                detailResult=r;
                prefetchAdjacent(selectedSymbol);
                if(!hadInstant)main.post(()->{if(selectedSymbol.equals(detailSymbol) && selectedTimeframe==detailTimeframe)renderStockDetail(selectedSymbol,r,null,base);});

                // Ağır verileri ekran açıldıktan sonra arka planda tamamla.
                io.execute(()->{
                    try{
                        CatalystContextEngine.Result cx=selectedSymbol.equals(detailSymbol)?detailContext:null;
                        if(cx==null)try{cx=CatalystContextEngine.analyze(selectedSymbol,r.score);}catch(Exception ignored){cx=null;}
                        List<MarketDataService.Candle> chart;
                        chart=DetailedChartController.cached(selectedSymbol,selectedTimeframe);
                        if(chart==null||chart.size()<2)try{chart=DetailedChartController.fetch(selectedSymbol,selectedTimeframe);}catch(Exception ignored){chart=base;}
                        final CatalystContextEngine.Result safeCx=cx;
                        final List<MarketDataService.Candle> safeChart=chart;
                        if(selectedSymbol.equals(detailSymbol))detailContext=safeCx;
                        main.post(()->{
                            if(selectedSymbol.equals(detailSymbol) && selectedTimeframe==detailTimeframe)
                                renderStockDetail(selectedSymbol,r,safeCx,safeChart);
                        });
                    }catch(Exception ignored){}
                });
            }catch(Exception e){
                main.post(()->{if(selectedSymbol.equals(detailSymbol) && selectedTimeframe==detailTimeframe){shell(selectedSymbol+" • analiz");content.addView(txt("Veri alınamadı: "+e.getMessage(),15,RED));}});
            }
        });
    }

    private Holding findHolding(String symbol){String n=MarketDataService.normalizeSymbol(symbol);for(Holding h:holdings)if(MarketDataService.normalizeSymbol(h.symbol).equals(n))return h;return null;}
    private ShortPulseEngine.Result holdingSignal(String symbol){String n=MarketDataService.normalizeSymbol(symbol);ShortPulseEngine.Result r=holdingSignals.get(n);if(r!=null)return r;for(Map.Entry<String,ShortPulseEngine.Result> e:holdingSignals.entrySet())if(MarketDataService.normalizeSymbol(e.getKey()).equals(n))return e.getValue();return null;}
    private CatalystContextEngine.Result holdingContext(String symbol){String n=MarketDataService.normalizeSymbol(symbol);CatalystContextEngine.Result r=holdingContexts.get(n);if(r!=null)return r;for(Map.Entry<String,CatalystContextEngine.Result> e:holdingContexts.entrySet())if(MarketDataService.normalizeSymbol(e.getKey()).equals(n))return e.getValue();return null;}
    private RadarItem findRadarItem(String symbol){String n=MarketDataService.normalizeSymbol(symbol);synchronized(radarResults){for(RadarItem x:radarResults)if(MarketDataService.normalizeSymbol(x.symbol).equals(n))return x;}return null;}

    private void renderStockDetail(String symbol,ShortPulseEngine.Result r,CatalystContextEngine.Result cx,List<MarketDataService.Candle> chart) {
        shell(symbol+" • "+ChartTimeframes.label(detailTimeframe)); Holding owned=findHolding(symbol); RadarItem radarHit=findRadarItem(symbol); LinearLayout q=card(); LinearLayout head=new LinearLayout(this);head.setGravity(Gravity.CENTER_VERTICAL); LinearLayout left=new LinearLayout(this);left.setOrientation(LinearLayout.VERTICAL);left.addView(bold(symbol,22,NAVY));left.addView(txt(ChartTimeframes.label(detailTimeframe)+" grafik • "+r.horizonText,12,Color.GRAY)); MarketDataService.Spot live=MarketDataService.latestSpot(symbol); double shownPrice=live!=null&&live.price>0?live.price:r.price; LinearLayout right=new LinearLayout(this);right.setOrientation(LinearLayout.VERTICAL);right.setGravity(Gravity.END);right.addView(bold(money(shownPrice,symbol),25,r.changePct>=0?GREEN:RED));right.addView(txt((r.changePct>=0?"+":"")+fmt(r.changePct)+"%",14,r.changePct>=0?GREEN:RED));head.addView(left,new LinearLayout.LayoutParams(0,-2,1));head.addView(right,new LinearLayout.LayoutParams(-2,-2));q.addView(head); if(live!=null)q.addView(txt("Fiyat kaynağı: "+live.source,11,Color.GRAY));q.addView(txt("ATR% "+fmt(r.atrPct)+"  •  RelVol x"+fmt(r.relativeVolume)+"  •  Güven %"+(int)r.confidence,13,Color.DKGRAY)); if(owned!=null){double pnl=(shownPrice-owned.cost)*owned.qty,pct=owned.cost>0?(shownPrice/owned.cost-1)*100:0;q.addView(txt("Portföy: "+owned.qty+" adet • Maliyet "+money(owned.cost,symbol)+" • P/L "+money(pnl,symbol)+" ("+String.format(Locale.US,"%+.2f%%",pct)+")",13,pnl>=0?GREEN:RED));} if(radarHit!=null)q.addView(txt("Radar: "+radarHit.recommendation+" • Pulse "+fmt(radarHit.score)+" • Güven %"+(int)radarHit.confidence,12,NAVY2));content.addView(q);spacer(7);
        content.addView(signalBanner(r));spacer(7); if(cx!=null){content.addView(contextBanner(cx));spacer(7);}
        HorizontalScrollView tfScroll=new HorizontalScrollView(this); LinearLayout tfRow=new LinearLayout(this); tfRow.setOrientation(LinearLayout.HORIZONTAL);
        for(int i=0;i<ChartTimeframes.LABELS.length;i++){final int idx=i;Button b=button(ChartTimeframes.LABELS[i],i==detailTimeframe?GREEN:NAVY2);b.setOnClickListener(v->{if(idx!=detailTimeframe)analyzeStock(symbol,idx);});tfRow.addView(b,new LinearLayout.LayoutParams(dp(82),-2));}
        tfScroll.addView(tfRow);content.addView(tfScroll);spacer(5);
        if(chart==null||chart.size()<2){content.addView(txt("Bu zaman diliminde grafik verisi yetersiz.",14,RED));}else{content.addView(txt(ChartTimeframes.label(detailTimeframe)+" • "+chart.size()+" veri noktası",11,Color.GRAY));content.addView(new PriceChartView(this,chart,ChartTimeframes.label(detailTimeframe).toUpperCase(Locale.ROOT)),new LinearLayout.LayoutParams(-1,dp(340)));}spacer(7);
        LinearLayout info=card();info.addView(bold("Teknik görünüm",17,NAVY));info.addView(txt(r.explanation,14,Color.DKGRAY));LinearLayout metrics=new LinearLayout(this);metrics.setOrientation(LinearLayout.HORIZONTAL);TextView m1=txt("Momentum\\n"+r.momentumText,12,Color.DKGRAY),m2=txt("Hacim/Para\\n"+r.flowText,12,Color.DKGRAY),m3=txt("Trend\\n"+r.trendText,12,Color.DKGRAY);m1.setGravity(Gravity.CENTER);m2.setGravity(Gravity.CENTER);m3.setGravity(Gravity.CENTER);metrics.addView(m1,new LinearLayout.LayoutParams(0,-2,1));metrics.addView(m2,new LinearLayout.LayoutParams(0,-2,1));metrics.addView(m3,new LinearLayout.LayoutParams(0,-2,1));info.addView(metrics);info.addView(txt("Hedef: "+r.horizonText+"  •  Stop ref. "+money(r.stopReference,symbol),13,NAVY2));content.addView(info);
        LinearLayout news=card();news.addView(bold("Bilgi akışı",17,NAVY)); if(cx==null){news.addView(txt("Haber/katalizör verisi arka planda yükleniyor…",14,Color.GRAY));}else{news.addView(txt("Haber skoru: "+fmt(cx.newsScore)+"/8  •  "+cx.dataStatus,14,Color.DKGRAY));news.addView(txt(cx.note,14,cx.technicalConflict?PURPLE:Color.DKGRAY));news.addView(txt("Kapsama: "+cx.coverage,12,Color.GRAY));}content.addView(news);spacer(7);
        LinearLayout actions=new LinearLayout(this); Button prev=button("◀ Önceki",NAVY2), add=button(owned==null?"Portföye Ekle":"Pozisyonu Düzenle",owned==null?GREEN:AMBER), refreshDetail=button("Yenile",NAVY2), next=button("Sonraki ▶",NAVY2);String prevSymbol=adjacentSymbol(symbol,-1),nextSymbol=adjacentSymbol(symbol,1);prev.setEnabled(!prevSymbol.equals(symbol));next.setEnabled(!nextSymbol.equals(symbol));if(!prev.isEnabled())prev.setText("◀ Başlangıç");if(!next.isEnabled())next.setText("Son ▶"); actions.addView(prev,new LinearLayout.LayoutParams(0,-2,1)); actions.addView(add,new LinearLayout.LayoutParams(0,-2,1.15f)); actions.addView(refreshDetail,new LinearLayout.LayoutParams(0,-2,.8f)); actions.addView(next,new LinearLayout.LayoutParams(0,-2,1)); content.addView(actions); prev.setOnClickListener(v->{if(!prevSymbol.equals(symbol))analyzeStock(prevSymbol,detailTimeframe);}); add.setOnClickListener(v->portfolioDialog(owned,symbol)); refreshDetail.setOnClickListener(v->analyzeStock(symbol,detailTimeframe)); next.setOnClickListener(v->{if(!nextSymbol.equals(symbol))analyzeStock(nextSymbol,detailTimeframe);});
    }

    private void showBaskets() {
        shell("100.000 TL • 3 Sepet"); if(radarResults.isEmpty()){LinearLayout c=card();c.addView(bold(scanRunning?"Radar taraması devam ediyor":"Önce radar taraması gerekiyor",18,NAVY));c.addView(txt("Tarama bir kez tamamlanınca sonuç kaydedilir; ekrandan çıksan da kaybolmaz.",13,Color.DKGRAY));Button go=button("Radarı Aç",GREEN);c.addView(go);go.setOnClickListener(v->showRadar());content.addView(c);return;}
        List<RadarItem>all=new ArrayList<>(radarResults);all.sort((a,b)->Double.compare(b.score,a.score));List<RadarItem>fast=new ArrayList<>(),twoWeek=new ArrayList<>(),div=new ArrayList<>();List<String>dp=Arrays.asList(DIVIDEND_POOL);for(RadarItem r:all){if(r.score>=5.2&&r.confidence>=60)fast.add(r);if(r.score>=3.7&&!r.recommendation.contains("SAT")&&!r.recommendation.contains("RİSK"))twoWeek.add(r);if(dp.contains(r.symbol)&&r.score>=1.5&&!r.recommendation.contains("SAT"))div.add(r);}basket("1 • HIZLI 1–3 GÜN",33333,fast,GREEN,"Güçlü momentum + hacim + kısa trend.");basket("2 • 4–10 İŞLEM GÜNÜ",33333,twoWeek,NAVY2,"Daha dengeli Pulse skoru; en fazla yaklaşık iki hafta.");basket("3 • TEMETTÜ + TEKNİK",33334,div,PURPLE,"Temettü geçmişi güçlü şirket havuzu içinden mevcut teknik görünümü zayıf olmayanlar.");
    }

    private void basket(String title,int budget,List<RadarItem>xs,int color,String note){TextView h=bold(title+"  •  "+budget+" TL",18,Color.WHITE);h.setBackgroundColor(color);h.setPadding(dp(12),dp(12),dp(12),dp(12));content.addView(h);content.addView(txt(note,13,Color.DKGRAY));int n=Math.min(4,xs.size());if(n==0){content.addView(txt("Şu an filtreden geçen aday yok; nakitte bekleme sonucu üretildi.",14,RED));spacer(8);return;}int per=budget/n;int used=0;for(int i=0;i<n;i++){RadarItem r=xs.get(i);int lots=Math.max(0,(int)Math.floor(per/r.price));used+=(int)Math.round(lots*r.price);LinearLayout c=card();c.addView(bold(r.symbol+"  •  "+r.recommendation,17,color));c.addView(txt(money(r.price,r.symbol)+"  •  yaklaşık "+lots+" lot  •  Pulse "+fmt(r.score)+"  •  Güven %"+(int)r.confidence,13,Color.DKGRAY));LinearLayout actions=new LinearLayout(this);Button d=button("Grafik / Tavsiye",color),add=button(findHolding(r.symbol)==null?"Portföye Ekle":"Portföyde",findHolding(r.symbol)==null?GREEN:AMBER);actions.addView(d,new LinearLayout.LayoutParams(0,-2,1));actions.addView(add,new LinearLayout.LayoutParams(0,-2,1));c.addView(actions);d.setOnClickListener(v->analyzeStock(r.symbol));add.setOnClickListener(v->portfolioDialog(findHolding(r.symbol),r.symbol));content.addView(c);spacer(5);}content.addView(txt("Yaklaşık kullanım "+used+" TL  •  Nakit "+Math.max(0,budget-used)+" TL",12,Color.GRAY));spacer(6);}

    private void savePortfolio(){JSONArray a=new JSONArray();try{for(Holding h:holdings){JSONObject o=new JSONObject();o.put("s",h.symbol);o.put("q",h.qty);o.put("c",h.cost);a.put(o);}}catch(Exception ignored){}getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("portfolio",a.toString()).apply();}
    private void loadPortfolio(){holdings.clear();try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("portfolio","[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);holdings.add(new Holding(o.getString("s"),o.getInt("q"),o.getDouble("c")));}}catch(Exception ignored){}}
    private void saveRadarCache(){JSONArray a=new JSONArray();try{int n=Math.min(80,radarResults.size());for(int i=0;i<n;i++){RadarItem r=radarResults.get(i);JSONObject o=new JSONObject();o.put("s",r.symbol);o.put("r",r.recommendation);o.put("w",r.why);o.put("h",r.horizon);o.put("p",r.price);o.put("sc",r.score);o.put("cf",r.confidence);a.put(o);}}catch(Exception ignored){}getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("radar",a.toString()).apply();}
    private void loadRadarCache(){radarResults.clear();try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("radar","[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);ShortPulseEngine.Result pr=new ShortPulseEngine.Result();pr.recommendation=o.getString("r");pr.explanation=o.getString("w");pr.horizonText=o.getString("h");pr.price=o.getDouble("p");pr.score=o.getDouble("sc");pr.confidence=o.getDouble("cf");radarResults.add(new RadarItem(o.getString("s"),pr));}}catch(Exception ignored){}}

    private void prefetchAdjacent(String symbol) {
        final int tfIndex=detailTimeframe;
        io.execute(()->{
            for(int d:new int[]{-1,1}){
                if(!symbol.equals(detailSymbol)||tfIndex!=detailTimeframe)return;
                String s=adjacentSymbol(symbol,d);
                if(s.equals(symbol))continue;
                try{
                    List<MarketDataService.Candle> cached=MarketDataService.cachedSeries(s,"1mo","1d");
                    if(cached==null||cached.size()<15)MarketDataService.fetchDaily(s,"1mo");
                    if(!symbol.equals(detailSymbol)||tfIndex!=detailTimeframe)return;
                    List<MarketDataService.Candle> tf=DetailedChartController.cached(s,tfIndex);
                    if(tf==null||tf.size()<2)DetailedChartController.fetch(s,tfIndex);
                }catch(Exception ignored){}
            }
        });
    }

    private String adjacentSymbol(String symbol,int delta) {
        String s=symbol==null?"":symbol.trim().toUpperCase(Locale.ROOT);
        List<String> order=new ArrayList<>();
        synchronized(radarResults){for(RadarItem x:radarResults)if(x!=null&&x.symbol!=null&&!order.contains(x.symbol))order.add(x.symbol);}
        if(order.isEmpty())order.addAll(Arrays.asList(ALL_SYMBOLS));
        int at=order.indexOf(s);
        if(at<0){String n=MarketDataService.normalizeSymbol(s);for(int i=0;i<order.size();i++)if(MarketDataService.normalizeSymbol(order.get(i)).equals(n)){at=i;break;}}
        return at<0?s:order.get(Math.floorMod(at+delta,order.size()));
    }

    private String money(double x,String symbol){String n=MarketDataService.normalizeSymbol(symbol);if(n.endsWith(".IS"))return String.format(Locale.US,"%.2f ₺",x);if(n.endsWith(".DE"))return String.format(Locale.US,"%.2f €",x);double rate=CurrencyService.usdToEur();if(!Double.isFinite(rate))io.execute(CurrencyService::refreshIfNeeded);double shown=Double.isFinite(rate)?x*rate:x;return String.format(Locale.US,"%.2f %s",shown,Double.isFinite(rate)?"€":"$");} private String fmt(double x){return String.format(Locale.US,"%.2f",x);}
}
