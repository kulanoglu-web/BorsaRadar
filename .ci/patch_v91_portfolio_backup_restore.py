from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')
# v91 portable backup/restore: real portfolio + fake portfolio, versioned JSON, shareable to Files/Drive/etc.
s=s.replace('import android.content.Intent;','import android.content.Intent;\nimport android.content.ClipData;')
# Add helpers before collapsible section.
anchor='    private android.view.View pnlBar(final double pct){'
helpers='''    private String portfolioBackupJson(){
        try{
            JSONObject root=new JSONObject(); root.put("format","BorsaRadarPortfolioBackup"); root.put("version",1); root.put("createdAt",System.currentTimeMillis());
            JSONArray real=new JSONArray(); for(Holding h:holdings){JSONObject o=new JSONObject();o.put("symbol",h.symbol);o.put("qty",h.qty);o.put("cost",h.cost);real.put(o);} root.put("real",real);
            JSONObject fake=new JSONObject(); android.content.SharedPreferences fp=getSharedPreferences("paper_portfolio",MODE_PRIVATE); for(java.util.Map.Entry<String,?> e:fp.getAll().entrySet()) fake.put(e.getKey(),String.valueOf(e.getValue())); root.put("fake",fake);
            return root.toString(2);
        }catch(Exception e){return null;}
    }
    private void backupPortfolios(){
        try{String json=portfolioBackupJson(); if(json==null)throw new Exception("json"); java.io.File dir=new java.io.File(getCacheDir(),"backup");dir.mkdirs();java.io.File f=new java.io.File(dir,"BorsaRadar-Portfoy-Yedek.json");try(java.io.FileOutputStream out=new java.io.FileOutputStream(f)){out.write(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
            android.net.Uri uri=androidx.core.content.FileProvider.getUriForFile(this,getPackageName()+".fileprovider",f); Intent i=new Intent(Intent.ACTION_SEND);i.setType("application/json");i.putExtra(Intent.EXTRA_STREAM,uri);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivity(Intent.createChooser(i,"Portföy yedeğini kaydet"));
        }catch(Exception e){Toast.makeText(this,"Yedek oluşturulamadı",Toast.LENGTH_LONG).show();}
    }
    private void choosePortfolioBackup(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");startActivityForResult(i,991);}
    private void restorePortfolioBackup(android.net.Uri uri,boolean replace){
        try{String json;try(java.io.InputStream in=getContentResolver().openInputStream(uri)){java.util.Scanner sc=new java.util.Scanner(in,"UTF-8").useDelimiter("\\\\A");json=sc.hasNext()?sc.next():"";} JSONObject root=new JSONObject(json);if(!"BorsaRadarPortfolioBackup".equals(root.optString("format")))throw new Exception("format");
            if(replace){holdings.clear();getSharedPreferences("paper_portfolio",MODE_PRIVATE).edit().clear().apply();}
            JSONArray real=root.optJSONArray("real"); if(real!=null)for(int x=0;x<real.length();x++){JSONObject o=real.getJSONObject(x);String sy=o.getString("symbol");int q=o.getInt("qty");double c=o.getDouble("cost");boolean found=false;for(Holding h:holdings)if(h.symbol.equals(sy)){found=true;break;}if(!found)holdings.add(new Holding(sy,q,c));}
            JSONObject fake=root.optJSONObject("fake");if(fake!=null){android.content.SharedPreferences.Editor ed=getSharedPreferences("paper_portfolio",MODE_PRIVATE).edit();java.util.Iterator<String> it=fake.keys();while(it.hasNext()){String k=it.next();ed.putString(k,fake.optString(k));}ed.apply();}
            savePortfolio();Toast.makeText(this,"Gerçek + Fake portföy geri yüklendi",Toast.LENGTH_LONG).show();showPortfolio();
        }catch(Exception e){Toast.makeText(this,"Yedek okunamadı veya uyumsuz",Toast.LENGTH_LONG).show();}
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){super.onActivityResult(requestCode,resultCode,data);if(requestCode==991&&resultCode==RESULT_OK&&data!=null&&data.getData()!=null){android.net.Uri u=data.getData();new AlertDialog.Builder(this).setTitle("Portföy yedeğini geri yükle").setMessage("Birleştir mevcut kayıtları korur. Yerine koy mevcut Gerçek ve Fake portföyü yedekteki kayıtlarla değiştirir.").setPositiveButton("Birleştir",(d,w)->restorePortfolioBackup(u,false)).setNegativeButton("Yerine koy",(d,w)->restorePortfolioBackup(u,true)).setNeutralButton("İptal",null).show();}}
'''
if anchor not in s: raise SystemExit('v90 pnl anchor missing')
s=s.replace(anchor,helpers+anchor,1)
# Add backup controls to portfolio screen after shell.
needle='        shell("Portföy");'
repl='''        shell("Portföy");
        LinearLayout backupRow=new LinearLayout(this);backupRow.setOrientation(LinearLayout.HORIZONTAL);Button backup=button("⬆ Yedekle",NAVY2),restore=button("⬇ Geri Yükle",Color.rgb(75,85,105));backupRow.addView(backup,new LinearLayout.LayoutParams(0,-2,1));backupRow.addView(restore,new LinearLayout.LayoutParams(0,-2,1));content.addView(backupRow);spacer(6);backup.setOnClickListener(v->backupPortfolios());restore.setOnClickListener(v->choosePortfolioBackup());'''
if needle not in s: raise SystemExit('portfolio shell missing')
s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')

# FileProvider for portable backup share.
m=Path('app/src/main/AndroidManifest.xml');ms=m.read_text(encoding='utf-8')
if 'androidx.core.content.FileProvider' not in ms:
    provider='''\n        <provider android:name="androidx.core.content.FileProvider" android:authorities="${applicationId}.fileprovider" android:exported="false" android:grantUriPermissions="true"><meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths" /></provider>'''
    ms=ms.replace('</application>',provider+'\n    </application>')
m.write_text(ms,encoding='utf-8')
x=Path('app/src/main/res/xml');x.mkdir(parents=True,exist_ok=True);(x/'file_paths.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<paths xmlns:android="http://schemas.android.com/apk/res/android"><cache-path name="backup" path="backup/" /></paths>\n',encoding='utf-8')
