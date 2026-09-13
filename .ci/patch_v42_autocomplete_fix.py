from pathlib import Path
import re
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Force suggestion dropdown on every typed character and keep adapter synced with selected market.
def inject_after(var):
    needle=f'{var}.setThreshold(1); {var}.setSingleLine(true);'
    repl=needle+f'''\n        {var}.addTextChangedListener(new android.text.TextWatcher(){{
            @Override public void beforeTextChanged(CharSequence cs,int st,int c,int a){{}}
            @Override public void onTextChanged(CharSequence cs,int st,int before,int count){{
                if(cs!=null && cs.length()>=1) {var}.post(()->{{ if({var}.hasFocus()) {var}.showDropDown(); }});
            }}
            @Override public void afterTextChanged(android.text.Editable e){{}}
        }});'''
    return repl

s=s.replace('sym.setThreshold(1); sym.setSingleLine(true);',inject_after('sym'))
s=s.replace('x.setThreshold(1); x.setSingleLine(true);',inject_after('x'))

# Set an adapter immediately, not only after Spinner callback.
s=s.replace('''        market.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> p,android.view.View v,int pos,long id){
                String[] a=pos==1?GlobalStockUniverse.GERMANY:pos==2?GlobalStockUniverse.USA:BistUniverse.ENTRIES;
                sym.setAdapter(new ArrayAdapter<>(MainActivity.this,android.R.layout.simple_dropdown_item_1line,a));
            }''','''        sym.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,BistUniverse.ENTRIES));
        market.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> p,android.view.View v,int pos,long id){
                String[] a=pos==1?GlobalStockUniverse.GERMANY:pos==2?GlobalStockUniverse.USA:BistUniverse.ENTRIES;
                sym.setAdapter(new ArrayAdapter<>(MainActivity.this,android.R.layout.simple_dropdown_item_1line,a));
                if(sym.getText().length()>0) sym.post(sym::showDropDown);
            }''')

s=s.replace('''        market.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> p,android.view.View v,int pos,long id){
                String[] a=pos==1?GlobalStockUniverse.GERMANY:pos==2?GlobalStockUniverse.USA:BistUniverse.ENTRIES;
                x.setAdapter(new ArrayAdapter<>(MainActivity.this,android.R.layout.simple_dropdown_item_1line,a));
            }''','''        x.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,BistUniverse.ENTRIES));
        market.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> p,android.view.View v,int pos,long id){
                String[] a=pos==1?GlobalStockUniverse.GERMANY:pos==2?GlobalStockUniverse.USA:BistUniverse.ENTRIES;
                x.setAdapter(new ArrayAdapter<>(MainActivity.this,android.R.layout.simple_dropdown_item_1line,a));
                if(x.getText().length()>0) x.post(x::showDropDown);
            }''')

# Better hint.
s=s.replace('Harf yaz: THY / SAP / NVD','Bir harf yaz: örn. T, S, N')
p.write_text(s,encoding='utf-8')
