from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v91 portable backup/restore: all 3 real portfolio profiles + fake portfolio.
anchor='    private android.view.View pnlBar(final double pct){'
helpers='''    private String portfolioBackupJson(){
        try{
            JSONObject root=new JSONObject(); root.put("format","BorsaRadarPortfolioBackup"); root.put("version",2); root.put("createdAt",System.currentTimeMillis());
            android.content.SharedPreferences sp=getSharedPreferences(PREFS,MODE_PRIVATE);
            JSONObject profiles=new JSONObject();
            for(int m=0;m<3;m++) profiles.put(String.valueOf(m),new JSONArray(sp.getString("portfolio_"+m,"[]")));
            root.put("realProfiles",profiles); root.put("activeProfile",primaryMarket());
            JSONObject fake=new JSONObject(); android.content.SharedPreferences fp=getSharedPreferences("paper_portfolio",MODE_PRIVATE);
            for(java.util.Map.Entry<String,?> e:fp.getAll().entrySet()) fake.put(e.getKey(),String.valueOf(e.getValue()));
            root.put("fake",fake); return root.toString(2);
        }catch(Exception e){return null;}
    }
    private void backupPortfolios(){
        try{String json=portfolioBackupJson(); if(json==null)throw new Exception("json");
            Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT); i.addCategory(Intent.CATEGORY_OPENABLE); i.setType("application/json"); i.putExtra(Intent.EXTRA_TITLE,"BorsaRadar-Portfoy-Yedek.json");
            pendingPortfolioBackupJson=json; startActivityForResult(i,990);
        }catch(Exception e){Toast.makeText(this,"Yedek oluşturulamadı",Toast.LENGTH_LONG).show();}
    }
    private String pendingPortfolioBackupJson=null;
    private void choosePortfolioBackup(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");startActivityForResult(i,991);}
    private void restorePortfolioBackup(android.net.Uri uri,boolean replace){
        try{String json;try(java.io.InputStream in=getContentResolver().openInputStream(uri)){java.util.Scanner sc=new java.util.Scanner(in,"UTF-8").useDelimiter("\\A");json=sc.hasNext()?sc.next():"";}
            JSONObject root=new JSONObject(json);if(!"BorsaRadarPortfolioBackup".equals(root.optString("format")))throw new Exception("format");
            android.content.SharedPreferences sp=getSharedPreferences(PREFS,MODE_PRIVATE); android.content.SharedPreferences.Editor pe=sp.edit();
            JSONObject profiles=root.optJSONObject("realProfiles");
            if(profiles!=null){for(int m=0;m<3;m++){String key="portfolio_"+m;JSONArray incoming=profiles.optJSONArray(String.valueOf(m));if(incoming==null)continue;if(replace){pe.putString(key,incoming.toString());}else{JSONArray merged=new JSONArray(sp.getString(key,"[]"));java.util.HashSet<String> seen=new java.util.HashSet<>();for(int j=0;j<merged.length();j++)seen.add(merged.optJSONObject(j).optString("s"));for(int j=0;j<incoming.length();j++){JSONObject o=incoming.optJSONObject(j);if(o!=null&&!seen.contains(o.optString("s"))){merged.put(o);seen.add(o.optString("s"));}}pe.putString(key,merged.toString());}}}
            else {JSONArray old=root.optJSONArray("real");if(old!=null){JSONArray converted=replace?new JSONArray():new JSONArray(sp.getString("portfolio_"+primaryMarket(),"[]"));java.util.HashSet<String> seen=new java.util.HashSet<>();for(int j=0;j<converted.length();j++)seen.add(converted.optJSONObject(j).optString("s"));for(int j=0;j<old.length();j++){JSONObject o=old.getJSONObject(j);String sy=o.getString("symbol");if(!seen.contains(sy)){JSONObject n=new JSONObject();n.put("s",sy);n.put("q",o.getInt("qty"));n.put("c",o.getDouble("cost"));converted.put(n);seen.add(sy);}}pe.putString("portfolio_"+primaryMarket(),converted.toString());}}
            pe.apply();
            android.content.SharedPreferences.Editor fe=getSharedPreferences("paper_portfolio",MODE_PRIVATE).edit();if(replace)fe.clear();JSONObject fake=root.optJSONObject("fake");if(fake!=null){java.util.Iterator<String> it=fake.keys();while(it.hasNext()){String k=it.next();fe.putString(k,fake.optString(k));}}fe.apply();
            loadPortfolio();Toast.makeText(this,"Gerçek + Fake portföy geri yüklendi",Toast.LENGTH_LONG).show();showPortfolio();
        }catch(Exception e){Toast.makeText(this,"Yedek okunamadı veya uyumsuz",Toast.LENGTH_LONG).show();}
    }
    private void handlePortfolioFileResult(int requestCode,int resultCode,Intent data){
        if(resultCode!=RESULT_OK||data==null||data.getData()==null)return; final android.net.Uri u=data.getData();
        if(requestCode==990&&pendingPortfolioBackupJson!=null){try(java.io.OutputStream out=getContentResolver().openOutputStream(u)){out.write(pendingPortfolioBackupJson.getBytes(java.nio.charset.StandardCharsets.UTF_8));Toast.makeText(this,"Portföy yedeği kaydedildi",Toast.LENGTH_LONG).show();}catch(Exception e){Toast.makeText(this,"Yedek kaydedilemedi",Toast.LENGTH_LONG).show();}finally{pendingPortfolioBackupJson=null;}}
        else if(requestCode==991){new AlertDialog.Builder(this).setTitle("Portföy yedeğini geri yükle").setMessage("Birleştir mevcut kayıtları korur. Yerine koy üç Gerçek portföyü ve Fake portföyü yedekteki kayıtlarla değiştirir.").setPositiveButton("Birleştir",(d,w)->restorePortfolioBackup(u,false)).setNegativeButton("Yerine koy",(d,w)->restorePortfolioBackup(u,true)).setNeutralButton("İptal",null).show();}
    }
    private LinearLayout portfolioBackupControls(){LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);Button backup=button("⬆ Yedekle",NAVY2),restore=button("⬇ Geri Yükle",Color.rgb(75,85,105));row.addView(backup,new LinearLayout.LayoutParams(0,-2,1));row.addView(restore,new LinearLayout.LayoutParams(0,-2,1));backup.setOnClickListener(v->backupPortfolios());restore.setOnClickListener(v->choosePortfolioBackup());return row;}
'''
if anchor not in s: raise SystemExit('v90 pnl anchor missing')
s=s.replace(anchor,helpers+anchor,1)
# showPortfolio already calls shell("Portföy"), which creates content. Put controls immediately after it.
needle='        shell("Portföy");'
if needle not in s: raise SystemExit('portfolio shell anchor missing')
s=s.replace(needle,needle+'\n        content.addView(portfolioBackupControls()); spacer(6);',1)
# Integrate with an existing onActivityResult if present; otherwise create one before pnlBar.
if 'protected void onActivityResult(' in s:
    old='super.onActivityResult(requestCode,resultCode,data);'
    if old not in s: raise SystemExit('existing onActivityResult has no super anchor')
    s=s.replace(old,old+' handlePortfolioFileResult(requestCode,resultCode,data);',1)
else:
    method='    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){super.onActivityResult(requestCode,resultCode,data);handlePortfolioFileResult(requestCode,resultCode,data);}\n'
    s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding='utf-8')
