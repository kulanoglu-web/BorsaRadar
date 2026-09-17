from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# ONLY back-navigation from stock detail in this patch.
# Existing route history tracks top-level screens but detail rendering never becomes a route,
# so Android Back can skip the screen that opened the detail. Capture that route before detail opens.
anchor='    private boolean navigatingBack=false;'
if anchor not in s: raise SystemExit('navigation state anchor missing')
if 'detailReturnRoute' not in s:
    s=s.replace(anchor,anchor+'\n    private int detailReturnRoute=-1;\n    private boolean detailScreenOpen=false;',1)
# Mark detail entry at both renderers without pushing a synthetic route.
for sig in ['private void renderFastTechnicalDetail(String symbol,List<MarketDataService.Candle> data){','private void renderStockDetail(String symbol,FullAnalysisEngine.Result a,List<MarketDataService.Candle> data,String frame){']:
    pos=s.find(sig)
    if pos<0: raise SystemExit('detail renderer missing: '+sig)
    ins=pos+len(sig)
    mark='\n        if(!detailScreenOpen){detailReturnRoute=currentRoute;detailScreenOpen=true;}'
    if mark.strip() not in s[pos:pos+500]: s=s[:ins]+mark+s[ins:]
# When a top-level route is explicitly opened, detail mode ends.
needle='private void openRoute(int route){\n        navigatingBack=true;'
repl='private void openRoute(int route){\n        detailScreenOpen=false;detailReturnRoute=-1;\n        navigatingBack=true;'
if needle not in s: raise SystemExit('openRoute anchor missing')
s=s.replace(needle,repl,1)
# Back from detail must first restore the exact top-level screen that opened it.
needle='''    @Override public void onBackPressed(){
        // Android back first returns to the previous BorsaRadar screen.
        if(!navHistory.isEmpty()){openRoute(navHistory.pop());return;}'''
repl='''    @Override public void onBackPressed(){
        // Stock detail: return to the screen that actually opened this detail.
        if(detailScreenOpen){int r=detailReturnRoute;detailScreenOpen=false;detailReturnRoute=-1;openRoute(r<0?currentRoute:r);return;}
        // Android back first returns to the previous BorsaRadar screen.
        if(!navHistory.isEmpty()){openRoute(navHistory.pop());return;}'''
if needle not in s: raise SystemExit('back handler anchor missing')
s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')
s=p.read_text(encoding='utf-8')
checks={'detail route field':'detailReturnRoute=-1' in s,'detail state field':'detailScreenOpen=false' in s,'fast detail marked':'renderFastTechnicalDetail' in s and 'if(!detailScreenOpen){detailReturnRoute=currentRoute;detailScreenOpen=true;}' in s,'back detail branch':'if(detailScreenOpen){int r=detailReturnRoute' in s,'old history preserved':'if(!navHistory.isEmpty()){openRoute(navHistory.pop());return;}' in s}
for k,v in checks.items(): print('v141',k,v)
if not all(checks.values()): raise SystemExit('v141 verification FAILED')
