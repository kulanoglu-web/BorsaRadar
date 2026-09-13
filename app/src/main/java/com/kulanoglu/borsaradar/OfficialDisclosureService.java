package com.kulanoglu.borsaradar;

import java.util.ArrayList;
import java.util.List;

/** Resmi bildirim kaynaklari icin ortak giris katmani. */
public final class OfficialDisclosureService {
    private OfficialDisclosureService(){}
    public static List<MarketEvent> fetch(String symbol){
        // KAP/SPK/SEC baglantilari burada toplanir. Kaynak erisilemezse bos liste doner.
        return new ArrayList<>();
    }
}
