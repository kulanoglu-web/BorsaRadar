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
    private static final int NAVY = Color.rgb(5, 18, 34);
    private static final int NAVY2 = Color.rgb(11, 31, 53);\n    private static final int PANEL = Color.rgb(12, 34, 59);\n    private static final int BLUE = Color.rgb(36, 118, 255);\n    private static final int MUTED = Color.rgb(137, 163, 188);
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
        showDashboard();
    }

    @Override protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }

    private int dp(int x) { return Math.round(x * getResources().getDisplayMetrics().density); }

    private android.graphics.drawable.GradientDrawable bg(int color,int radius) { android.graphics.drawable.GradientDrawable g=new android.graphics.drawable.GradientDrawable(); g.setColor(color); g.setCornerRadius(dp(radius)); return g; }\n\n    private TextView chip(String text,int color) { TextView v=bold(text,10,Color.WHITE); v.setGravity(Gravity.CENTER); v.setPadding(dp(8),dp(3),dp(8),dp(3)); v.setBackground(bg(color,12)); return v; }\n\n    private TextView txt(String text, int sp, int color) {
        TextView v=new TextView(this);
        v.setText(text); v.setTextSize(sp); v.setTextColor(color);
        v.setPadding(dp(8),dp(4),dp(8),dp(4));
        return v;
    }

    private TextView bold(String text, int sp, int color) {
        TextView v=txt(text,sp,color); v.setTypeface(null, Typeface.BOLD); return v;
    }

    private Button button(String text, int color) {
        Button b=new Button(this);
        b.setText(text); b.setAllCaps(false); b.setTextColor(Color.WHITE); b.setTextSize(13);
        android.graphics.drawable.GradientDrawable bg=new android.graphics.drawable.GradientDrawable(); bg.setColor(color); bg.setCornerRadius(dp(10)); b.setBackground(bg); b.setPadding(dp(6),dp(3),dp(6),dp(3));
        return b;
    }

    private void spacer(int h) { Space s=new Space(this); content.addView(s,new LinearLayout.LayoutParams(1,dp(h))); }

    private LinearLayout card() {
        LinearLayout c=new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setPadding(dp(10),dp(8),dp(10),dp(8));
        android.graphics.drawable.GradientDrawable bg=new android.graphics.drawable.GradientDrawable(); bg.setColor(PANEL); bg.setCornerRadius(dp(12)); c.setBackground(bg);
        return c;
    }

    private void shell(String page) {
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(NAVY);
        LinearLayout head=new LinearLayout(this); head.setGravity(Gravity.CENTER_VERTICAL); head.setPadding(dp(14),dp(8),dp(14),dp(7)); head.setBackgroundColor(NAVY);
        TextView logo=bold("BR",14,Color.WHITE); logo.setGravity(Gravity.CENTER); android.graphics.drawable.GradientDrawable lbg=new android.graphics.drawable.GradientDrawable(); lbg.setColor(BLUE); lbg.setCornerRadius(dp(10)); logo.setBackground(lbg);
        TextView brand=bold("  BORSA RADAR",15,Color.WHITE); TextView title=bold(page,11,Color.rgb(170,190,210)); title.setGravity(Gravity.END);
        head.addView(logo,new LinearLayout.LayoutParams(dp(30),dp(30))); head.addView(brand,new LinearLayout.LayoutParams(0,dp(38),1)); head.addView(title,new LinearLayout.LayoutParams(0,dp(38),1)); root.addView(head);
        ScrollView sv=new ScrollView(this); sv.setFillViewport(true); sv.setBackgroundColor(NAVY);
        content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(12),dp(8),dp(12),dp(12)); content.setBackgroundColor(NAVY);
        sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL); nav.setPadding(dp(5),dp(4),dp(5),dp(5)); nav.setBackgroundColor(Color.rgb(7,27,46));
        Button home=button("⌂\nAna Sayfa",page.equals("Ana Sayfa")?Color.rgb(16,48,78):NAVY2), markets=button("▥\nPiyasalar",page.equals("Piyasalar")?Color.rgb(16,48,78):NAVY2), radar=button("◎\nRadar",page.contains("Radar")?Color.rgb(16,48,78):NAVY2), portfolio=button("▣\nPortföy",page.equals("Portföy")?Color.rgb(16,48,78):NAVY2), more=button("•••\nDiğer",page.equals("Diğer")?Color.rgb(16,48,78):NAVY2);
        Button[] ns={home,markets,radar,portfolio,more}; String[] pages={"Ana Sayfa","Piyasalar","Radar Taraması","Portföy","Diğer"}; for(int i=0;i<ns.length;i++){Button b=ns[i];b.setTextSize(10);b.setAllCaps(false); if(page.equals(pages[i])||(i==2&&page.contains("Radar"))){b.setTextColor(Color.rgb(83,158,255));} nav.addView(b,new LinearLayout.LayoutParams(0,dp(44),1));}
        home.setOnClickListener(v->showDashboard()); markets.setOnClickListener(v->singleStockDialog()); radar.setOnClickListener(v->showRadar()); portfolio.setOnClickListener(v->showPortfolio()); more.setOnClickListener(v->showMore()); root.addView(nav);
        setContentView(root);
    }

    private void shellDetail(String symbol) {
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(NAVY);
        LinearLayout top=new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL); top.setPadding(dp(10),dp(5),dp(10),dp(4)); top.setBackgroundColor(NAVY);
        Button back=button("‹",NAVY2); back.setTextSize(21); back.setPadding(0,0,0,0); back.setOnClickListener(v->{detailRequestGeneration.incrementAndGet();showPortfolio();});
        TextView brand=bold("BORSA RADAR",14,Color.WHITE); brand.setPadding(dp(6),0,0,0);
        TextView ticker=bold(symbol,15,Color.WHITE); ticker.setGravity(Gravity.END); ticker.setPadding(0,0,0,0);
        top.addView(back,new LinearLayout.LayoutParams(dp(38),dp(34))); top.addView(brand,new LinearLayout.LayoutParams(0,dp(34),1)); top.addView(ticker,new LinearLayout.LayoutParams(0,dp(34),1));
        root.addView(top);
        ScrollView sv=new ScrollView(this); sv.setFillViewport(true); sv.setBackgroundColor(NAVY);
        content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(7),dp(3),dp(7),dp(9)); content.setBackgroundColor(NAVY);
        sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout nav=new LinearLayout(this); nav.setBackgroundColor(Color.rgb(7,27,46)); Button home=button("⌂\nAna Sayfa",NAVY2),markets=button("▥\nPiyasalar",NAVY2),radar=button("◎\nRadar",NAVY2),portfolio=button("▣\nPortföy",NAVY2),more=button("•••\nDiğer",NAVY2); Button[] ns={home,markets,radar,portfolio,more}; for(Button b:ns){b.setTextSize(9);b.setAllCaps(false);nav.addView(b,new LinearLayout.LayoutParams(0,dp(44),1));} home.setOnClickListener(v->showDashboard());markets.setOnClickListener(v->singleStockDialog());radar.setOnClickListener(v->showRadar());portfolio.setOnClickListener(v->showPortfolio());more.setOnClickListener(v->showMore());root.addView(nav);
        setContentView(root);
    }

    private void showDashboard() {
        shell("Ana Sayfa");
        LinearLayout hero=new LinearLayout(this);hero.setGravity(Gravity.CENTER_VERTICAL);LinearLayout ht=new LinearLayout(this);ht.setOrientation(LinearLayout.VERTICAL);ht.addView(bold("Piyasayı tek ekrandan takip et",18,Color.WHITE));ht.addView(txt("Canlı radar • portföy • haber • teknik",10,Color.rgb(145,175,200)));hero.addView(ht,new LinearLayout.LayoutParams(0,dp(45),1));TextView bell=bold("●",14,Color.rgb(70,150,255));bell.setGravity(Gravity.CENTER);hero.addView(bell,new LinearLayout.LayoutParams(dp(32),dp(32)));content.addView(hero);
        TextView search=txt("⌕   Hisse, endeks veya şirket ara...",12,Color.rgb(185,205,220));search.setPadding(dp(12),dp(9),dp(12),dp(9));search.setBackgroundColor(NAVY2);search.setOnClickListener(v->singleStockDialog());content.addView(search);spacer(5);
        LinearLayout exchange=new LinearLayout(this);String[] ex={"BIST","Almanya","ABD","Tümü"};for(String e:ex){Button q=button(e,e.equals("BIST")?BLUE:NAVY2);q.setTextSize(10);q.setOnClickListener(v->singleStockDialog());exchange.addView(q,new LinearLayout.LayoutParams(0,dp(30),1));}content.addView(exchange);spacer(7);
        content.addView(bold("Stratejiler",13,Color.WHITE));LinearLayout r1=new LinearLayout(this),r2=new LinearLayout(this);Button fast=button("⚡ Hızlı Tarama\nAnlık fırsatlar",BLUE),shortB=button("↗ Kısa Vade\nGünlük / saatlik",Color.rgb(40,61,105)),div=button("◆ Temettü\nDüzenli gelir",Color.rgb(18,83,76)),longB=button("◎ Uzun Vade\nGüçlü şirketler",Color.rgb(93,72,30));for(Button x:new Button[]{fast,shortB,div,longB}){x.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);x.setTextSize(10);}r1.addView(fast,new LinearLayout.LayoutParams(0,dp(52),1));r1.addView(shortB,new LinearLayout.LayoutParams(0,dp(52),1));r2.addView(div,new LinearLayout.LayoutParams(0,dp(52),1));r2.addView(longB,new LinearLayout.LayoutParams(0,dp(52),1));content.addView(r1);content.addView(r2);fast.setOnClickListener(v->showRadar());shortB.setOnClickListener(v->showBaskets());div.setOnClickListener(v->showBaskets());longB.setOnClickListener(v->showBaskets());spacer(7);
        LinearLayout fh=new LinearLayout(this);fh.setGravity(Gravity.CENTER_VERTICAL);fh.addView(bold("Günün Öne Çıkanları",13,Color.WHITE),new LinearLayout.LayoutParams(0,dp(28),1));TextView all=txt("Tümünü Gör ›",10,Color.rgb(83,158,255));all.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);all.setOnClickListener(v->showRadar());fh.addView(all,new LinearLayout.LayoutParams(0,dp(28),1));content.addView(fh);
        LinearLayout featured=card();List<RadarItem> top=new ArrayList<>(radarResults);top.removeIf(x->x.recommendation.contains("SAT")||x.recommendation.contains("RİSK"));top.sort((x,y)->Double.compare(y.score,x.score));if(top.isEmpty()){LinearLayout row=new LinearLayout(this);LinearLayout lt=new LinearLayout(this);lt.setOrientation(LinearLayout.VERTICAL);lt.addView(bold("Radar bekliyor",12,Color.WHITE));lt.addView(txt("Tarama sonrası fırsatlar burada",9,Color.rgb(155,180,200)));row.addView(lt,new LinearLayout.LayoutParams(0,dp(38),1));Button go=button("Tara",BLUE);go.setOnClickListener(v->showRadar());row.addView(go,new LinearLayout.LayoutParams(dp(68),dp(34)));featured.addView(row);}else for(int i=0;i<Math.min(3,top.size());i++){RadarItem x=top.get(i);LinearLayout row=new LinearLayout(this);TextView sy=bold(x.symbol,12,Color.WHITE),px=bold(money(x.price,x.symbol),11,Color.WHITE),sg=bold(x.recommendation,10,x.recommendation.contains("AL")?GREEN:AMBER);sg.setGravity(Gravity.END);row.addView(sy,new LinearLayout.LayoutParams(0,dp(29),1));row.addView(px,new LinearLayout.LayoutParams(0,dp(29),1));row.addView(sg,new LinearLayout.LayoutParams(0,dp(29),1));row.setOnClickListener(v->analyzeStock(x.symbol));featured.addView(row);}content.addView(featured);spacer(6);
        content.addView(bold("Piyasa Özeti",13,Color.WHITE));LinearLayout markets=new LinearLayout(this);String[] names={"BIST100","DAX","S&P500","NASDAQ"};String[] syms={"XU100.IS","^GDAXI","^GSPC","^IXIC"};for(int i=0;i<names.length;i++){MarketDataService.Spot sp=MarketDataService.latestSpot(syms[i]);LinearLayout mc=card();mc.setPadding(dp(6),dp(5),dp(6),dp(5));mc.addView(bold(names[i],9,Color.WHITE));mc.addView(bold(sp!=null&&sp.price>0?fmt(sp.price):"—",11,Color.rgb(190,210,225)));mc.addView(txt(sp!=null?"güncel":"veri bekleniyor",8,Color.rgb(130,160,185)));final String sym=syms[i];mc.setOnClickListener(v->analyzeStock(sym));markets.addView(mc,new LinearLayout.LayoutParams(0,dp(58),1));}content.addView(markets);spacer(6);
        LinearLayout news=card();LinearLayout nr=new LinearLayout(this);nr.setGravity(Gravity.CENTER_VERTICAL);nr.addView(bold("●",10,RED),new LinearLayout.LayoutParams(dp(22),dp(32)));LinearLayout nt=new LinearLayout(this);nt.setOrientation(LinearLayout.VERTICAL);nt.addView(bold("Son Dakika",12,Color.WHITE));nt.addView(txt("KAP ve önemli piyasa gelişmeleri",9,Color.rgb(165,190,210)));nr.addView(nt,new LinearLayout.LayoutParams(0,dp(38),1));TextView ar=bold("›",18,Color.rgb(100,165,225));ar.setGravity(Gravity.CENTER);nr.addView(ar,new LinearLayout.LayoutParams(dp(24),dp(38)));news.addView(nr);news.setOnClickListener(v->showRadar());content.addView(news);
        if(scanRunning){spacer(4);ProgressBar bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);bar.setMax(ALL_SYMBOLS.length);bar.setProgress(scanDone.get());content.addView(bar);}
    }

    private void showPortfolio() {
        shell("Portföy");
        double totalValue=0,totalCost=0;int priced=0;for(Holding h:new ArrayList<>(holdings)){ShortPulseEngine.Result s=holdingSignal(h.symbol);if(s!=null&&s.price>0){MarketDataService.Spot live=MarketDataService.latestSpot(h.symbol);double px=live!=null&&live.price>0?live.price:s.price;totalValue+=px*h.qty;totalCost+=h.cost*h.qty;priced++;}}
        double pnl=totalValue-totalCost,pct=totalCost>0?pnl/totalCost*100:0;
        LinearLayout hero=card();hero.addView(txt("TOPLAM PORTFÖY DEĞERİ",10,Color.rgb(145,175,198)));hero.addView(bold(priced>0?fmt(totalValue)+" ₺":"0,00 ₺",25,Color.WHITE));hero.addView(bold((pnl>=0?"+":"")+fmt(pnl)+" ₺   "+String.format(Locale.US,"%+.2f%%",pct),12,pnl>=0?GREEN:RED));content.addView(hero);spacer(5);
        LinearLayout tabs=new LinearLayout(this);Button pt=button("Portföy",BLUE),it=button("İşlemler",NAVY2);tabs.addView(pt,new LinearLayout.LayoutParams(0,dp(34),1));tabs.addView(it,new LinearLayout.LayoutParams(0,dp(34),1));content.addView(tabs);spacer(6);
        if(holdings.isEmpty()){LinearLayout empty=card();empty.addView(bold("Portföyün henüz boş",15,Color.WHITE));empty.addView(txt("İlk hissenizi ekleyerek takibe başlayın.",11,Color.rgb(165,190,210)));content.addView(empty);}
        else {LinearLayout hdr=card();String[] hs={"HİSSE","ADET / MAL.","GÜNCEL","K/Z"};for(String x:hs){TextView t=bold(x,8,Color.rgb(135,165,190));t.setGravity(x.equals("HİSSE")?Gravity.START:Gravity.END);hdr.addView(t,new LinearLayout.LayoutParams(0,dp(26),1));}hdr.setOrientation(LinearLayout.HORIZONTAL);content.addView(hdr);for(Holding h:new ArrayList<>(holdings)){ShortPulseEngine.Result s=holdingSignal(h.symbol);MarketDataService.Spot live=MarketDataService.latestSpot(h.symbol);double px=live!=null&&live.price>0?live.price:(s!=null?s.price:0),hpnl=px>0?(px-h.cost)*h.qty:0,hpct=h.cost>0&&px>0?(px/h.cost-1)*100:0;LinearLayout row=card();row.setGravity(Gravity.CENTER_VERTICAL);TextView sy=bold(h.symbol,12,Color.WHITE);TextView qty=txt(h.qty+" / "+money(h.cost,h.symbol),10,Color.rgb(180,202,218));qty.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);TextView cur=bold(px>0?money(px,h.symbol):"—",11,Color.WHITE);cur.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);TextView pl=bold(px>0?String.format(Locale.US,"%+.2f%%",hpct):"—",11,hpnl>=0?GREEN:RED);pl.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);row.addView(sy,new LinearLayout.LayoutParams(0,dp(42),1));row.addView(qty,new LinearLayout.LayoutParams(0,dp(42),1.35f));row.addView(cur,new LinearLayout.LayoutParams(0,dp(42),1));row.addView(pl,new LinearLayout.LayoutParams(0,dp(42),1));row.setOnClickListener(v->analyzeStock(h.symbol));content.addView(row);spacer(2);}}
        spacer(6);LinearLayout actions=new LinearLayout(this);Button add=button("+ Hisse Ekle",GREEN),analysis=button("Portföy Analiz",BLUE);actions.addView(add,new LinearLayout.LayoutParams(0,dp(42),1));actions.addView(analysis,new LinearLayout.LayoutParams(0,dp(42),1));content.addView(actions);add.setOnClickListener(v->portfolioDialog(null,null));analysis.setEnabled(!portfolioRefreshing);analysis.setOnClickListener(v->refreshPortfolio());
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
        LinearLayout box=card();box.setBackgroundColor(NAVY2);box.addView(bold("Portföy özeti",18,Color.WHITE));
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
        LinearLayout c=card(); c.setBackgroundColor(NAVY2); c.addView(bold(h.symbol+"  •  "+h.qty+" lot",20,Color.WHITE));c.addView(txt("Pozisyona dokun: grafik ve güncel tavsiye",11,Color.GRAY)); c.addView(txt("Ortalama maliyet  "+money(h.cost,h.symbol)+"  •  Maliyet toplamı "+money(h.cost*h.qty,h.symbol),14,Color.DKGRAY));
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
        LinearLayout tabs=new LinearLayout(this); tabs.setGravity(Gravity.CENTER);
        String[] names={"Genel","Grafik","Haber","KAP","Finansal"};
        for(String t:names){
            Button x=button(t,t.equals(active)?BLUE:NAVY); x.setTextSize(9); x.setAllCaps(false);
            tabs.addView(x,new LinearLayout.LayoutParams(0,dp(34),1));
            if(t.equals("Genel"))x.setOnClickListener(v->showStockGeneral(symbol,r,cx));
            else if(t.equals("Grafik"))x.setOnClickListener(v->analyzeStock(symbol,detailTimeframe));
            else if(t.equals("Haber")||t.equals("KAP"))x.setOnClickListener(v->showStockNews(symbol,r,cx));
            else x.setOnClickListener(v->showStockFinancial(symbol,r));
        }
        content.addView(tabs); spacer(4);
    }

    private void showStockGeneral(String symbol,ShortPulseEngine.Result r,CatalystContextEngine.Result cx){
        shellDetail(symbol);stockTabs(symbol,"Genel",r,cx);int sigColor=r.recommendation.contains("AL")?GREEN:(r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:AMBER);
        LinearLayout head=card();LinearLayout pr=new LinearLayout(this);pr.setGravity(Gravity.CENTER_VERTICAL);LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.addView(bold(symbol,20,Color.WHITE));l.addView(txt("BIST100  •  Hisse Detayı",10,Color.rgb(145,175,198)));LinearLayout rr=new LinearLayout(this);rr.setOrientation(LinearLayout.VERTICAL);rr.setGravity(Gravity.END);rr.addView(bold(money(r.price,symbol),22,Color.WHITE));TextView ch=bold(String.format(Locale.US,"%+.2f%%",r.changePct),12,r.changePct>=0?GREEN:RED);ch.setGravity(Gravity.END);rr.addView(ch);pr.addView(l,new LinearLayout.LayoutParams(0,dp(50),1));pr.addView(rr,new LinearLayout.LayoutParams(0,dp(50),1));head.addView(pr);head.addView(txt("Bugün  •  "+new java.text.SimpleDateFormat("dd.MM.yyyy HH:mm",Locale.getDefault()).format(new java.util.Date()),10,Color.rgb(135,165,190)));content.addView(head);spacer(5);
        LinearLayout quick=card();String[] q={"AÇILIŞ\n—","YÜKSEK\n—","DÜŞÜK\n—","HACİM\n—"};for(String x:q){TextView t=bold(x,10,Color.WHITE);t.setGravity(Gravity.CENTER);quick.addView(t,new LinearLayout.LayoutParams(0,dp(45),1));}quick.setOrientation(LinearLayout.HORIZONTAL);content.addView(quick);spacer(5);
        LinearLayout signals=new LinearLayout(this);String[] sn={"AL","TUT","SAT"};int[] sc={GREEN,AMBER,RED};for(int i=0;i<3;i++){Button x=button(sn[i],r.recommendation.contains(sn[i])?sc[i]:NAVY2);x.setTextSize(11);signals.addView(x,new LinearLayout.LayoutParams(0,dp(38),1));}content.addView(signals);spacer(6);
        LinearLayout info=card();info.addView(bold("Hızlı Bilgiler",13,Color.WHITE));LinearLayout vals=new LinearLayout(this);String[] iv={"F/K\n—","PD/DD\n—","Temettü\n—","Beta\n—"};for(String x:iv){TextView t=bold(x,10,Color.WHITE);t.setGravity(Gravity.CENTER);vals.addView(t,new LinearLayout.LayoutParams(0,dp(45),1));}info.addView(vals);content.addView(info);spacer(5);
        LinearLayout ranges=card();ranges.addView(bold("Fiyat Aralıkları",12,Color.WHITE));ranges.addView(txt("Günlük aralık     —────────●────────—",11,Color.rgb(165,195,215)));ranges.addView(txt("52 hafta           —────────●────────—",11,Color.rgb(165,195,215)));content.addView(ranges);spacer(6);
        LinearLayout deep=new LinearLayout(this);
        Button tech=button("Teknik Analiz",BLUE), risk=button("Hedef Fiyat & Risk",NAVY2);
        tech.setOnClickListener(v->showStockTechnical(symbol,r)); risk.setOnClickListener(v->showStockRisk(symbol,r));
        deep.addView(tech,new LinearLayout.LayoutParams(0,dp(40),1)); deep.addView(risk,new LinearLayout.LayoutParams(0,dp(40),1)); content.addView(deep);spacer(5);
        LinearLayout state=card();state.addView(bold("Teknik Görünüm",12,Color.WHITE));state.addView(bold(r.recommendation+"   •   Güven %"+(int)r.confidence,14,sigColor));state.addView(txt("Pulse "+fmt(r.score)+"  •  "+r.horizonText,10,Color.rgb(165,195,215)));content.addView(state);spacer(5);
        LinearLayout links=new LinearLayout(this);Button technical=button("Teknik Analiz",BLUE),risk=button("Hedef Fiyat & Risk",Color.rgb(62,75,130));links.addView(technical,new LinearLayout.LayoutParams(0,dp(40),1));links.addView(risk,new LinearLayout.LayoutParams(0,dp(40),1));content.addView(links);technical.setOnClickListener(v->showStockTechnical(symbol,r));risk.setOnClickListener(v->showStockRisk(symbol,r));
    }

    private void showStockNews(String symbol,ShortPulseEngine.Result r,CatalystContextEngine.Result cx){
        shellDetail(symbol); stockTabs(symbol,"Haber",r,cx);
        LinearLayout header=card();header.setBackgroundColor(NAVY2);header.addView(bold("Haber & KAP",16,Color.WHITE));
        LinearLayout filters=new LinearLayout(this);String[] fs={"Tümü","KAP","Medya","Analist"};for(int i=0;i<fs.length;i++){Button q=button(fs[i],i==0?BLUE:NAVY2);q.setTextSize(10);filters.addView(q,new LinearLayout.LayoutParams(0,dp(32),1));}header.addView(filters);content.addView(header);spacer(6);
        if(cx==null){LinearLayout empty=card();empty.setBackgroundColor(NAVY2);empty.addView(bold("Haber akışı hazırlanıyor",14,Color.WHITE));empty.addView(txt("KAP ve haber bağlamı arka planda yükleniyor.",12,Color.rgb(175,198,216)));content.addView(empty);}
        else{
            LinearLayout n1=card();n1.setBackgroundColor(NAVY2);n1.addView(bold(cx.positiveCatalyst?"POZİTİF":"GÜNCEL BAĞLAM",11,cx.positiveCatalyst?GREEN:AMBER));n1.addView(bold(cx.note,13,Color.WHITE));n1.addView(txt("Kapsam: "+cx.coverage+"  •  Haber skoru "+fmt(cx.newsScore)+"/8",11,Color.rgb(170,195,215)));content.addView(n1);spacer(5);
            LinearLayout n2=card();n2.setBackgroundColor(NAVY2);n2.addView(bold("Teknik / Haber İlişkisi",13,Color.WHITE));n2.addView(txt(cx.technicalConflict?"Teknik görünüm ile haber akışı arasında çelişki var.":"Haber bağlamı teknik görünümle birlikte değerlendiriliyor.",12,cx.technicalConflict?AMBER:Color.rgb(175,198,216)));content.addView(n2);
        }
    }
    private void showStockFinancial(String symbol,ShortPulseEngine.Result r){
        shellDetail(symbol); stockTabs(symbol,"Finansal",r,detailContext);
        LinearLayout head=card();head.setBackgroundColor(NAVY2);head.addView(bold("Finansal Veriler",16,Color.WHITE));head.addView(txt("Özet     Gelir Tablosu     Bilanço     Nakit Akışı",11,Color.rgb(120,180,255)));content.addView(head);spacer(6);
        String[][] rows={{"Piyasa Değeri","—"},{"F/K","—"},{"PD/DD","—"},{"FD/FAVÖK","—"},{"Hisse Başına Kâr","—"},{"Temettü Verimi","—"},{"Özsermaye Kârlılığı","—"},{"Net Kâr","—"},{"Ciro","—"},{"Büyüme","—"},{"Sektör","—"},{"52 Hafta Düşük / Yüksek","—"}};
        LinearLayout table=card();table.setBackgroundColor(NAVY2);
        for(int i=0;i<rows.length;i++){LinearLayout row=new LinearLayout(this);TextView k=txt(rows[i][0],12,Color.rgb(175,198,216)),v=bold(rows[i][1],12,Color.WHITE);v.setGravity(Gravity.END);row.addView(k,new LinearLayout.LayoutParams(0,dp(31),1));row.addView(v,new LinearLayout.LayoutParams(0,dp(31),1));table.addView(row);}
        content.addView(table);spacer(6);
        LinearLayout market=card();market.setBackgroundColor(NAVY2);market.addView(bold("Piyasa Verisi",14,Color.WHITE));market.addView(txt("Son fiyat   "+money(r.price,symbol),12,Color.WHITE));market.addView(txt("Günlük değişim   "+String.format(Locale.US,"%+.2f%%",r.changePct),12,r.changePct>=0?GREEN:RED));market.addView(txt("Teknik güven   %"+(int)r.confidence,12,Color.WHITE));content.addView(market);
    }

    private void showStockTechnical(String symbol,ShortPulseEngine.Result r){
        shellDetail(symbol); stockTabs(symbol,"Teknik",r,detailContext);
        int overall=r.recommendation.contains("AL")?GREEN:(r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:AMBER);
        LinearLayout head=card();head.setBackgroundColor(NAVY2);head.addView(bold("Teknik Analiz",16,Color.WHITE));head.addView(txt("İndikatör Sinyalleri",12,Color.rgb(150,190,220)));content.addView(head);spacer(5);
        String[][] rows={{"RSI","Momentum"},{"MACD","Trend"},{"Stochastic","Momentum"},{"CCI","Momentum"},{"EMA20","Kısa trend"},{"EMA50","Orta trend"},{"EMA200","Ana trend"},{"Bollinger","Volatilite"},{"ATR","Risk"},{"SuperTrend","Trend"},{"Fibonacci","Destek / Direnç"}};
        LinearLayout table=card();table.setBackgroundColor(NAVY2);for(int i=0;i<rows.length;i++){LinearLayout row=new LinearLayout(this);TextView n=bold(rows[i][0],12,Color.WHITE),desc=txt(rows[i][1],10,Color.rgb(160,185,205));LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.addView(n);l.addView(desc);String signal=i<4?(r.score>=4?"AL":r.score<=1?"SAT":"İZLE"):(r.recommendation.contains("AL")?"AL":r.recommendation.contains("SAT")?"SAT":"İZLE");int col=signal.equals("AL")?GREEN:signal.equals("SAT")?RED:AMBER;TextView sv=bold(signal,11,col);sv.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);row.addView(l,new LinearLayout.LayoutParams(0,dp(37),1));row.addView(sv,new LinearLayout.LayoutParams(dp(70),dp(37)));table.addView(row);}content.addView(table);spacer(6);
        LinearLayout overallBox=card();overallBox.setBackgroundColor(NAVY2);overallBox.addView(bold("Genel Teknik Görünüm",14,Color.WHITE));overallBox.addView(bold(r.recommendation+"   •   Alım Gücü %"+(int)r.confidence,16,overall));overallBox.addView(txt("Kısa vade: "+r.horizonText+"   •   Pulse "+fmt(r.score),11,Color.rgb(175,198,216)));content.addView(overallBox);
    }
    private void showStockRisk(String symbol,ShortPulseEngine.Result r){
        shellDetail(symbol); stockTabs(symbol,"Hedef",r,detailContext);
        LinearLayout analysts=card();analysts.setBackgroundColor(NAVY2);analysts.addView(bold("Hedef Fiyat & Risk",16,Color.WHITE));analysts.addView(txt("Analist Hedefleri & Tahminleri",12,Color.rgb(150,190,220)));
        LinearLayout ar=new LinearLayout(this);String[] labels={"Ortalama\n—","Yüksek\n—","Düşük\n—","Analist\n—"};for(String x:labels){TextView t=bold(x,11,Color.WHITE);t.setGravity(Gravity.CENTER);ar.addView(t,new LinearLayout.LayoutParams(0,dp(48),1));}analysts.addView(ar);content.addView(analysts);spacer(6);
        LinearLayout horizons=card();horizons.setBackgroundColor(NAVY2);horizons.addView(bold("Zaman Ufku",14,Color.WHITE));String[] hs={"Kısa Vade","Orta Vade","Uzun Vade"};for(String h:hs){LinearLayout row=new LinearLayout(this);row.addView(txt(h,12,Color.rgb(175,198,216)),new LinearLayout.LayoutParams(0,dp(30),1));TextView v=bold("—",12,Color.WHITE);v.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);row.addView(v,new LinearLayout.LayoutParams(0,dp(30),1));horizons.addView(row);}content.addView(horizons);spacer(6);
        LinearLayout sr=card();sr.setBackgroundColor(NAVY2);sr.addView(bold("Destek / Direnç",14,Color.WHITE));sr.addView(txt("Doğrulanmış fiyat seviyeleri hesaplandığında burada gösterilecek.",11,Color.rgb(175,198,216)));content.addView(sr);spacer(6);
        LinearLayout risk=card();risk.setBackgroundColor(NAVY2);risk.addView(bold("Risk Yönetimi",14,Color.WHITE));risk.addView(txt("Mevcut fiyat   "+money(r.price,symbol),12,Color.WHITE));risk.addView(txt("Stop-Loss   —",12,RED));risk.addView(txt("Risk / Ödül   —",12,AMBER));risk.addView(txt("Sinyal güveni   %"+(int)r.confidence,12,Color.WHITE));content.addView(risk);spacer(5);
        LinearLayout actions=new LinearLayout(this);Button add=button("+ Portföye Ekle",GREEN),chart=button("Grafiğe Dön",BLUE);actions.addView(add,new LinearLayout.LayoutParams(0,dp(44),1));actions.addView(chart,new LinearLayout.LayoutParams(0,dp(44),1));content.addView(actions);Holding owned=findHolding(symbol);add.setOnClickListener(v->portfolioDialog(owned,symbol));chart.setOnClickListener(v->analyzeStock(symbol,detailTimeframe));
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
        shell("Radar Taraması");
        LinearLayout titleRow=new LinearLayout(this);titleRow.setGravity(Gravity.CENTER_VERTICAL);titleRow.addView(bold("Radar Taraması",17,Color.WHITE),new LinearLayout.LayoutParams(0,dp(34),1));TextView search=bold("⌕",18,Color.WHITE);search.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);titleRow.addView(search,new LinearLayout.LayoutParams(dp(36),dp(34)));content.addView(titleRow);
        LinearLayout filters=new LinearLayout(this);String[] fs={"Tümü","AL Sinyali","İzle","SAT"};for(int i=0;i<fs.length;i++){Button q=button(fs[i],i==0?BLUE:NAVY2);q.setTextSize(10);filters.addView(q,new LinearLayout.LayoutParams(0,dp(34),1));}content.addView(filters);spacer(5);
        LinearLayout selectors=new LinearLayout(this);String[] ss={"BIST100 ▼","Tüm Sektörler ▼","Teknik+Temel ▼"};for(String x:ss){Button q=button(x,NAVY2);q.setTextSize(9);selectors.addView(q,new LinearLayout.LayoutParams(0,dp(34),1));}content.addView(selectors);spacer(6);
        Button scan=button(scanRunning?"Taranıyor  "+scanDone.get()+"/"+ALL_SYMBOLS.length:"Tüm BIST\u0027i Tara",BLUE);scan.setEnabled(!scanRunning);scan.setOnClickListener(v->scanRadar());content.addView(scan,new LinearLayout.LayoutParams(-1,dp(42)));spacer(7);
        if(scanRunning){ProgressBar pb=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);pb.setMax(ALL_SYMBOLS.length);pb.setProgress(scanDone.get());content.addView(pb);}
        if(!radarResults.isEmpty()){
            List<RadarItem> snap=new ArrayList<>(radarResults);snap.sort((x,y)->Double.compare(y.score,x.score));int buy=0,hold=0,risk=0;for(RadarItem x:snap){if(x.recommendation.contains("AL"))buy++;else if(x.recommendation.contains("SAT")||x.recommendation.contains("RİSK"))risk++;else hold++;}
            LinearLayout stats=card();stats.setOrientation(LinearLayout.HORIZONTAL);String[] st={"AL\n"+buy,"İZLE\n"+hold,"SAT\n"+risk,"TOPLAM\n"+snap.size()};int[] co={GREEN,AMBER,RED,Color.WHITE};for(int i=0;i<st.length;i++){TextView v=bold(st[i],11,co[i]);v.setGravity(Gravity.CENTER);stats.addView(v,new LinearLayout.LayoutParams(0,dp(46),1));}content.addView(stats);spacer(6);
            renderRadarList(snap,30);
        } else {LinearLayout empty=card();empty.addView(bold("Henüz radar sonucu yok",15,Color.WHITE));empty.addView(txt("Taramayı başlat; sonuçlar bu ekranda fiyat ve sinyal ile listelenecek.",11,Color.rgb(165,190,210)));content.addView(empty);}
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
        items.sort((x,y)->Double.compare(y.score,x.score));LinearLayout hdr=card();hdr.setOrientation(LinearLayout.HORIZONTAL);String[] hh={"HİSSE","FİYAT","DEĞİŞİM","SİNYAL"};for(String h:hh){TextView t=bold(h,9,Color.rgb(135,165,190));t.setGravity(h.equals("HİSSE")?Gravity.START:Gravity.END);hdr.addView(t,new LinearLayout.LayoutParams(0,dp(28),1));}content.addView(hdr);spacer(3);
        int n=Math.min(max,items.size());for(int i=0;i<n;i++){RadarItem r=items.get(i);MarketDataService.Spot spot=MarketDataService.latestSpot(r.symbol);double shown=spot!=null&&spot.price>0?spot.price:r.price;double ch=r.price>0?(shown/r.price-1.0)*100.0:0;String sig=r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?"SAT":r.recommendation.contains("AL")?"AL":"İZLE";int col=sig.equals("AL")?GREEN:sig.equals("SAT")?RED:AMBER;
            LinearLayout row=card();row.setGravity(Gravity.CENTER_VERTICAL);TextView sy=bold(r.symbol,13,Color.WHITE);LinearLayout syBox=new LinearLayout(this);syBox.setOrientation(LinearLayout.VERTICAL);syBox.addView(sy);syBox.addView(txt(r.horizon,9,Color.rgb(135,165,190)));TextView px=bold(money(shown,r.symbol),12,Color.WHITE);px.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);TextView change=bold(String.format(Locale.US,"%+.2f%%",ch),11,ch>=0?GREEN:RED);change.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);TextView signal=chip(sig,col);signal.setGravity(Gravity.CENTER);row.addView(syBox,new LinearLayout.LayoutParams(0,dp(40),1));row.addView(px,new LinearLayout.LayoutParams(0,dp(40),1));row.addView(change,new LinearLayout.LayoutParams(0,dp(40),1));LinearLayout sigBox=new LinearLayout(this);sigBox.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);sigBox.addView(signal,new LinearLayout.LayoutParams(dp(54),dp(27)));row.addView(sigBox,new LinearLayout.LayoutParams(0,dp(40),1));row.setOnClickListener(v->analyzeStock(r.symbol));content.addView(row);spacer(2);
        }
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
        // Yükleme sırasında da ekran boş kalmasın: sekmeler ve seçili zaman dilimi hemen görünür.
        stockTabs(selectedSymbol,"Grafik",detailResult,detailContext);
        LinearLayout loadingTf=new LinearLayout(this); loadingTf.setOrientation(LinearLayout.HORIZONTAL); loadingTf.setGravity(Gravity.CENTER);
        final int[] loadingIdx={5,3,7,8,9,10,11}; final String[] loadingLabels={"1G","1H","1A","3A","6A","1Y","2Y"};
        for(int k=0;k<loadingIdx.length;k++){final int idx=loadingIdx[k];Button b=button(loadingLabels[k],idx==selectedTimeframe?GREEN:NAVY2);b.setAllCaps(false);b.setTextSize(11);b.setOnClickListener(v->{if(idx!=detailTimeframe)analyzeStock(selectedSymbol,idx);});loadingTf.addView(b,new LinearLayout.LayoutParams(0,dp(38),1));}
        content.addView(loadingTf);
        content.addView(txt(ChartTimeframes.label(selectedTimeframe)+" grafik verisi yükleniyor…",14,Color.rgb(170,195,215)));

        final ShortPulseEngine.Result previousResult=sameSymbol?detailResult:null;
        io.execute(()->{
            try{
                // Seçili grafik ve analiz verisini aynı iş içinde yükle. İç içe executor yok:
                // tek iş parçacıklı executor kullanılsa bile grafik isteği artık kilitlenmez.
                List<MarketDataService.Candle> chart=null;
                try{chart=DetailedChartController.cached(selectedSymbol,selectedTimeframe);}catch(Exception ignored){}
                if(chart==null||chart.size()<2) chart=DetailedChartController.fetch(selectedSymbol,selectedTimeframe);

                ShortPulseEngine.Result r=previousResult;
                if(r==null){
                    List<MarketDataService.Candle> base=MarketDataService.cachedSeries(selectedSymbol,"1mo","1d");
                    if(base==null||base.size()<15) base=MarketDataService.fetchDaily(selectedSymbol,"1mo");
                    r=ShortPulseEngine.analyze(base);
                }
                final ShortPulseEngine.Result safeResult=r;
                final List<MarketDataService.Candle> safeChart=chart;

                CatalystContextEngine.Result cx=detailContext;
                if(cx==null)try{cx=CatalystContextEngine.analyze(selectedSymbol,safeResult.score);}catch(Exception ignored){}
                final CatalystContextEngine.Result safeCx=cx;

                main.post(()->{
                    if(requestGeneration!=detailRequestGeneration.get()||!selectedSymbol.equals(detailSymbol)||selectedTimeframe!=detailTimeframe)return;
                    detailResult=safeResult; detailContext=safeCx;
                    renderStockDetail(selectedSymbol,safeResult,safeCx,safeChart);
                     if(selectedTimeframe<=8){ prefetchTimeframes(selectedSymbol); prefetchAdjacent(selectedSymbol); }
                });
            }catch(Exception e){
                final String msg=e.getMessage()==null?"veri alınamadı":e.getMessage();
                main.post(()->{
                    if(requestGeneration!=detailRequestGeneration.get()||!selectedSymbol.equals(detailSymbol)||selectedTimeframe!=detailTimeframe)return;
                    shellDetail(selectedSymbol);
                    content.addView(txt(ChartTimeframes.label(selectedTimeframe)+" verisi alınamadı: "+msg,14,RED));
                });
            }
        });
    }

    private Holding findHolding(String symbol){String n=MarketDataService.normalizeSymbol(symbol);for(Holding h:holdings)if(MarketDataService.normalizeSymbol(h.symbol).equals(n))return h;return null;}
    private ShortPulseEngine.Result holdingSignal(String symbol){String n=MarketDataService.normalizeSymbol(symbol);ShortPulseEngine.Result r=holdingSignals.get(n);if(r!=null)return r;for(Map.Entry<String,ShortPulseEngine.Result> e:holdingSignals.entrySet())if(MarketDataService.normalizeSymbol(e.getKey()).equals(n))return e.getValue();return null;}
    private CatalystContextEngine.Result holdingContext(String symbol){String n=MarketDataService.normalizeSymbol(symbol);CatalystContextEngine.Result r=holdingContexts.get(n);if(r!=null)return r;for(Map.Entry<String,CatalystContextEngine.Result> e:holdingContexts.entrySet())if(MarketDataService.normalizeSymbol(e.getKey()).equals(n))return e.getValue();return null;}
    private RadarItem findRadarItem(String symbol){String n=MarketDataService.normalizeSymbol(symbol);synchronized(radarResults){for(RadarItem x:radarResults)if(MarketDataService.normalizeSymbol(x.symbol).equals(n))return x;}return null;}

    private void loadDetailContextAsync(String symbol,double score,int generation) {
        io.execute(()->{
            try{
                CatalystContextEngine.Result cx=CatalystContextEngine.analyze(symbol,score);
                if(cx!=null)main.post(()->{if(generation==detailRequestGeneration.get()&&symbol.equals(detailSymbol))detailContext=cx;});
            }catch(Exception ignored){}
        });
    }

    private void renderStockDetail(String symbol,ShortPulseEngine.Result r,CatalystContextEngine.Result cx,List<MarketDataService.Candle> chart) {
        shellDetail(symbol);
        stockTabs(symbol,"Grafik",r,cx);
        Holding owned=findHolding(symbol);
        MarketDataService.Spot live=MarketDataService.latestSpot(symbol);
        double chartLast=(chart!=null&&!chart.isEmpty())?chart.get(chart.size()-1).close:0;
        double shownPrice=chartLast>0?chartLast:(live!=null&&live.price>0?live.price:r.price);
        int pos=r.changePct>=0?GREEN:RED;

        LinearLayout priceBox=new LinearLayout(this); priceBox.setOrientation(LinearLayout.VERTICAL); priceBox.setPadding(dp(6),dp(2),dp(6),dp(3)); priceBox.setBackgroundColor(NAVY);
        LinearLayout priceRow=new LinearLayout(this); priceRow.setGravity(Gravity.BOTTOM);
        TextView price=bold(money(shownPrice,symbol),23,Color.WHITE); price.setPadding(0,0,0,0);
        TextView change=bold(String.format(Locale.US,"  %+.2f%%",r.changePct),13,pos); change.setPadding(0,0,0,dp(4));
        priceRow.addView(price); priceRow.addView(change); priceBox.addView(priceRow);
        String source=chartLast>0?ChartTimeframes.label(detailTimeframe)+" grafik kapanışı":(live!=null?live.source:"teknik kapanış");
        TextView sourceLine=txt("Son fiyat • "+source,10,Color.rgb(160,178,198)); sourceLine.setPadding(0,dp(2),0,0); priceBox.addView(sourceLine);
        content.addView(priceBox);

        LinearLayout tfRow=new LinearLayout(this); tfRow.setOrientation(LinearLayout.HORIZONTAL); tfRow.setGravity(Gravity.CENTER); tfRow.setPadding(0,dp(3),0,dp(3));
        final int[] compactIdx={5,3,7,8,9,10,11}; final String[] compactLabels={"1G","1H","1A","3A","6A","1Y","2Y"};
        for(int k=0;k<compactIdx.length;k++){final int idx=compactIdx[k];Button b=button(compactLabels[k],idx==detailTimeframe?GREEN:NAVY2);b.setAllCaps(false);b.setTextSize(12);b.setPadding(dp(2),0,dp(2),0);b.setOnClickListener(v->{if(idx!=detailTimeframe)analyzeStock(symbol,idx);});tfRow.addView(b,new LinearLayout.LayoutParams(0,dp(34),1));}
        content.addView(tfRow);
        LinearLayout indicators=new LinearLayout(this); indicators.setGravity(Gravity.CENTER);
        String[] inds={"RSI","MACD","Stoch","CCI","BB"};
        for(String in:inds){Button ib=button(in,NAVY2);ib.setTextSize(10);ib.setAllCaps(false);indicators.addView(ib,new LinearLayout.LayoutParams(0,dp(30),1));}
        content.addView(indicators);

        if(chart==null||chart.size()<2){
            TextView empty=txt(ChartTimeframes.label(detailTimeframe)+" verisi yüklenemedi. Başka zaman diliminden veri gösterilmedi.",12,Color.rgb(255,120,120)); empty.setPadding(dp(10),dp(18),dp(10),dp(18)); content.addView(empty);
        }else{
            content.addView(new PriceChartView(this,chart,ChartTimeframes.label(detailTimeframe).toUpperCase(Locale.ROOT)),new LinearLayout.LayoutParams(-1,dp(330)));
        }

        LinearLayout status=new LinearLayout(this); status.setOrientation(LinearLayout.VERTICAL); status.setPadding(dp(10),dp(5),dp(10),dp(5)); status.setBackgroundColor(NAVY2);
        int sigColor=r.recommendation.contains("AL")?GREEN:(r.recommendation.contains("SAT")||r.recommendation.contains("RİSK")?RED:AMBER); TextView sig=bold(r.recommendation+"   •   Güven %"+(int)r.confidence,14,sigColor); sig.setPadding(0,0,0,0); status.addView(sig);
        TextView sigScope=txt("Teknik sinyal • "+ChartTimeframes.label(detailTimeframe)+" grafik • Pulse "+fmt(r.score),10,Color.rgb(160,178,198)); sigScope.setPadding(0,dp(3),0,0); status.addView(sigScope);
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
        LinearLayout profile=card();profile.setBackgroundColor(NAVY2);LinearLayout pr=new LinearLayout(this);TextView avatar=bold("BR",14,Color.WHITE);avatar.setGravity(Gravity.CENTER);pr.addView(avatar,new LinearLayout.LayoutParams(dp(42),dp(42)));LinearLayout ptxt=new LinearLayout(this);ptxt.setOrientation(LinearLayout.VERTICAL);ptxt.addView(bold("BorsaRadar",15,Color.WHITE));ptxt.addView(txt("Piyasa araçları ve uygulama ayarları",10,Color.rgb(170,195,215)));pr.addView(ptxt,new LinearLayout.LayoutParams(0,dp(42),1));profile.addView(pr);content.addView(profile);spacer(7);
        String[][] groups={{"PİYASA","Piyasa Takvimi","Sektörler","Favorilerim","Alarmlar","Hisse Karşılaştırma"},{"ARAÇLAR","Döviz / Altın / Emtia","Ekonomik Veriler"},{"UYGULAMA","Ayarlar","Destek","Hakkında"}};
        for(String[] g:groups){content.addView(bold(g[0],11,Color.rgb(130,165,195)));for(int i=1;i<g.length;i++){LinearLayout row=card();row.setBackgroundColor(NAVY2);TextView name=bold(g[i],13,Color.WHITE),arrow=bold("›",20,Color.rgb(120,170,220));arrow.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);row.setOrientation(LinearLayout.HORIZONTAL);row.addView(name,new LinearLayout.LayoutParams(0,dp(31),1));row.addView(arrow,new LinearLayout.LayoutParams(dp(28),dp(31)));content.addView(row);spacer(3);}spacer(4);}
        Button strategy=button("Strateji Seçimi",BLUE);strategy.setOnClickListener(v->showBaskets());content.addView(strategy,new LinearLayout.LayoutParams(-1,dp(42)));spacer(5);Button exit=button("Çıkış Yap",RED);content.addView(exit,new LinearLayout.LayoutParams(-1,dp(42)));
    }

    private void showBaskets() {
        shell("Strateji Seçimi");content.addView(txt("Tarama amacını seç",11,Color.rgb(150,180,205)));spacer(4);
        LinearLayout modes=new LinearLayout(this);modes.setOrientation(LinearLayout.VERTICAL);String[][] ms={{"⚡  Kısa Vade","Günlük / saatlik fırsatlar"},{"◆  Temettü","Düzenli gelir odaklı"},{"◎  Uzun Vade","Güçlü şirket / trend"}};for(int i=0;i<ms.length;i++){LinearLayout box=card();LinearLayout row=new LinearLayout(this);LinearLayout tx=new LinearLayout(this);tx.setOrientation(LinearLayout.VERTICAL);tx.addView(bold(ms[i][0],14,Color.WHITE));tx.addView(txt(ms[i][1],10,Color.rgb(155,185,207)));row.addView(tx,new LinearLayout.LayoutParams(0,dp(45),1));TextView check=bold(i==0?"●":"○",18,i==0?Color.rgb(70,150,255):Color.rgb(100,125,150));check.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);row.addView(check,new LinearLayout.LayoutParams(dp(40),dp(45)));box.addView(row);modes.addView(box);spacer(3);}content.addView(modes);spacer(6);
        LinearLayout criteria=card();criteria.addView(bold("Tarama Kriterleri",14,Color.WHITE));String[] cs={"Teknik Analiz","Temel Analiz","Haber Taraması","Sektör Analizi","Büyük Alıcı / Satıcı","Finansal Güç","Temettü Potansiyeli"};for(String x:cs){LinearLayout row=new LinearLayout(this);row.addView(txt(x,12,Color.rgb(190,207,220)),new LinearLayout.LayoutParams(0,dp(33),1));TextView ck=bold("✓",13,GREEN);ck.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);row.addView(ck,new LinearLayout.LayoutParams(dp(35),dp(33)));criteria.addView(row);}content.addView(criteria);spacer(7);
        Button start=button("Taramayı Başlat",GREEN);start.setOnClickListener(v->{if(!scanRunning)scanRadar();else showRadar();});content.addView(start,new LinearLayout.LayoutParams(-1,dp(46)));spacer(6);
        if(!radarResults.isEmpty()){List<RadarItem> all=new ArrayList<>(radarResults);all.sort((x,y)->Double.compare(y.score,x.score));LinearLayout preview=card();preview.addView(bold("Son Radar Özeti",13,Color.WHITE));preview.addView(txt(all.size()+" hisse değerlendirildi • sonuçlar Radar ekranında",10,Color.rgb(155,185,207)));Button open=button("Radar Sonuçlarını Aç",BLUE);open.setOnClickListener(v->showRadar());preview.addView(open);content.addView(preview);}
    }

    private void basket(String title,int budget,List<RadarItem>xs,int color,String note){TextView h=bold(title+"  •  "+budget+" TL",18,Color.WHITE);h.setBackgroundColor(color);h.setPadding(dp(12),dp(12),dp(12),dp(12));content.addView(h);content.addView(txt(note,13,Color.DKGRAY));content.addView(txt("Bütçe adaylara eşit bölünür; lot hesabı güncel mevcut fiyatla yapılır.",11,Color.GRAY));xs.sort((a,b)->Double.compare(b.score,a.score));int n=Math.min(4,xs.size());if(n==0){content.addView(txt("Şu an filtreden geçen aday yok; filtre zorlanmıyor ve "+budget+" TL nakit korunuyor.",14,RED));spacer(8);return;}int per=budget/n;content.addView(txt("Aday başına hedef bütçe yaklaşık "+per+" TL",11,Color.GRAY));int used=0;for(int i=0;i<n;i++){RadarItem r=xs.get(i);MarketDataService.Spot live=MarketDataService.latestSpot(r.symbol);double px=live!=null&&live.price>0?live.price:r.price;int lots=px>0?Math.max(0,(int)Math.floor(per/px)):0;used+=(int)Math.round(lots*px);LinearLayout c=card();c.setBackgroundColor(NAVY2);c.addView(bold((i+1)+". "+r.symbol+"  •  "+r.recommendation,17,color));c.addView(txt(money(px,r.symbol)+"  •  yaklaşık "+lots+" lot  •  Pulse "+fmt(r.score)+"  •  Güven %"+(int)r.confidence,13,Color.rgb(180,202,218)));if(lots==0)c.addView(txt("Aday başı bütçe mevcut fiyatla 1 lot için yetersiz.",11,AMBER));c.addView(txt(r.horizon+"  •  "+r.why,12,Color.GRAY));if(findHolding(r.symbol)!=null)c.addView(txt("Mevcut portföy pozisyonu",11,NAVY2));LinearLayout actions=new LinearLayout(this);Button d=button("Grafik / Tavsiye",color),add=button(findHolding(r.symbol)==null?"Portföye Ekle":"Pozisyonu Düzenle",findHolding(r.symbol)==null?GREEN:AMBER);actions.addView(d,new LinearLayout.LayoutParams(0,-2,1));actions.addView(add,new LinearLayout.LayoutParams(0,-2,1));c.addView(actions);d.setOnClickListener(v->analyzeStock(r.symbol));add.setOnClickListener(v->portfolioDialog(findHolding(r.symbol),r.symbol));c.setOnClickListener(v->analyzeStock(r.symbol));content.addView(c);spacer(5);}content.addView(txt("Yaklaşık kullanım "+used+" TL  •  Nakit "+Math.max(0,budget-used)+" TL  •  "+n+" aday",12,Color.GRAY));content.addView(txt("Lot hesabı yaklaşık model dağılımıdır; emir oluşturmaz.",10,Color.GRAY));spacer(6);}

    private void savePortfolio(){JSONArray a=new JSONArray();try{for(Holding h:holdings){JSONObject o=new JSONObject();o.put("s",h.symbol);o.put("q",h.qty);o.put("c",h.cost);a.put(o);}}catch(Exception ignored){}getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("portfolio",a.toString()).apply();}
    private void loadPortfolio(){holdings.clear();try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("portfolio","[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);holdings.add(new Holding(o.getString("s"),o.getInt("q"),o.getDouble("c")));}}catch(Exception ignored){}}
    private void saveRadarCache(){JSONArray a=new JSONArray();try{int n=Math.min(80,radarResults.size());for(int i=0;i<n;i++){RadarItem r=radarResults.get(i);JSONObject o=new JSONObject();o.put("s",r.symbol);o.put("r",r.recommendation);o.put("w",r.why);o.put("h",r.horizon);o.put("p",r.price);o.put("sc",r.score);o.put("cf",r.confidence);a.put(o);}}catch(Exception ignored){}getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("radar",a.toString()).apply();}
    private void loadRadarCache(){radarResults.clear();try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("radar","[]"));for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);ShortPulseEngine.Result pr=new ShortPulseEngine.Result();pr.recommendation=o.getString("r");pr.explanation=o.getString("w");pr.horizonText=o.getString("h");pr.price=o.getDouble("p");pr.score=o.getDouble("sc");pr.confidence=o.getDouble("cf");radarResults.add(new RadarItem(o.getString("s"),pr));}}catch(Exception ignored){}}

    private void prefetchTimeframes(String symbol) {
        // Grafik açıldıktan sonra diğer görünür zaman dilimlerini cache'e hazırla.
        // Seçili grafik zaten ekranda; bu işlem sadece sonraki dokunuşları hızlandırır.
        final String s=symbol; final int generation=detailRequestGeneration.get();
        io.execute(()->{
            for(int idx:new int[]{5,3,7,8}){
                if(generation!=detailRequestGeneration.get()||!s.equals(detailSymbol))return;
                if(idx==detailTimeframe)continue;
                try{
                    List<MarketDataService.Candle> d=DetailedChartController.cached(s,idx);
                    if(d==null||d.size()<2)DetailedChartController.fetch(s,idx);
                }catch(Exception ignored){}
            }
        });
    }

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
