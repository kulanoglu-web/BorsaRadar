package com.kulanoglu.borsaradar;

import java.util.Locale;

public final class SourceTrustResolver {
    private SourceTrustResolver(){}
    public static InformationImportanceEngine.Source resolve(String provider,String url){
        String p=(provider==null?"":provider).toLowerCase(Locale.ROOT);
        String u=(url==null?"":url).toLowerCase(Locale.ROOT);
        if(u.contains("kap.org.tr"))return InformationImportanceEngine.Source.KAP;
        if(p.contains("reuters")||u.contains("reuters.com"))return InformationImportanceEngine.Source.REUTERS;
        if(p.contains("bloomberg")||u.contains("bloomberg.com"))return InformationImportanceEngine.Source.BLOOMBERG;
        if(u.contains("sec.gov")||u.contains("spk.gov.tr"))return InformationImportanceEngine.Source.REGULATOR;
        if(u.contains("borsaistanbul.com"))return InformationImportanceEngine.Source.EXCHANGE;
        if(p.contains("business wire")||p.contains("globe newswire")||p.contains("pr newswire"))return InformationImportanceEngine.Source.COMPANY;
        if(u.contains("x.com")||u.contains("twitter.com"))return InformationImportanceEngine.Source.X_OTHER;
        if(p.contains("cnbc")||p.contains("financial times")||p.contains("wsj")||p.contains("barron's")||p.contains("marketwatch"))return InformationImportanceEngine.Source.MAJOR_NEWS;
        return InformationImportanceEngine.Source.OTHER;
    }
}
