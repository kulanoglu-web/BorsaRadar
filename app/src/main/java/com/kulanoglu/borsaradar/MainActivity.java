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
    private int detailTimeframe=7; // detail chart default: 1 ay
    private String detailSymbol="";
    private ShortPulseEngine.Result detailResult=null;
    private CatalystContextEngine.Result detailContext=null;
    private final AtomicInteger scanDone=new AtomicInteger(0), scanFailed=new AtomicInteger(0);
    private final AtomicInteger detailRequestGeneration=new AtomicInteger(0);

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
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(NAVY);
        LinearLayout head=new LinearLayout(this); head.setGravity(Gravity.CENTER_VERTICAL); head.setPadding(dp(14),dp(9),dp(14),dp(7)); head.setBackgroundColor(NAVY);
        TextView logo=bold("BR",16,Color.WHITE); logo.setGravity(Gravity.CENTER); logo.setBackgroundColor(RED);
        TextView brand=bold(" BorsaRadar",18,Color.WHITE); TextView title=bold(page,13,Color.rgb(170,190,210)); title.setGravity(Gravity.END);
        head.addView(logo,new LinearLayout.LayoutParams(dp(38),dp(38))); head.addView(brand,new LinearLayout.LayoutParams(0,dp(38),1)); head.addView(title,new LinearLayout.LayoutParams(0,dp(38),1)); root.addView(head);
        ScrollView sv=new ScrollView(this); sv.setFillViewport(true); sv.setBackgroundColor(NAVY);
        content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(10),dp(8),dp(10),dp(12)); content.setBackgroundColor(NAVY);
        sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL); nav.setPadding(dp(4),dp(3),dp(4),dp(4)); nav.setBackgroundColor(Color.rgb(7,27,46));
        Button home=button("⌂\nAna Sayfa",NAVY2), markets=button("▥\nPiyasalar",NAVY2), radar=button("◎\nRadar",NAVY2), portfolio=button("▣\nPortföy",NAVY2), more=button("•••\nDiğer",NAVY2);
        Button[] ns={home,markets,radar,portfolio,more}; String[] pages={"Ana Sayfa","Piyasalar","Radar Taraması","Portföy","Diğer"}; for(int i=0;i<ns.length;i++){Button b=ns[i];b.setTextSize(10);b.setAllCaps(false); if(page.equals(pages[i])||(i==2&&page.contains("Radar")))b.setTextColor(Color.rgb(90,165,255)); nav.addView(b,new LinearLayout.LayoutParams(0,dp(52),1));}
        home.setOnClickListener(v->showDashboard()); markets.setOnClickListener(v->singleStockDialog()); radar.setOnClickListener(v->showRadar()); portfolio.setOnClickListener(v->showPortfolio()); more.setOnClickListener(v->showMore()); root.addView(nav);
        setContentView(root);
    }

    private void shellDetail(String symbol) {
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(NAVY);
        LinearLayout top=new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL); top.setPadding(dp(14),dp(8),dp(14),dp(5)); top.setBackgroundColor(NAVY);
        Button back=button("‹",NAVY2); back.setTextSize(24); back.setPadding(0,0,0,0); back.setOnClickListener(v->{detailRequestGeneration.incrementAndGet();showPortfolio();});
        TextView brand=bold("BORSA RADAR",16,Color.WHITE); brand.setPadding(dp(6),0,0,0);
        TextView ticker=bold(symbol,17,Color.WHITE); ticker.setGravity(Gravity.END); ticker.setPadding(0,0,0,0);
        top.addView(back,new LinearLayout.LayoutParams(dp(44),dp(38))); top.addView(brand,new LinearLayout.LayoutParams(0,dp(38),1)); top.addView(ticker,new LinearLayout.LayoutParams(0,dp(38),1));
        root.addView(top);
        ScrollView sv=new ScrollView(this); sv.setFillViewport(true); sv.setBackgroundColor(NAVY);
        content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(8),dp(4),dp(8),dp(12)); content.setBackgroundColor(NAVY);
        sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout nav=new LinearLayout(this); nav.setBackgroundColor(Color.rgb(7,27,46)); Button home=button("⌂\nAna Sayfa",NAVY2),markets=button("▥\nPiyasalar",NAVY2),radar=button("◎\nRadar",NAVY2),portfolio=button("▣\nPortföy",NAVY2),more=button("•••\nDiğer",NAVY2); Button[] ns={home,markets,radar,portfolio,more}; for(Button b:ns){b.setTextSize(9);b.setAllCaps(false);nav.addView(b,new LinearLayout.LayoutParams(0,dp(48),1));} home.setOnClickListener(v->showDashboard());markets.setOnClickListener(v->singleStockDialog());radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());more.setOnClickListener(v->showMore());root.addView(nav);
        setContentView(root);
    }

    private void showDashboard() {
        shell("Ana Sayfa");
        TextView search=txt("⌕  Hisse ara (ör. THYAO, NVDA, SAP)...",13,Color.rgb(180,198,216)); search.setPadding(dp(12),dp(12),dp(12),dp(12)); search.setBackgroundColor(NAVY2); search.setOnClickListener(v->singleStockDialog()); content.addView(search); spacer(7);
        LinearLayout exchange=new LinearLayout(this); String[] ex={"BIST","Almanya","ABD","Tümü"}; for(String e:ex){Button q=button(e,e.equals("BIST")?Color.rgb(25,105,220):NAVY2);q.setTextSize(11);exchange.addView(q,new LinearLayout.LayoutParams(0,dp(40),1));} content.addView(exchange); spacer(7);
        LinearLayout hero=card();hero.addView(bold("Hızlı Tarama",18,Color.WHITE)); hero.setBackgroundColor(NAVY2);if(scanRunning){ProgressBar scanBar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);scanBar.setMax(ALL_SYMBOLS.length);scanBar.setProgress(scanDone.get());hero.addView(scanBar);hero.addView(txt("BIST taraması "+scanDone.get()+"/"+ALL_SYMBOLS.length+"  •  başarılı "+Math.max(0,scanDone.get()-scanFailed.get())+"  •  başarısız "+scanFailed.get(),12,Color.GRAY));}
        LinearLayout row=new LinearLayout(this);Button radar=button(scanRunning?"Tarama "+scanDone.get()+"/"+ALL_SYMBOLS.length:"Hızlı Tarama",RED),portfolio=button("Kısa Vade",Color.rgb(20,95,180)),baskets=button("Temettü",GREEN),longTerm=button("Uzun Vade",NAVY2);row.addView(radar,new LinearLayout.LayoutParams(0,-2,1));row.addView(portfolio,new LinearLayout.LayoutParams(0,-2,1));row.addView(baskets,new LinearLayout.LayoutParams(0,-2,1));row.addView(longTerm,new LinearLayout.LayoutParams(0,-2,1));hero.addView(row);radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());baskets.setOnClickListener(v->showBaskets());longTerm.setOnClickListener(v->showBaskets());content.addView(hero);spacer(7);
        LinearLayout status=card();status.addView(bold("Durum",17,NAVY));int buy=0,risk=0,watch=0;for(RadarItem x:new ArrayList<>(radarResults)){if(x.recommendation.contains("AL"))buy++;else if(x.recommendation.contains("SAT")||x.recommendation.contains("RİSK"))risk++;else watch++;}status.addView(txt("Portföy: "+holdings.size()+" pozisyon  •  Radar: "+radarResults.size()+" sonuç"+(scanRunning?"  •  tarama sürüyor":"")+(portfolioRefreshing?"  •  portföy yenileniyor":""),13,Color.DKGRAY));if(!radarResults.isEmpty()){status.addView(txt("Radar özeti: "+buy+" AL • "+watch+" TUT/İZLE • "+risk+" SAT/RİSK",13,Color.DKGRAY));int ownedRadar=0;for(Holding h:new ArrayList<>(holdings))if(findRadarItem(h.symbol)!=null)ownedRadar++;if(ownedRadar>0)status.addView(txt("Portföy-radar eşleşmesi: "+ownedRadar+" pozisyon",12,NAVY2));}long rt=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("radar_ts",0),pt=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("portfolio_ts",0);if(rt>0)status.addView(txt("Radar güncelleme: "+new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(rt)),12,Color.GRAY));if(pt>0)status.addView(txt("Portföy güncelleme: "+new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(pt)),12,Color.GRAY));if(rt==0&&!scanRunning)status.addView(txt("Radar henüz taranmadı.",11,Color.GRAY));if(pt==0&&!holdings.isEmpty()&&!portfolioRefreshing)status.addView(txt("Portföy henüz güncellenmedi.",11,Color.GRAY));content.addView(status);spacer(7); LinearLayout featured=card(); featured.setBackgroundColor(NAVY2); featured.addView(bold("Günün Öne Çıkanları",16,Color.WHITE)); featured.addView(txt("Radar sonuçları hazır olduğunda en güçlü AL / İZLE adayları burada öne çıkar.",12,Color.rgb(175,198,216))); content.addView(featured); spacer(7); LinearLayout market=card(); market.setBackgroundColor(NAVY2); market.addView(bold("Piyasa Özeti",15,Color.WHITE)); market.addView(txt("BIST 100     DAX     S&P 500     NASDAQ",12,Color.rgb(170,198,216))); content.addView(market); spacer(7); LinearLayout breaking=card(); breaking.setBackgroundColor(NAVY2); breaking.addView(bold("Son Dakika",15,Color.WHITE)); breaking.addView(txt("Önemli piyasa haberleri ve KAP gelişmeleri burada gösterilir.",12,Color.rgb(170,198,216))); content.addView(breaking); spacer(7);
        if(!radarResults.isEmpty()){List<RadarItem> top=new ArrayList<>(radarResults);top.removeIf(x->x.recommendation.contains("SAT")||x.recommendation.contains("RİSK"));top.sort((a,b)->Double.compare(b.score,a.score));int n=Math.min(3,top.size());LinearLayout picks=card();picks.addView(bold("Radar ilk 3",17,NAVY));picks.addView(txt("SAT/RİSK sinyalleri bu kısa listede gösterilmez. Pulse sırası kullanılır.",11,Color.GRAY));if(n==0)picks.addView(txt("Şu an AL/TUT tarafında öne çıkan aday yok.",12,Color.GRAY));else picks.addView(txt(n+" aday • doğrudan detaya geç",11,Color.GRAY));for(int i=0;i<n;i++){RadarItem x=top.get(i);Button pick=button((i+1)+". "+x.symbol+" • "+x.recommendation+" • Pulse "+fmt(x.score)+" • %"+(int)x.confidence,x.recommendation.contains("AL")?GREEN:AMBER);picks.addView(pick);pick.setOnClickListener(v->analyzeStock(x.symbol));}content.addView(picks);spacer(7);}LinearLayout quick=new LinearLayout(this);Button stock=button("Tek Hisse Analizi",AMBER),refreshP=button(portfolioRefreshing?"Portföy yenileniyor":"Portföyü Güncelle",NAVY2);stock.setContentDescription("Hisse koduyla tek hisse analizi aç");refreshP.setContentDescription("Portföy teknik verilerini güncelle");quick.addView(stock,new LinearLayout.LayoutParams(0,-2,1));quick.addView(refreshP,new LinearLayout.LayoutParams(0,-2,1));content.addView(quick);stock.setOnClickListener(v->singleStockDialog());refreshP.setEnabled(!portfolioRefreshing&&!holdings.isEmpty());refreshP.setOnClickListener(v->refreshPortfolio());
    }

    private void showPortfolio() {
        shell("Portföy");
        LinearLayout total=card(); total.setBackgroundColor(NAVY2); total.addView(txt("TOPLAM PORTFÖY DEĞERİ",11,Color.rgb(160,185,205))); total.addView(bold(holdings.isEmpty()?"0,00 ₺":holdings.size()+" pozisyon",24,Color.WHITE)); total.addView(txt("Portföy / İşlemler",12,Color.rgb(100,170,255))); content.addView(total); spacer(6);
        LinearLayout actions=new LinearLayout(this); Button add=button("+ Hisse Ekle",GREEN), refresh=button("Portföy Analiz",Color.rgb(25,105,220));
        actions.addView(add,new LinearLayout.LayoutParams(0,-2,1)); actions.addView(refresh,new LinearLayout.LayoutParams(0,-2,1)); content.addView(actions);
        add.setOnClickListener(v->portfolioDialog(null,null)); refresh.setEnabled(!portfolioRefreshing); refresh.setText(portfolioRefreshing?"Güncelleniyor…":"Tümünü Güncelle"); refresh.setOnClickListener(v->refreshPortfolio()); spacer(8); long pts=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("portfolio_ts",0); if(pts>0)content.addView(txt("Son portföy güncellemesi: "+new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(pts))+" • "+holdings.size()+" pozisyon",12,Color.GRAY));if(portfolioRefreshing)content.addView(txt("Teknik veriler yenileniyor; mevcut pozisyonlar korunuyor.",12,Color.GRAY));
        if(holdings.isEmpty()) { LinearLayout c=card(); c.addView(bold("Portföy boş",19,NAVY)); c.addView(txt("Hisse ekleyince maliyet, güncel fiyat, teknik görünüm ve haber/katalizör bağlamı burada görünür.",14,Color.DKGRAY));Button radar=button("Radardan Hisse Bul",GREEN);c.addView(radar);radar.setOnClickListener(v->showRadar()); content.addView(c); return; }
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
            if(priced<holdings.size())box.addView(txt("Bazı pozisyonların güncel fiyatı henüz yok: "+priced+"/"+holdings.size()+" fiyatlandı • eksik "+(holdings.size()-priced),12,AMBER));
            if(tlValue>0)addMarketSummary(box,"BIST",tlValue,tlCost,"₺");
            if(eurValue>0)addMarketSummary(box,"Avrupa",eurValue,eurCost,"€");
            if(usdValue>0){double rate=CurrencyService.usdToEur();if(Double.isFinite(rate)){addMarketSummary(box,"ABD",usdValue*rate,usdCost*rate,"€");box.addView(txt("ABD toplamı USD→EUR dönüşümüyle gösteriliyor.",10,Color.GRAY));}else addMarketSummary(box,"ABD",usdValue,usdCost,"$");}
            box.addView(txt("Fiyatlanan "+priced+"/"+holdings.size()+"  •  Artıda "+positive+"  •  Ekside "+negative+"  •  Nötr/eksik "+Math.max(0,holdings.size()-positive-negative),12,Color.DKGRAY));
        }
        content.addView(box);spacer(7);
    }

    private void addMarketSummary(LinearLayout box,String label,double value,double cost,String currency){
        double pnl=value-cost,pct=cost>0?pnl/cost*100:0;
        box.addView(bold(label+"  "+fmt(value)+" "+currency+"  •  P/L "+(pnl>=0?"+":"")+fmt(pnl)+" "+currency+"  •  "+String.format(Locale.US,"%+.2f%%",pct),15,pnl>=0?GREEN:RED));
    }

    private void renderHolding(Holding h) {
        LinearLayout c=card(); c.addView(bold(h.symbol+"  •  "+h.qty+" lot",20,NAVY));c.addView(txt("Pozisyona dokun: grafik ve güncel tavsiye",11,Color.GRAY)); c.addView(txt("Ortalama maliyet  "+money(h.cost,h.symbol)+"  •  Maliyet toplamı "+money(h.cost*h.qty,h.symbol),14,Color.DKGRAY));
        ShortPulseEngine.Result s=holdingSignal(h.symbol);
        if(s==null){c.addView(txt("Güncel değerlendirme henüz yok.",13,Color.GRAY));Button one=button("Bu Hisseyi Güncelle",NAVY2);c.addView(one);one.setOnClickListener(v->warmPortfolioSignal(h.symbol));}
        else {
            MarketDataService.Spot live=MarketDataService.latestSpot(h.symbol); double current=live!=null&&live.price>0?live.price:s.price;
            double pnl=(current-h.cost)*h.qty, pct=h.cost>0?(current/h.cost-1)*100:0;
            c.addView(bold("Son  "+money(current,h.symbol)+"   P/L  "+money(pnl,h.symbol)+"  (%"+fmt(pct)+")",16,pnl>=0?GREEN:RED)); c.addView(txt("Pozisyon değeri  "+money(current*h.qty,h.symbol)+(live!=null?"  •  fiyat "+live.source:"  •  teknik kapanış"),13,Color.DKGRAY)); c.addView(signalBanner(s)); c.addView(txt(s.explanation,13,Color.DKGRAY));
            CatalystContextEngine.Result cx=holdingContext(h.symbol); if(cx!=null)c.addView(contextBanner(cx));else c.addView(txt("Haber/katalizör bağlamı arka planda hazırlanıyor; teknik sonuç kullanılabilir.",12,Color.GRAY));
            c.addView(txt("Hedef süre: "+s.horizonText+"  •  Güven %"+(int)s.confidence+"  •  Stop ref. "+money(s.stopReference,h.symbol),13,NAVY2));RadarItem radar=findRadarItem(h.symbol);if(radar!=null)c.addView(txt("Radar: "+radar.recommendation+" • Pulse "+fmt(radar.score)+" • Güven %"+(int)radar.confidence,12,NAVY2));
        }
        LinearLayout row=new LinearLayout(this); Button detail=button("Grafik / Tavsiye",NAVY2), edit=button("Düzenle",AMBER), del=button("Sil",RED);detail.setContentDescription(h.symbol+" grafik ve tavsiye");edit.setContentDescription(h.symbol+" pozisyonunu düzenle");del.setContentDescription(h.symbol+" pozisyonunu sil");
        row.addView(detail,new LinearLayout.LayoutParams(0,-2,1.2f)); row.addView(edit,new LinearLayout.LayoutParams(0,-2,1)); row.addView(del,new LinearLayout.LayoutParams(0,-2,.7f)); c.addView(row);
        c.setOnClickListener(v->analyzeStock(h.symbol)); detail.setOnClickListener(v->{ShortPulseEngine.Result cached=holdingSignal(h.symbol);if(cached!=null)detailResult=cached;CatalystContextEngine.Result cc=holdingContext(h.symbol);if(cc!=null)detailContext=cc;analyzeStock(h.symbol);}); edit.setOnClickListener(v->portfolioDialog(h,h.symbol)); del.setOnClickListener(v->{String n=MarketDataService.normalizeSymbol(h.symbol);holdings.remove(h);holdingSignals.keySet().removeIf(k->MarketDataService.normalizeSymbol(k).equals(n));holdingContexts.keySet().removeIf(k->MarketDataService.normalizeSymbol(k).equals(n));savePortfolio();showPortfolio();}); content.addView(c); spacer(8);
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

    private void stockTabs(String symbol,String active,ShortPulseEngine.Result r,CatalystContextEngine.Result cx){
        LinearLayout tabs=new LinearLayout(this); String[] names={"Genel","Grafik","Haber","KAP","Finansal"};
        for(String t:names){Button b=button(t,t.equals(active)?Color.rgb(25,105,220):NAVY);b.setTextSize(10);b.setAllCaps(false);tabs.addView(b,new LinearLayout.LayoutParams(0,dp(38),1));
            if(t.equals("Genel"))b.setOnClickListener(v->showStockGeneral(symbol,r,cx)); else if(t.equals("Grafik"))b.setOnClickListener(v->analyzeStock(symbol,detailTimeframe)); else if(t.equals("Haber")||t.equals("KAP"))b.setOnClickListener(v->showStockNews(symbol,r,cx)); else if(t.equals("Finansal"))b.setOnClickListener(v->showStockFinancial(symbol,r)); else if(t.equals("Teknik"))b.setOnClickListener(v->showStockTechnical(symbol,r)); else b.setOnClickListener(v->showStockRisk(symbol,r));}
        content.addView(tabs);
    }
    private void showStockGeneral(String symbol,ShortPulseEngine.Result r,CatalystContextEngine.Result cx){
        shellDetail(symbol); stockTabs(symbol,"Genel",r,cx);
        LinearLayout signal=card(); signal.setBackgroundColor(NAVY2); signal.addView(bold("Hisse Detayı • Genel",17,Color.WHITE)); signal.addView(bold(r.recommendation+"   •   Güven %"+(int)r.confidence,18,r.recommendation.contains("AL")?GREEN:r.recommendation.contains("SAT")?RED:AMBER)); signal.addView(txt("Değişim "+String.format(Locale.US,"%+.2f%%",r.changePct)+"   •   Pulse "+fmt(r.score),13,Color.rgb(190,210,225))); content.addView(signal);
        LinearLayout quick=card(); quick.setBackgroundColor(NAVY2); quick.addView(bold("Hızlı Bilgiler",15,Color.WHITE)); quick.addView(txt("F/K   —        PD/DD   —        Temettü   —        Beta   —",12,Color.rgb(180,205,222))); quick.addView(txt("Teknik sinyal, fiyat hareketi ve haber bağlamı birlikte değerlendirilir.",12,Color.rgb(180,200,218))); if(cx!=null)quick.addView(txt("Haber bağlamı: "+cx.note,12,Color.WHITE)); content.addView(quick); LinearLayout links=new LinearLayout(this); Button technical=button("Teknik Analiz",Color.rgb(25,105,220)), risk=button("Hedef Fiyat & Risk",NAVY2); links.addView(technical,new LinearLayout.LayoutParams(0,dp(42),1)); links.addView(risk,new LinearLayout.LayoutParams(0,dp(42),1)); content.addView(links); technical.setOnClickListener(v->showStockTechnical(symbol,r)); risk.setOnClickListener(v->showStockRisk(symbol,r));
    }
    private void showStockNews(String symbol,ShortPulseEngine.Result r,CatalystContextEngine.Result cx){
        shellDetail(symbol); stockTabs(symbol,"Haber",r,cx); LinearLayout box=card(); box.setBackgroundColor(NAVY2); box.addView(bold("Haber & KAP",17,Color.WHITE)); box.addView(txt("Tümü   •   KAP   •   Medya   •   Analist",11,Color.rgb(130,185,255)));
        if(cx==null)box.addView(txt("Haber/KAP bağlamı henüz yüklenmedi. Grafik ekranından yenileyebilirsin.",12,Color.rgb(180,200,218))); else {box.addView(txt(cx.note,13,Color.WHITE)); box.addView(txt("Kapsam: "+cx.coverage+"   •   Haber skoru "+fmt(cx.newsScore)+"/8",12,Color.rgb(170,195,215)));} content.addView(box);
    }
    private void showStockFinancial(String symbol,ShortPulseEngine.Result r){
        shellDetail(symbol); stockTabs(symbol,"Finansal",r,detailContext); LinearLayout box=card(); box.setBackgroundColor(NAVY2); box.addView(bold("Finansal Veriler",17,Color.WHITE)); box.addView(txt("Özet   •   Gelir Tablosu   •   Bilanço   •   Nakit Akışı",11,Color.rgb(130,185,255))); box.addView(txt("Son fiyat   "+money(r.price,symbol),13,Color.WHITE)); box.addView(txt("Günlük değişim   "+String.format(Locale.US,"%+.2f%%",r.changePct),13,r.changePct>=0?GREEN:RED)); box.addView(txt("Teknik güven   %"+(int)r.confidence,13,Color.WHITE)); box.addView(txt("Finansal oranlar veri kaynağı doğrulandıkça bu ekrana eklenecek.",11,Color.rgb(160,180,200))); content.addView(box);
    }

    private void showStockTechnical(String symbol,ShortPulseEngine.Result r){
        shellDetail(symbol); stockTabs(symbol,"Teknik",r,detailContext);
        LinearLayout box=card(); box.setBackgroundColor(NAVY2); box.addView(bold("Teknik Görünüm",17,Color.WHITE));
        box.addView(txt("Pulse skoru   "+fmt(r.score),13,Color.WHITE)); box.addView(txt("Sinyal   "+r.recommendation,13,r.recommendation.contains("AL")?GREEN:r.recommendation.contains("SAT")?RED:AMBER));
        box.addView(txt("Güven   %"+(int)r.confidence,13,Color.WHITE)); box.addView(txt("Zaman dilimi   "+ChartTimeframes.label(detailTimeframe),12,Color.rgb(170,195,215))); content.addView(box);
    }
    private void showStockRisk(String symbol,ShortPulseEngine.Result r){
        shellDetail(symbol); stockTabs(symbol,"Hedef",r,detailContext);
        LinearLayout box=card(); box.setBackgroundColor(NAVY2); box.addView(bold("Hedef & Risk",17,Color.WHITE));
        box.addView(txt("Mevcut fiyat   "+money(r.price,symbol),13,Color.WHITE)); box.addView(txt("Sinyal güveni   %"+(int)r.confidence,13,Color.WHITE));
        box.addView(txt("Hedef, stop ve risk/ödül seviyeleri doğrulanmış fiyat yapısından hesaplanarak burada gösterilecek.",12,Color.rgb(180,200,218))); content.addView(box);
        LinearLayout actions=new LinearLayout(this); Button add=button("+ Portföye Ekle",GREEN),chart=button("Grafiğe Dön",Color.rgb(25,105,220)); actions.addView(add,new LinearLayout.LayoutParams(0,dp(44),1)); actions.addView(chart,new LinearLayout.LayoutParams(0,dp(44),1)); content.addView(actions);
        stockTabs(symbol,"Grafik",r,cx);
        Holding owned=findHolding(symbol); add.setOnClickListener(v->portfolioDialog(owned,symbol)); chart.setOnClickListener(v->analyzeStock(symbol,detailTimeframe));
    }

    private void refreshPortfolio() {
        if(holdings.isEmpty()){Toast.makeText(this,"Önce hisse ekle",Toast.LENGTH_SHORT).show();return;}
        if(portfolioRefreshing)return;
        portfolioRefreshing=true;
        final List<Holding> snapshot=new ArrayList<>(holdings);
        shell("Portföy güncelleniyor");
        ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(snapshot.size());content.addView(bar);
        TextView st=txt("0/"+snapshot.size()+" • teknik veriler",15,NAVY);content.addView(st);content.addView(txt("Haber/katalizör verileri teknik yenilemeyi bekletmez.",12,Color.GRAY));
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
                bar.setProgress(finished);st.setText(finished+"/"+snapshot.size()+" • teknik veriler");
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
            try{String oldKey=edit==null?"":MarketDataService.normalizeSymbol(edit.symbol);String raw=sym.getText().toString().trim().toUpperCase(Locale.ROOT); String s=parseSymbol(raw); if(s.length()<2)throw new Exception(); int q=Integer.parseInt(qty.getText().toString()); double c=Double.parseDouble(cost.getText().toString().replace(',','.')); if(q<=0||c<=0)throw new Exception(); if(edit==null){Holding existing=findHolding(s);if(existing==null)holdings.add(new Holding(s,q,c));else{int total=existing.qty+q;existing.cost=(existing.cost*existing.qty+c*q)/total;existing.qty=total;}}else{Holding collision=findHolding(s);if(collision!=null&&collision!=edit){int total=collision.qty+q;collision.cost=(collision.cost*collision.qty+c*q)/total;collision.qty=total;holdings.remove(edit);}else{edit.symbol=s;edit.qty=q;edit.cost=c;}} savePortfolio();String newKey=MarketDataService.normalizeSymbol(s);if(!oldKey.isEmpty()&&!oldKey.equals(newKey)&&findHolding(oldKey)==null){holdingSignals.keySet().removeIf(k->MarketDataService.normalizeSymbol(k).equals(oldKey));holdingContexts.keySet().removeIf(k->MarketDataService.normalizeSymbol(k).equals(oldKey));}warmPortfolioSignal(s);showPortfolio();}catch(Exception ex){Toast.makeText(this,"Hisse / adet / fiyatı kontrol et",Toast.LENGTH_LONG).show();}
        }).setNegativeButton("İptal",null).show();
    }

    private void warmPortfolioSignal(String symbol){
        final String s=MarketDataService.normalizeSymbol(symbol);
        List<MarketDataService.Candle> cached=MarketDataService.cachedSeries(s,"1mo","1d");
        if(cached!=null&&cached.size()>=15)try{holdingSignals.put(s,ShortPulseEngine.analyze(cached));main.post(()->{if(findHolding(s)!=null)showPortfolio();});}catch(Exception ignored){}
        io.execute(()->{try{List<MarketDataService.Candle>d=MarketDataService.fetchDaily(s,"1mo");ShortPulseEngine.Result r=ShortPulseEngine.analyze(d);holdingSignals.put(s,r);main.post(()->{if(findHolding(s)!=null)showPortfolio();});io.execute(()->{try{CatalystContextEngine.Result cx=CatalystContextEngine.analyze(s,r.score);if(cx!=null){holdingContexts.put(s,cx);main.post(()->{if(findHolding(s)!=null)showPortfolio();});}}catch(Exception ignored){}});}catch(Exception ignored){}});
    }

    private String parseSymbol(String raw){
        if(raw==null)return ""; String s=raw.trim(); int cut=s.indexOf(" • "); if(cut>0)s=s.substring(0,cut).trim(); if(MarketDataService.isGlobalSymbol(s))return s; return BistUniverse.symbolFromEntry(s);
    }

    private void showRadar() {
        shell("Radar Taraması"); LinearLayout filters=new LinearLayout(this); String[] fs={"Tümü","AL Sinyali","İzle","SAT"}; int[] fc={NAVY2,GREEN,NAVY2,RED}; for(int i=0;i<fs.length;i++){Button q=button(fs[i],fc[i]);q.setTextSize(11);filters.addView(q,new LinearLayout.LayoutParams(0,dp(40),1));} content.addView(filters); spacer(5); LinearLayout top=card(); top.setBackgroundColor(NAVY2); top.addView(bold("BIST 100  •  Tüm Sektörler  •  Teknik + Temel",14,Color.WHITE)); top.addView(txt("İlk tarama teknik olarak hızlı yapılır. Haber/katalizör bağlamı detay açıldığında yüklenir; böylece yüzlerce gereksiz ağ isteği yapılmaz.",13,Color.DKGRAY));
        Button scan=button(scanRunning?"Tarama "+scanDone.get()+"/"+ALL_SYMBOLS.length:"Tüm BIST'i Tara",GREEN); if(!radarResults.isEmpty()&&!scanRunning)top.addView(txt("Mevcut sonuçlar korunur; yeni tarama yeterli kapsamayla tamamlandığında listeyi yeniler.",12,Color.GRAY)); top.addView(scan); scan.setEnabled(!scanRunning); scan.setOnClickListener(v->scanRadar()); content.addView(top); spacer(8);
        if(scanRunning){content.addView(txt("Eski sonuçlar aşağıda kullanılabilir; yeni tarama tamamlanınca otomatik değişir.",12,Color.GRAY));int done=scanDone.get(),failed=scanFailed.get();ProgressBar pb=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);pb.setMax(ALL_SYMBOLS.length);pb.setProgress(done);content.addView(pb);content.addView(txt(done+"/"+ALL_SYMBOLS.length+" • başarılı "+Math.max(0,done-failed)+" • başarısız "+failed,14,NAVY));}
        if(!radarResults.isEmpty()){List<RadarItem> snap=new ArrayList<>(radarResults);snap.sort((a,b)->Double.compare(b.score,a.score));LinearLayout summary=card();long radarTs=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("radar_ts",0);String radarAge=radarTs>0?new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(radarTs)):"önbellek";summary.addView(bold("Son tarama • "+snap.size()+" hisse",16,NAVY));if(snap.size()<ALL_SYMBOLS.length)summary.addView(txt("Son başarılı sonuç kümesi: "+snap.size()+"/"+ALL_SYMBOLS.length,11,AMBER));summary.addView(txt("Güncelleme: "+radarAge+(scanRunning?" • yeni tarama sürüyor":""),12,Color.GRAY));int buy=0,hold=0,risk=0;for(RadarItem x:snap){if(x.recommendation.contains("AL"))buy++;else if(x.recommendation.contains("SAT")||x.recommendation.contains("RİSK"))risk++;else hold++;}summary.addView(txt("AL "+buy+"  •  TUT/İZLE "+hold+"  •  SAT/RİSK "+risk,13,Color.DKGRAY));summary.addView(txt("Gösterilen liste Pulse skoruna göre sıralıdır.",11,Color.GRAY));if(scanRunning)summary.addView(txt("Yeni tarama mevcut listeyi kullanım dışı bırakmaz.",11,NAVY2));Button baskets=button("3 Sepet Stratejisini Aç",PURPLE);summary.addView(baskets);baskets.setOnClickListener(v->showBaskets());content.addView(summary);spacer(6);renderRadarList(snap,30);}else content.addView(txt("Henüz radar sonucu yok.",14,Color.GRAY));
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
                int minCoverage=Math.max(20,ALL_SYMBOLS.length/4);if(sorted.size()>=minCoverage){synchronized(radarResults){radarResults.clear();radarResults.addAll(sorted);}saveRadarCache();getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putLong("radar_ts",System.currentTimeMillis()).apply();}
                scanRunning=false;main.post(()->{if(sorted.size()<minCoverage)Toast.makeText(this,"Yeni tarama yeterli kapsama ulaşmadı; önceki radar sonuçları korundu.",Toast.LENGTH_LONG).show();showRadar();});
            }else if(done%50==0)main.post(this::showRadar);
        });
    }

    private void renderRadarList(List<RadarItem> items,int max) {
        items.sort((a,b)->Double.compare(b.score,a.score)); content.addView(bold("En güçlü adaylar",18,NAVY));content.addView(txt("İlk "+Math.min(max,items.size())+" / "+items.size()+" sonuç gösteriliyor.",11,Color.GRAY));content.addView(txt("Karta dokun: detay • Detay ekranında Önceki/Sonraki ile sıralı adaylarda ilerle.",12,Color.GRAY)); int n=Math.min(max,items.size());
        for(int i=0;i<n;i++){RadarItem r=items.get(i);LinearLayout c=card();int col=r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:r.recommendation.contains("AL")?GREEN:AMBER;LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);LinearLayout left=new LinearLayout(this);left.setOrientation(LinearLayout.VERTICAL);left.addView(bold((i+1)+". "+r.symbol,18,NAVY));left.addView(txt(r.recommendation+"  •  Pulse "+fmt(r.score),14,col));LinearLayout right=new LinearLayout(this);right.setOrientation(LinearLayout.VERTICAL);right.setGravity(Gravity.END);MarketDataService.Spot spot=MarketDataService.latestSpot(r.symbol);double shown=spot!=null&&spot.price>0?spot.price:r.price;right.addView(bold(money(shown,r.symbol),17,col));if(spot==null)right.addView(txt("teknik kapanış",10,Color.GRAY));right.addView(txt("Güven %"+(int)r.confidence+" • "+r.horizon,12,Color.GRAY));if(spot!=null)right.addView(txt("Fiyat: "+spot.source,10,Color.GRAY));row.addView(left,new LinearLayout.LayoutParams(0,-2,1));row.addView(right,new LinearLayout.LayoutParams(-2,-2));c.addView(row);c.addView(txt(r.horizon+"  •  "+r.why,12,Color.GRAY));Holding owned=findHolding(r.symbol);if(owned!=null){double pct=owned.cost>0?(shown/owned.cost-1)*100:0;c.addView(txt("Portföyünde • "+owned.qty+" lot • maliyete göre "+String.format(Locale.US,"%+.2f%%",pct),12,pct>=0?GREEN:RED));}LinearLayout actions=new LinearLayout(this);Button d=button("Grafik / Detay",NAVY2),add=button(findHolding(r.symbol)==null?"Portföye Ekle":"Pozisyonu Düzenle",findHolding(r.symbol)==null?GREEN:AMBER);d.setContentDescription(r.symbol+" grafik ve detay");add.setContentDescription(r.symbol+" portföy işlemi");actions.addView(d,new LinearLayout.LayoutParams(0,-2,1));actions.addView(add,new LinearLayout.LayoutParams(0,-2,1));c.addView(actions);d.setOnClickListener(v->analyzeStock(r.symbol));add.setOnClickListener(v->portfolioDialog(findHolding(r.symbol),r.symbol));c.setOnClickListener(v->analyzeStock(r.symbol));content.addView(c);spacer(6);}
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
        final int requestGeneration=detailRequestGeneration.incrementAndGet();
        shellDetail(selectedSymbol);
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
                if(!hadInstant)main.post(()->{if(selectedSymbol.equals(detailSymbol) && selectedTimeframe==detailTimeframe){ List<MarketDataService.Candle> initialChart=DetailedChartController.cached(selectedSymbol,selectedTimeframe); if(initialChart!=null&&initialChart.size()>=2) renderStockDetail(selectedSymbol,r,null,initialChart); else { shell(selectedSymbol+" • "+ChartTimeframes.label(selectedTimeframe)); content.addView(txt(ChartTimeframes.label(selectedTimeframe)+" grafik verisi yükleniyor…",15,NAVY)); } }});

                // Ağır verileri ekran açıldıktan sonra arka planda tamamla.
                io.execute(()->{
                    try{
                        CatalystContextEngine.Result cx=selectedSymbol.equals(detailSymbol)?detailContext:null;
                        if(cx==null)try{cx=CatalystContextEngine.analyze(selectedSymbol,r.score);}catch(Exception ignored){cx=null;}
                        List<MarketDataService.Candle> chart;
                        chart=DetailedChartController.cached(selectedSymbol,selectedTimeframe);
                        if(chart==null||chart.size()<2)try{chart=DetailedChartController.fetch(selectedSymbol,selectedTimeframe);}catch(Exception ignored){chart=null;}
                        final CatalystContextEngine.Result safeCx=cx;
                        final List<MarketDataService.Candle> safeChart=chart;
                        if(requestGeneration==detailRequestGeneration.get() && selectedSymbol.equals(detailSymbol) && selectedTimeframe==detailTimeframe)detailContext=safeCx;
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
        shellDetail(symbol);
        stockTabs(symbol,"Grafik",r,cx);
        Holding owned=findHolding(symbol);
        MarketDataService.Spot live=MarketDataService.latestSpot(symbol);
        double shownPrice=live!=null&&live.price>0?live.price:r.price;
        int pos=r.changePct>=0?GREEN:RED;

        LinearLayout priceBox=new LinearLayout(this); priceBox.setOrientation(LinearLayout.VERTICAL); priceBox.setPadding(dp(10),dp(3),dp(10),dp(5)); priceBox.setBackgroundColor(NAVY);
        LinearLayout priceRow=new LinearLayout(this); priceRow.setGravity(Gravity.BOTTOM);
        TextView price=bold(money(shownPrice,symbol),30,pos); price.setPadding(0,0,0,0);
        TextView change=bold(String.format(Locale.US,"  %+.2f%%",r.changePct),14,pos); change.setPadding(0,0,0,dp(4));
        priceRow.addView(price); priceRow.addView(change); priceBox.addView(priceRow);
        String source=live!=null?live.source:"teknik kapanış";
        TextView sourceLine=txt("Son fiyat • "+source,10,Color.rgb(160,178,198)); sourceLine.setPadding(0,dp(2),0,0); priceBox.addView(sourceLine);
        content.addView(priceBox);

        LinearLayout tfRow=new LinearLayout(this); tfRow.setOrientation(LinearLayout.HORIZONTAL); tfRow.setGravity(Gravity.CENTER); tfRow.setPadding(0,dp(3),0,dp(3));
        final int[] compactIdx={7,8,9,10,11}; final String[] compactLabels={"1A","3A","6A","1Y","2Y"};
        for(int k=0;k<compactIdx.length;k++){final int idx=compactIdx[k];Button b=button(compactLabels[k],idx==detailTimeframe?GREEN:NAVY2);b.setAllCaps(false);b.setTextSize(12);b.setPadding(dp(2),0,dp(2),0);b.setOnClickListener(v->{if(idx!=detailTimeframe)analyzeStock(symbol,idx);});tfRow.addView(b,new LinearLayout.LayoutParams(0,dp(38),1));}
        content.addView(tfRow);

        if(chart==null||chart.size()<2){
            TextView empty=txt(ChartTimeframes.label(detailTimeframe)+" verisi yüklenemedi. Başka zaman diliminden veri gösterilmedi.",12,Color.rgb(255,120,120)); empty.setPadding(dp(10),dp(18),dp(10),dp(18)); content.addView(empty);
        }else{
            content.addView(new PriceChartView(this,chart,ChartTimeframes.label(detailTimeframe).toUpperCase(Locale.ROOT)),new LinearLayout.LayoutParams(-1,dp(405)));
        }

        LinearLayout status=new LinearLayout(this); status.setOrientation(LinearLayout.VERTICAL); status.setPadding(dp(10),dp(7),dp(10),dp(7)); status.setBackgroundColor(NAVY2);
        TextView sig=bold(r.recommendation+" • Güven %"+(int)r.confidence,13,Color.WHITE); sig.setPadding(0,0,0,0); status.addView(sig);
        if(owned!=null){double pnl=(shownPrice-owned.cost)*owned.qty;TextView own=txt("Maliyet "+money(owned.cost,symbol)+" • P/L "+money(pnl,symbol),11,pnl>=0?Color.rgb(90,220,170):Color.rgb(255,130,140));own.setPadding(0,dp(3),0,0);status.addView(own);}
        content.addView(status); spacer(4);

        LinearLayout actions=new LinearLayout(this);
        Button prev=button("◀",NAVY2),add=button(owned==null?"+ Portföy":"Pozisyon",owned==null?GREEN:AMBER),refresh=button("↻",NAVY2),next=button("▶",NAVY2);
        String prevSymbol=adjacentSymbol(symbol,-1),nextSymbol=adjacentSymbol(symbol,1);
        prev.setEnabled(!prevSymbol.equals(symbol)); next.setEnabled(!nextSymbol.equals(symbol));
        actions.addView(prev,new LinearLayout.LayoutParams(0,dp(42),.65f)); actions.addView(add,new LinearLayout.LayoutParams(0,dp(42),1.7f)); actions.addView(refresh,new LinearLayout.LayoutParams(0,dp(42),.65f)); actions.addView(next,new LinearLayout.LayoutParams(0,dp(42),.65f));
        content.addView(actions);
        prev.setOnClickListener(v->{if(!prevSymbol.equals(symbol))analyzeStock(prevSymbol,detailTimeframe);});
        add.setOnClickListener(v->portfolioDialog(owned,symbol));
        refresh.setOnClickListener(v->analyzeStock(symbol,detailTimeframe));
        next.setOnClickListener(v->{if(!nextSymbol.equals(symbol))analyzeStock(nextSymbol,detailTimeframe);});
    }

    private void showMore() {
        shell("Diğer");
        LinearLayout profile=card(); profile.setBackgroundColor(NAVY2); profile.addView(bold("BorsaRadar",18,Color.WHITE)); profile.addView(txt("Piyasa araçları ve uygulama ayarları",12,Color.rgb(170,195,215))); content.addView(profile); spacer(6);
        String[] items={"Piyasa Takvimi","Sektörler","Favorilerim","Alarmlar","Hisse Karşılaştırma","Döviz / Altın / Emtia","Ekonomik Veriler","Ayarlar","Destek","Hakkında"};
        for(String item:items){Button b=button(item+"   ›",NAVY2);b.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);b.setAllCaps(false);content.addView(b,new LinearLayout.LayoutParams(-1,dp(46)));spacer(2);}
        Button strategy=button("Strateji Seçimi",Color.rgb(25,105,220)); strategy.setOnClickListener(v->showBaskets()); content.addView(strategy); spacer(4); Button exit=button("Çıkış Yap",RED); content.addView(exit);
    }

    private void showBaskets() {
        shell("Strateji Seçimi");
        LinearLayout strategy=card(); strategy.setBackgroundColor(NAVY2); strategy.addView(bold("Tarama Stratejisi",18,Color.WHITE)); strategy.addView(txt("Kısa Vade   •   Temettü   •   Uzun Vade",14,Color.rgb(150,195,255))); strategy.addView(txt("✓ Teknik Analiz    ✓ Temel Analiz    ✓ Haber Taraması",12,Color.WHITE)); strategy.addView(txt("✓ Sektör Analizi   ✓ Büyük Alıcı/Satıcı   ✓ Finansal Güç",12,Color.WHITE)); Button start=button("Taramayı Başlat",GREEN); strategy.addView(start); start.setOnClickListener(v->showRadar()); content.addView(strategy); spacer(7); if(radarResults.isEmpty()){LinearLayout c=card();c.addView(bold(scanRunning?"Radar taraması devam ediyor":"Önce radar taraması gerekiyor",18,NAVY));if(scanRunning)c.addView(txt("Tamamlanınca 3 Sepet son geçerli radar sonucundan otomatik üretilebilir.",12,Color.GRAY));c.addView(txt("Tarama bir kez tamamlanınca sonuç kaydedilir; ekrandan çıksan da kaybolmaz.",13,Color.DKGRAY));Button go=button("Radarı Aç",GREEN);c.addView(go);go.setOnClickListener(v->showRadar());content.addView(c);return;}
        long radarTs=getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("radar_ts",0);if(radarTs>0)content.addView(txt("Radar verisi: "+new java.text.SimpleDateFormat("dd.MM HH:mm",Locale.getDefault()).format(new java.util.Date(radarTs))+(scanRunning?" • yeni tarama sürüyor, sepetler son tamamlanan sonucu kullanıyor":""),11,Color.GRAY));List<RadarItem>all=new ArrayList<>(radarResults);all.sort((a,b)->Double.compare(b.score,a.score));List<RadarItem>fast=new ArrayList<>(),twoWeek=new ArrayList<>(),div=new ArrayList<>();List<String>dp=Arrays.asList(DIVIDEND_POOL);for(RadarItem r:all){if(r.score>=5.2&&r.confidence>=60)fast.add(r);if(r.score>=3.7&&!r.recommendation.contains("SAT")&&!r.recommendation.contains("RİSK"))twoWeek.add(r);if(dp.contains(r.symbol)&&r.score>=1.5&&!r.recommendation.contains("SAT"))div.add(r);}content.addView(txt("Sepetler son tamamlanan radar sonucundan üretilir; uygun aday yoksa sistem hisseyi zorla seçmez. Aynı hisse farklı strateji filtresine uyarsa birden fazla sepette görünebilir.",12,Color.GRAY));content.addView(txt("Toplam model bütçesi: 100.000 TL • 33.333 / 33.333 / 33.334 TL",11,NAVY2));spacer(6);basket("1 • HIZLI 1–3 GÜN",33333,fast,GREEN,"Güçlü momentum + hacim + kısa trend.");basket("2 • 4–10 İŞLEM GÜNÜ",33333,twoWeek,NAVY2,"Daha dengeli Pulse skoru; en fazla yaklaşık iki hafta.");basket("3 • TEMETTÜ + TEKNİK",33334,div,PURPLE,"Temettü geçmişi güçlü şirket havuzu içinden mevcut teknik görünümü zayıf olmayanlar.");
    }

    private void basket(String title,int budget,List<RadarItem>xs,int color,String note){TextView h=bold(title+"  •  "+budget+" TL",18,Color.WHITE);h.setBackgroundColor(color);h.setPadding(dp(12),dp(12),dp(12),dp(12));content.addView(h);content.addView(txt(note,13,Color.DKGRAY));content.addView(txt("Bütçe adaylara eşit bölünür; lot hesabı güncel mevcut fiyatla yapılır.",11,Color.GRAY));xs.sort((a,b)->Double.compare(b.score,a.score));int n=Math.min(4,xs.size());if(n==0){content.addView(txt("Şu an filtreden geçen aday yok; filtre zorlanmıyor ve "+budget+" TL nakit korunuyor.",14,RED));spacer(8);return;}int per=budget/n;content.addView(txt("Aday başına hedef bütçe yaklaşık "+per+" TL",11,Color.GRAY));int used=0;for(int i=0;i<n;i++){RadarItem r=xs.get(i);MarketDataService.Spot live=MarketDataService.latestSpot(r.symbol);double px=live!=null&&live.price>0?live.price:r.price;int lots=px>0?Math.max(0,(int)Math.floor(per/px)):0;used+=(int)Math.round(lots*px);LinearLayout c=card();c.addView(bold((i+1)+". "+r.symbol+"  •  "+r.recommendation,17,color));c.addView(txt(money(px,r.symbol)+"  •  yaklaşık "+lots+" lot  •  Pulse "+fmt(r.score)+"  •  Güven %"+(int)r.confidence,13,Color.DKGRAY));if(lots==0)c.addView(txt("Aday başı bütçe mevcut fiyatla 1 lot için yetersiz.",11,AMBER));c.addView(txt(r.horizon+"  •  "+r.why,12,Color.GRAY));if(findHolding(r.symbol)!=null)c.addView(txt("Mevcut portföy pozisyonu",11,NAVY2));LinearLayout actions=new LinearLayout(this);Button d=button("Grafik / Tavsiye",color),add=button(findHolding(r.symbol)==null?"Portföye Ekle":"Pozisyonu Düzenle",findHolding(r.symbol)==null?GREEN:AMBER);actions.addView(d,new LinearLayout.LayoutParams(0,-2,1));actions.addView(add,new LinearLayout.LayoutParams(0,-2,1));c.addView(actions);d.setOnClickListener(v->analyzeStock(r.symbol));add.setOnClickListener(v->portfolioDialog(findHolding(r.symbol),r.symbol));c.setOnClickListener(v->analyzeStock(r.symbol));content.addView(c);spacer(5);}content.addView(txt("Yaklaşık kullanım "+used+" TL  •  Nakit "+Math.max(0,budget-used)+" TL  •  "+n+" aday",12,Color.GRAY));content.addView(txt("Lot hesabı yaklaşık model dağılımıdır; emir oluşturmaz.",10,Color.GRAY));spacer(6);}

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
        int target=at+delta;
        return at<0||target<0||target>=order.size()?s:order.get(target);
    }

    private String money(double x,String symbol){String n=MarketDataService.normalizeSymbol(symbol);if(n.endsWith(".IS"))return String.format(Locale.US,"%.2f ₺",x);if(n.endsWith(".DE"))return String.format(Locale.US,"%.2f €",x);double rate=CurrencyService.usdToEur();if(!Double.isFinite(rate))io.execute(CurrencyService::refreshIfNeeded);double shown=Double.isFinite(rate)?x*rate:x;return String.format(Locale.US,"%.2f %s",shown,Double.isFinite(rate)?"€":"$");} private String fmt(double x){return String.format(Locale.US,"%.2f",x);}
    @Override public void onBackPressed(){ if(detailSymbol!=null&&!detailSymbol.isEmpty()){ detailRequestGeneration.incrementAndGet(); detailSymbol=""; showPortfolio(); } else super.onBackPressed(); }

}
