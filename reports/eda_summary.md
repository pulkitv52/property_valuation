# EDA Summary

Date: 2026-04-29

## Target Distribution
- Rows: `273587`
- Rows with geometry: `207442`
- Target non-null rows: `273587`
- Mean value_per_area: `323,860.93`
- Median value_per_area: `75,757.58`
- P90 value_per_area: `565,655.74`
- P95 value_per_area: `733,332.93`
- P99 value_per_area: `1,636,364.26`
- Skewness: `195.86`
- Zero or negative target rows: `0`

## Major Findings
- Target value_per_area is heavily right-skewed; segmentation or robust handling may still help.
- Target distribution has a very heavy tail relative to the median.
- 66145 rows still lack parcel geometry-derived spatial features.
- Target medians vary materially across Flat_or_Land; segmented modeling may help.
- Target medians vary materially across Urban; segmented modeling may help.
- Target medians vary materially across Rural; segmented modeling may help.
- Target medians vary materially across Transaction_code; segmented modeling may help.

## Target By Flat Or Land

```
Flat_or_Land  count          mean         median
        Land 183133  482434.52526  156136.136529
        Flat  90454   2813.125759         2430.0
```

## Target By Urban

```
Urban  count           mean    median
   No 204102  284866.413463   64400.0
  Yes  69485  438401.607125  381818.0
```

## Target By Rural

```
Rural  count           mean    median
  Yes 204102  284866.413463   64400.0
   No  69485  438401.607125  381818.0
```

## Target By Transaction Code

```
Transaction_code  count           mean         median
             101 162908  193883.220542   71428.571429
             201  42137  278584.896718       128000.0
            1210  14142   85102.553839         2448.0
            1401   8600  173050.720464        79200.0
             204   5183  214023.173149  101666.666667
            1201   3993  247113.459659    3794.871795
             104   3912  111287.675276    2962.962963
             110   3759  571071.531804       375000.0
             207   3663  230902.701124       100000.0
             105   3621  100572.731037         3148.0
```

## Target By Zone

```
Zone_no  count            mean        median
      0 262726   322839.881962       80000.0
      1   4321   234518.748926        3564.0
      5   4090   239423.907625        3330.0
      2   1415   598331.073791        4600.0
      4    910   744203.462935   4390.743802
      3    125  2153973.171148  2424240.3241
```

## Target By Mouza

```
       Mouza_Name  count           mean         median
         Bamunara  31131   32764.784902         2200.0
        Katrapota  17535   65398.884922    2553.763441
      Mallikbagan  12754   56731.952034        35000.0
             Goda  11842  406248.320673  272726.876034
            Arrah  10819   88892.177424         4230.0
        Sankarpur   9953  994562.270482    2452.500333
        Ichhlabad   9435  388731.521984  246000.708216
Bahirsarbamangala   9345  495199.938396       330000.0
             Nari   8851  283566.634572  156060.032744
     Kanainatshal   8399  226158.562592         3800.0
```

## Error By Flat Or Land

```
Flat_or_Land  count          mae   mean_actual
        Land  36553 97274.409474 357648.886346
        Flat  18165   286.578355   2804.993411
```

## Error By Transaction Code

```
Transaction_code  count          mae   mean_actual
             101  32574 58341.352547 202252.884780
             201   8396 38768.046448 274096.016736
            1210   2832 19380.037155  82417.912279
            1401   1754 25109.817563 171354.495750
             204   1067 32622.701468 219868.409586
            1201    811 44455.920849 130343.214735
             104    754 20040.298629 101313.106052
             110    753 56444.090124 563024.451346
             207    749 31376.090816 244392.560900
             105    715 18897.674337  80568.288058
```

## Error By Zone

```
Zone_no  count           mae  mean_actual
      0  52568  66184.647639 2.353226e+05
      1    873  31057.502003 2.776036e+05
      5    788  25376.873542 2.630734e+05
      2    300  58763.379419 5.036082e+05
      4    166  73072.758668 6.106391e+05
      3     23 209276.560365 2.241633e+06
```
