from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Add lightweight in-app navigation history. Each shell change records the prior screen via a numeric route.
# Route: 0 portfolio, 1 radar, 2 hourly, 3 single-stock entry, 4 baskets.
anchor='public class MainActivity extends Activity {'
if anchor not in s: raise SystemExit('activity anchor missing')
s=s.replace(anchor,anchor+'\n    private final java.util.ArrayDeque<Integer> navHistory=new java.util.ArrayDeque<>();\n    private int currentRoute=0;\n    private boolean navigatingBack=false;',1)
# Track routes at stable public screen methods.
def route(sig,num):
 global s
 needle=sig+' {'
 if needle in s:
  s=s.replace(needle,needle+'\n        pushRoute('+str(num)+');',1)
route('private void showPortfolio()',0)
route('private void showRadar()',1)
route('private void showHourlyRadar()',2)
route('private void showBaskets()',4)
# singleStockDialog is a dialog, don't add route if signature differs.
helper='''\n    private void pushRoute(int route){\n        if(navigatingBack){currentRoute=route;return;}\n        if(route!=currentRoute){navHistory.push(currentRoute);currentRoute=route;}\n    }\n\n    private void openRoute(int route){\n        navigatingBack=true;\n        try{\n            currentRoute=route;\n            if(route==1)showRadar();\n            else if(route==2)showHourlyRadar();\n            else if(route==4)showBaskets();\n            else showPortfolio();\n        }finally{navigatingBack=false;}\n    }\n\n    @Override public void onBackPressed(){\n        // Android back first returns to the previous BorsaRadar screen.\n        if(!navHistory.isEmpty()){openRoute(navHistory.pop());return;}\n        // From any non-home screen fall back to Portfolio instead of closing.\n        if(currentRoute!=0){openRoute(0);return;}\n        // On Portfolio require a second back press to exit, preventing accidental closure.\n        long now=System.currentTimeMillis();\n        android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);\n        long last=sp.getLong("last_back_exit",0L);\n        if(now-last<1800L){super.onBackPressed();}\n        else{sp.edit().putLong("last_back_exit",now).apply();Toast.makeText(this,"Çıkmak için tekrar geri bas",Toast.LENGTH_SHORT).show();}\n    }\n'''
# Insert before final class brace.
pos=s.rfind('}')
if pos<0: raise SystemExit('class end missing')
s=s[:pos]+helper+s[pos:]
p.write_text(s,encoding='utf-8')
