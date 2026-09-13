package com.kulanoglu.borsaradar;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Her hisse icin teknik ailelerin gecmiste 5 islem gunu sonraki yonu ne kadar iyi yakaladigini olcer.
 * Look-ahead sizdirmaz: her karar noktasinda sadece o ana kadarki mumlar kullanilir.
 */
public final class MethodPerformanceLearner {
    private MethodPerformanceLearner(){}
    public static final class Stat {
        public int samples,hits;
        public double accuracy=50,edge;
    }
    public static final class Result {
        public final Map<String,Stat> stats=new LinkedHashMap<>();
        public String bestMethod="YOK",summary="ogrenme verisi yok";
    }
    public static Result learn(List<MarketDataService.Candle> data){
        Result out=new Result();
        String[] names={"INDICATOR","METHOD","SHORT","MOST_QQE","V35"};
        for(String n:names)out.stats.put(n,new Stat());
        if(data==null||data.size()<90)return out;
        int horizon=5;
        for(int i=60;i+horizon<data.size();i+=3){
            List<MarketDataService.Candle> slice=data.subList(0,i+1);
            double now=data.get(i).close, future=data.get(i+horizon).close;
            double realized=(future-now)/Math.max(.000001,now);
            int actual=realized>0.008?1:realized<-0.008?-1:0;
            if(actual==0)continue;
            IndicatorEngine.Snapshot ind=IndicatorEngine.analyze(slice);
            MethodEngine.Result met=MethodEngine.analyze(ind);
            ShortPulseEngine.Result sh=ShortPulseEngine.analyze(slice);
            AdditionalIndicatorEngine.Result ad=AdditionalIndicatorEngine.analyze(slice);
            V35HybridEngine.Result v=V35HybridEngine.analyze(slice,0);
            record(out.stats.get("INDICATOR"),ind.score>=5?1:ind.score<=-2?-1:0,actual,realized);
            record(out.stats.get("METHOD"),met.percent>=58?1:met.percent<43?-1:0,actual,realized);
            record(out.stats.get("SHORT"),sh.score>=2.7?1:sh.score<=-1.3?-1:0,actual,realized);
            int aq=(ad.mostBull?1:-1)+(ad.qqeBull?1:-1)+(ad.abovePivot?1:-1);
            record(out.stats.get("MOST_QQE"),aq>=2?1:aq<=-2?-1:0,actual,realized);
            record(out.stats.get("V35"),v.opportunity?1:v.risk?-1:0,actual,realized);
        }
        double best=-1;
        StringBuilder b=new StringBuilder("Hisseye ozel 5g: ");
        for(Map.Entry<String,Stat> e:out.stats.entrySet()){
            Stat s=e.getValue();
            s.accuracy=s.samples==0?50:100.0*s.hits/s.samples;
            if(s.samples>=5&&s.accuracy>best){best=s.accuracy;out.bestMethod=e.getKey();}
            if(b.length()>16)b.append(" • ");
            b.append(e.getKey()).append(' ').append(IndicatorEngine.fmt(s.accuracy)).append("%/").append(s.samples);
        }
        out.summary=b.toString()+" • en iyi "+out.bestMethod;
        return out;
    }
    private static void record(Stat s,int predicted,int actual,double realized){
        if(s==null||predicted==0)return;
        s.samples++;
        if(predicted==actual)s.hits++;
        s.edge+=predicted*realized;
    }
}
