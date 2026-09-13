package com.kulanoglu.borsaradar;
public final class NewsFreshnessPolicy {
 private NewsFreshnessPolicy(){}
 public static double weight(double h){return h<=6?1.0:h<=24?.9:h<=72?.72:h<=168?.52:.25;}
}
