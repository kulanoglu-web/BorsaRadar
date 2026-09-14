from pathlib import Path
import re

p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Needed for rounded cards/buttons.
if 'import android.graphics.drawable.GradientDrawable;' not in s:
    s=s.replace('import android.graphics.Typeface;','import android.graphics.Typeface;\nimport android.graphics.drawable.GradientDrawable;')

# Add compact style helpers once.
anchor='    private int dp(int x) { return Math.round(x * getResources().getDisplayMetrics().density); }'
helpers='''    private int uiTextColor(int color) {
        if(color==NAVY) return Color.rgb(244,247,250);
        if(color==NAVY2) return Color.rgb(207,216,226);
        if(color==Color.DKGRAY) return Color.rgb(196,202,210);
        if(color==Color.GRAY) return Color.rgb(150,158,168);
        return color;
    }

    private GradientDrawable roundedBg(int color,int radiusDp){
        GradientDrawable g=new GradientDrawable();
        g.setColor(color); g.setCornerRadius(dp(radiusDp));
        return g;
    }
'''
if 'private int uiTextColor(int color)' not in s and anchor in s:
    s=s.replace(anchor,anchor+'\n\n'+helpers,1)

# Dark text/card primitives inspired by the two reference trading apps.
pat=r'''    private TextView txt\(String text, int sp, int color\) \{.*?\n    \}\n\n    private TextView bold'''
rep='''    private TextView txt(String text, int sp, int color) {
        TextView v=new TextView(this);
        v.setText(text); v.setTextSize(sp); v.setTextColor(uiTextColor(color));
        v.setPadding(dp(14),dp(8),dp(14),dp(8));
        return v;
    }

    private TextView bold'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: print('txt primitive already changed or not found')

pat=r'''    private Button button\(String text, int color\) \{.*?\n    \}\n\n    private void spacer'''
rep='''    private Button button(String text, int color) {
        Button b=new Button(this);
        b.setText(text); b.setAllCaps(false); b.setTextColor(Color.WHITE); b.setTextSize(14);
        b.setBackground(roundedBg(color,12)); b.setPadding(dp(10),dp(8),dp(10),dp(8));
        b.setMinHeight(dp(44));
        return b;
    }

    private void spacer'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: print('button primitive already changed or not found')

pat=r'''    private LinearLayout card\(\) \{.*?\n    \}\n\n    private void shell'''
rep='''    private LinearLayout card() {
        LinearLayout c=new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setPadding(dp(14),dp(12),dp(14),dp(12));
        c.setBackground(roundedBg(Color.rgb(29,33,39),16));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.setMargins(0,dp(4),0,dp(4)); c.setLayoutParams(lp);
        c.setElevation(dp(2));
        return c;
    }

    private void shell'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1: print('card primitive already changed or not found')

# Final shell: compact dark trading layout with top search-like title and bottom nav.
# On a global stock detail screen, header market follows the viewed stock rather than
# the active portfolio profile, so US:NVDA never shows a BIST badge/breadcrumb.
pat=r'''    private void shell\(String page\) \{.*?\n    \}\n\n    private void showPortfolio\(\)'''
rep='''    private void shell(String page) {
        final int SURFACE=Color.rgb(18,21,25), CARD=Color.rgb(29,33,39), MUTED=Color.rgb(151,160,171), ACCENT=Color.rgb(219,45,55);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(SURFACE);

        int shellMarket=primaryMarket();
        int split=page.indexOf(" •");
        if(split>0){
            String maybeSymbol=page.substring(0,split).trim();
            if(MarketDataService.isGlobalSymbol(maybeSymbol)) shellMarket=MarketSymbol.marketIndex(maybeSymbol);
        }
        final int displayMarket=shellMarket;

        LinearLayout head=new LinearLayout(this); head.setOrientation(LinearLayout.VERTICAL); head.setPadding(dp(14),dp(10),dp(14),dp(8)); head.setBackgroundColor(Color.rgb(21,25,30));
        LinearLayout titleRow=new LinearLayout(this); titleRow.setOrientation(LinearLayout.HORIZONTAL); titleRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView logo=bold("BR",20,Color.WHITE); logo.setGravity(Gravity.CENTER); logo.setBackground(roundedBg(ACCENT,10)); logo.setPadding(dp(10),dp(7),dp(10),dp(7));
        titleRow.addView(logo,new LinearLayout.LayoutParams(-2,-2));
        TextView title=bold(page,18,Color.WHITE); title.setPadding(dp(10),0,dp(6),0); titleRow.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        Button intl=button("🌐 "+uiLang()+" • "+marketShort(displayMarket),Color.rgb(48,54,62)); intl.setTextSize(12); titleRow.addView(intl,new LinearLayout.LayoutParams(-2,-2)); head.addView(titleRow);
        TextView sub=txt(marketName(displayMarket)+"  •  BorsaRadar",11,MUTED); sub.setPadding(dp(2),dp(4),0,0); head.addView(sub); root.addView(head);
        intl.setOnClickListener(v->showInternationalSetup());

        ScrollView sv=new ScrollView(this); sv.setFillViewport(true); content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(10),dp(8),dp(10),dp(14)); sv.addView(content); root.addView(sv,new LinearLayout.LayoutParams(-1,0,1));

        LinearLayout nav=new LinearLayout(this); nav.setOrientation(LinearLayout.HORIZONTAL); nav.setPadding(dp(6),dp(5),dp(6),dp(7)); nav.setBackgroundColor(Color.rgb(21,25,30));
        Button p=button("⌂\n"+L("Portföy","Portfolio","Portfolio"),Color.rgb(42,47,54));
        Button r=button("↗\n"+L("Radar","Radar","Radar"),ACCENT);
        Button one=button("⌕\n"+L("Tek Hisse","Einzeltitel","Single"),Color.rgb(42,47,54));
        Button three=button("▦\n"+L("3 Sepet","3 Körbe","3 Baskets"),Color.rgb(42,47,54));
        for(Button b:new Button[]{p,r,one,three}){b.setTextSize(11);b.setMinHeight(dp(50));}
        nav.addView(p,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(r,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(one,new LinearLayout.LayoutParams(0,-2,1)); nav.addView(three,new LinearLayout.LayoutParams(0,-2,1));
        p.setOnClickListener(v->showPortfolio()); r.setOnClickListener(v->showRadar()); one.setOnClickListener(v->singleStockDialog()); three.setOnClickListener(v->showBaskets()); root.addView(nav);
        setContentView(root);
    }

    private void showPortfolio()'''
s,n=re.subn(pat,rep,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('shell method not found for inspired UI')

# Make the key holding action resemble trading apps: large chart/analysis call-to-action.
s=s.replace('button("Grafik / Tavsiye",NAVY2)','button("Grafik • Analiz • Sinyal",Color.rgb(50,56,64))')

# Stronger AL/SAT presentation while preserving signal semantics.
s=s.replace('TextView v=bold(s.recommendation+"  •  Pulse "+fmt(s.score),20,Color.WHITE);','TextView v=bold(s.recommendation+"   •   Pulse "+fmt(s.score)+"   •   Güven %"+(int)s.confidence,19,Color.WHITE);')

# Version bump.
b=Path('app/build.gradle')
g=b.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 50',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]","versionName '3.12.2'",g)
b.write_text(g,encoding='utf-8')

p.write_text(s,encoding='utf-8')
