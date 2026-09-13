from pathlib import Path
p=Path('app/src/main/java/com/kulanoglu/borsaradar/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Ensure required imports exist even when older patch search patterns no longer match.
if 'import android.app.Notification;' not in s:
    s=s.replace('import android.app.Activity;','import android.app.Activity;\nimport android.app.Notification;\nimport android.app.NotificationChannel;\nimport android.app.NotificationManager;\nimport android.app.PendingIntent;')
if 'import android.content.Intent;' not in s:
    s=s.replace('import android.content.Context;','import android.content.Context;\nimport android.content.Intent;\nimport android.net.Uri;\nimport android.os.Build;')

helpers='''
    private void setupAlerts(){
        NotificationManager nm=(NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);
        if(Build.VERSION.SDK_INT>=26){
            NotificationChannel ch=new NotificationChannel("borsaradar_alerts","BorsaRadar V35 Alarmları",NotificationManager.IMPORTANCE_HIGH);
            ch.setDescription("V35 fırsat, kâr koruma ve zarar önleme uyarıları");
            nm.createNotificationChannel(ch);
        }
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=android.content.pm.PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},901);
        }
    }

    private void handleNotificationIntent(Intent i){
        if(i==null)return;
        final String symbol=i.getStringExtra("open_symbol");
        if(symbol!=null && !symbol.trim().isEmpty()){
            i.removeExtra("open_symbol");
            main.postDelayed(()->analyzeStock(symbol.trim()),180);
        }
    }

    @Override protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);
        setIntent(intent);
        handleNotificationIntent(intent);
    }
'''

# Append only helpers that are genuinely missing.
need=''
if 'private void setupAlerts()' not in s:
    need += helpers.split('    private void handleNotificationIntent')[0]
if 'private void handleNotificationIntent(Intent i)' not in s:
    tail='    private void handleNotificationIntent'+helpers.split('    private void handleNotificationIntent',1)[1]
    need += tail
if need:
    pos=s.rfind('}')
    s=s[:pos]+need+'\n'+s[pos:]

p.write_text(s,encoding='utf-8')
