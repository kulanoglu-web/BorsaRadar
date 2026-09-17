from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# ONLY back-navigation from stock detail in this patch.
anchor='    private boolean navigatingBack=false;'
if anchor not in s: raise SystemExit('navigation state anchor missing')
if 'detailReturnRoute' not in s:
    s=s.replace(anchor,anchor+'\n    private int detailReturnRoute=-1;\n    private boolean detailScreenOpen=false;',1)
mark='\n        if(!detailScreenOpen){detailReturnRoute=currentRoute;detailScreenOpen=true;}'
# Fast detail renderer is stable.
pos=s.find('private void renderFastTechnicalDetail(')
if pos<0: raise SystemExit('fast detail renderer missing')
brace=s.find('{',pos)
if brace<0: raise SystemExit('fast detail brace missing')
if mark.strip() not in s[brace:brace+500]:s=s[:brace+1]+mark+s[brace+1:]
# Deep detail signature has been transformed by older patches; match method name rather than exact parameters.
pos=s.find('private void renderStockDetail(')
if pos<0: raise SystemExit('deep detail renderer missing')
brace=s.find('{',pos)
if brace<0: raise SystemExit('deep detail brace missing')
if mark.strip() not in s[brace:brace+500]:s=s[:brace+1]+mark+s[brace+1:]
needle='private void openRoute(int route){\n        navigatingBack=true;'
repl='private void openRoute(int route){\n        detailScreenOpen=false;detailReturnRoute=-1;\n        navigatingBack=true;'
if needle not in s: raise SystemExit('openRoute anchor missing')
s=s.replace(needle,repl,1)
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
checks={'detail route field':'detailReturnRoute=-1' in s,'detail state field':'detailScreenOpen=false' in s,'fast detail marked':'renderFastTechnicalDetail' in s and mark.strip() in s,'deep detail exists':'private void renderStockDetail(' in s,'back detail branch':'if(detailScreenOpen){int r=detailReturnRoute' in s,'old history preserved':'if(!navHistory.isEmpty()){openRoute(navHistory.pop());return;}' in s}
for k,v in checks.items(): print('v141',k,v)
if not all(checks.values()): raise SystemExit('v141 verification FAILED')
