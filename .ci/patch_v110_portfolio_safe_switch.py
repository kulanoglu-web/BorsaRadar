from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v110: replace portfolio selector with a no-recursion, no-save, guarded switch.
a=s.find('    private LinearLayout portfolioMarketSelector(){')
if a>=0:
    b=s.find('    private void showPortfolio()',a)
    if b<0: raise SystemExit('portfolio selector end missing')
    helper='''    private LinearLayout portfolioMarketSelector(){
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
        String[] labels={"BIST","ALMANYA","ABD"};
        int cur=primaryMarket();if(cur<0||cur>2)cur=0;
        for(int i=0;i<3;i++){
            final int target=i;Button btn=button(labels[i],cur==i?GREEN:NAVY2);
            btn.setEnabled(target!=cur);
            btn.setOnClickListener(v->switchPortfolioMarket(target));
            row.addView(btn,new LinearLayout.LayoutParams(0,-2,1));
        }
        return row;
    }
    private void switchPortfolioMarket(int target){
        if(target<0||target>2)return;
        int old=primaryMarket();if(old==target)return;
        try{
            android.content.SharedPreferences sp=getSharedPreferences(PREFS,Context.MODE_PRIVATE);
            sp.edit().putInt("primary_market",target).putInt("active_profile",target).apply();
            holdings.clear();holdingSignals.clear();holdingContexts.clear();
            loadPortfolio();
            main.post(this::showPortfolio);
        }catch(Throwable t){
            getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putInt("primary_market",old).putInt("active_profile",old).apply();
            try{loadPortfolio();}catch(Throwable ignored){}
            Toast.makeText(this,"Portföy geçişi başarısız: "+t.getClass().getSimpleName(),Toast.LENGTH_LONG).show();
        }
    }

'''
    s=s[:a]+helper+s[b:]
# Do not let malformed persisted JSON kill portfolio screen.
old='''        }catch(Exception e){}
    }

    private void savePortfolio()'''
new='''        }catch(Throwable e){holdings.clear();}
    }

    private void savePortfolio()'''
if old in s:s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
