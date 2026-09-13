package com.kulanoglu.borsaradar;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Resmi X/Twitter hesaplarini ayirt etmek icin guvenli beyaz liste. */
public final class OfficialSocialRegistry {
    private OfficialSocialRegistry(){}
    private static final Set<String> HANDLES=new HashSet<>(Arrays.asList(
        "nvidia","apple","microsoft","amazon","google","meta","tesla","amd","intel","qualcomm",
        "bloomberg","reuters","borsaistanbul","spkgovtr","kap_org_tr"
    ));
    public static boolean isOfficialUrl(String url){
        if(url==null)return false; String u=url.toLowerCase(Locale.ROOT);
        int k=u.indexOf("x.com/"); int off=6; if(k<0){k=u.indexOf("twitter.com/");off=12;} if(k<0)return false;
        String h=u.substring(k+off).split("[/?#]")[0].replace("@","").trim();
        return HANDLES.contains(h);
    }
}
