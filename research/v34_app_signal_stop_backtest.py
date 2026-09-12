import json
from datetime import datetime, timezone
from pathlib import Path
import backtest_indicators as bi
import v33_app_signal_backtest as v33

START=100000.0;FEE=.001;MAX_POS=5;MAX_HOLD=10

def dt(t): return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')

def run():
    dates=bi.dates;cash=START;pos={};pending={};tr=[];peak=START;dd=0
    for day in dates:
        # önce bekleyen kapanış sinyallerini bugünkü açılışta uygula
        for s,cmd in list(pending.items()):
            i=bi.bysym.get(s,{}).get(day)
            if i is None: continue
            bar=bi.data[s][i]
            if cmd['kind']=='BUY' and s not in pos and len(pos)<MAX_POS:
                slots=max(1,MAX_POS-len(pos));alloc=min(cash/slots,START/MAX_POS)
                q=int(alloc/(bar['o']*(1+FEE)))
                if q>0:
                    cost=q*bar['o']*(1+FEE);cash-=cost
                    hard=min(bar['o']*.995,cmd['stop'])
                    pos[s]={'q':q,'en':bar['o'],'cost':cost,'entry_day':day,'age':0,'peak':bar['o'],'hard':hard,'atr':cmd['atr']}
            elif cmd['kind']=='SELL' and s in pos:
                p=pos.pop(s);px=bar['o'];pro=p['q']*px*(1-FEE);cash+=pro
                tr.append((s,p['entry_day'],day,p['en'],px,100*(pro-p['cost'])/p['cost'],cmd['reason']))
            del pending[s]

        # seans içi koruyucu stop: sadece önceden bilinen stop seviyesini kullanır
        for s in list(pos):
            i=bi.bysym.get(s,{}).get(day)
            if i is None: continue
            bar=bi.data[s][i];p=pos[s];p['peak']=max(p['peak'],bar['h']);p['age']+=1
            # kâr geliştikçe yumuşak trailing; girişteki ATR ile belirlenir
            stop=p['hard']
            gain=p['peak']/p['en']-1
            if gain>=.04: stop=max(stop,p['en']*1.002)
            if gain>=.08: stop=max(stop,p['peak']-2.0*p['atr'],p['en']*1.025)
            if gain>=.13: stop=max(stop,p['peak']-1.7*p['atr'],p['en']*1.06)
            p['hard']=stop
            if bar['l']<=stop:
                px=bar['o'] if bar['o']<stop else stop
                pro=p['q']*px*(1-FEE);cash+=pro
                tr.append((s,p['entry_day'],day,p['en'],px,100*(pro-p['cost'])/p['cost'],'STOP/KAR-KORU'))
                del pos[s]

        # kapanış sinyalleri ve yeni adaylar
        cand=[]
        for s,a in bi.data.items():
            i=bi.bysym[s].get(day)
            if i is None or i<30: continue
            z=v33.pulse(a[:i+1])
            if not z: continue
            if s in pos:
                if 'SAT' in z['rec'] or 'RİSK' in z['rec']:
                    pending[s]={'kind':'SELL','reason':'SAT/RİSK'}
                elif pos[s]['age']>=MAX_HOLD:
                    pending[s]={'kind':'SELL','reason':'10-GÜN'}
            else:
                good=(('ERKEN AL' in z['rec']) or z['rec']=='AL' or ('KADEMELİ AL' in z['rec'])) and z['conf']>=72
                if good:
                    w=a[max(0,i-19):i+1];turn=sum(x['c']*x['v'] for x in w)/len(w);vol=sum(x['v'] for x in w)/len(w)
                    if turn>=120_000_000 and vol>=120_000:
                        cand.append((z['conf']+3*z['early']+z['score'],s,z, v33.atr(a[:i+1],7)))
        cand.sort(reverse=True)
        slots=MAX_POS-len(pos)-sum(1 for x in pending.values() if x['kind']=='BUY')
        for _,s,z,a7 in cand:
            if slots<=0:break
            if s in pos or s in pending:continue
            pending[s]={'kind':'BUY','reason':z['rec'],'stop':z['stop'],'atr':a7};slots-=1

        eq=cash
        for s,p in pos.items():
            i=bi.bysym[s].get(day);eq+=p['q']*(bi.data[s][i]['c'] if i is not None else p['en'])
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)

    last=dates[-1]
    for s,p in list(pos.items()):
        i=max((i for t,i in bi.bysym[s].items() if t<=last),default=None)
        if i is None:continue
        px=bi.data[s][i]['c'];pro=p['q']*px*(1-FEE);cash+=pro
        tr.append((s,p['entry_day'],last,p['en'],px,100*(pro-p['cost'])/p['cost'],'DÖNEM SONU'))
    wins=sum(t[5]>0 for t in tr);gp=sum(max(0,t[5]) for t in tr);gl=-sum(min(0,t[5]) for t in tr);pf=gp/gl if gl else (99 if gp else 0)
    out={'from':dt(dates[0]),'to':dt(dates[-1]),'end':cash,'ret':100*(cash/START-1),'dd':100*dd,'n':len(tr),'win':100*wins/len(tr) if tr else 0,'pf':pf,'best':sorted(tr,key=lambda x:x[5],reverse=True)[:10],'worst':sorted(tr,key=lambda x:x[5])[:10],'details':tr}
    lines=['# BorsaRadar v3.7 Stop-Aware Geriye Dönük AL/SAT Testi',f"Dönem **{out['from']} → {out['to']}** | 100.000 TL | 5 pozisyon | maliyet tek yön %0,10",'Sinyal kapanışta, alım/satım ertesi açılışta. Koruyucu stop önceden belirlenir ve seans içi low ile test edilir; böylece stop gerçekten çalışır. TUPRS + savunma hisseleri hariç.','',f"Son portföy **{out['end']:.2f} TL** | Getiri **%{out['ret']:.2f}** | MaxDD **%{out['dd']:.2f}** | İşlem **{out['n']}** | Kazanma **%{out['win']:.1f}** | PF **{out['pf']:.2f}**",'', '## En iyi','|Hisse|Giriş|Çıkış|Alış|Satış|Net %|Neden|','|---|---|---|---:|---:|---:|---|']
    for t in out['best']:lines.append(f'|{t[0]}|{dt(t[1])}|{dt(t[2])}|{t[3]:.2f}|{t[4]:.2f}|{t[5]:.2f}|{t[6]}|')
    lines+=['','## En kötü','|Hisse|Giriş|Çıkış|Alış|Satış|Net %|Neden|','|---|---|---|---:|---:|---:|---|']
    for t in out['worst']:lines.append(f'|{t[0]}|{dt(t[1])}|{dt(t[2])}|{t[3]:.2f}|{t[4]:.2f}|{t[5]:.2f}|{t[6]}|')
    Path('research/result_v34_app_signal_stop.md').write_text('\n'.join(lines),encoding='utf-8');Path('research/result_v34_app_signal_stop.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':run()
