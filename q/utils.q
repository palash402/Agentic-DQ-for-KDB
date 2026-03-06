/ Shared DQ utilities — loaded by init.q
/ Namespace: .dq

/ True if x is null
.dq.isnull:{null x}

/ Count of nulls in a column
.dq.countNull:{count where null x}

/ Count of negative values in a numeric column
.dq.countNeg:{count where x<0}

/ Percentage: n out of d (safe against d=0)
.dq.pct:{[n;d] $[d=0;0f;100f*n%d]}

/ Bin a list of times into 1-minute buckets, return count per bucket
/ Usage: .dq.bin1min[`time$exec time from trade where date=2024.05.08]
.dq.bin1min:{[times]
  buckets:`minute$times;
  select count i by bucket:buckets from ([]bucket:buckets)}

/ Detect consecutive duplicate timestamps within a table column
/ Returns indices where time equals previous time
.dq.dupTimestamps:{[times]
  where not differ times}

/ Rolling z-score for outlier detection (window w)
/ Returns abs z-score for each element of vector x
.dq.rollingZscore:{[x;w]
  mu:mavg[w;x];
  sigma:mdev[w;x];
  abs (x-mu) % $[sigma=0;1f;sigma]}
