/ Trade-quote alignment tools
/ Namespace: .xqa
/ Depends on: trade, quote tables (date-partitioned)

/ .xqa.alignTradeQuote[tradeTable; quoteTable]
/ Wraps q's `aj` (asof join) to join each trade to its immediately preceding quote.
/ Returns a table with trade columns plus bid, ask, bsize, asize at trade time.
/
/ Parameters:
/   t - trade table (must have sym, time columns)
/   q - quote table (must have sym, time, bid, ask, bsize, asize columns)
/
/ Usage:
/   t: select sym,time,price,size from trade where date=2024.05.08,sym in syms
/   q: select sym,time,bid,ask,bsize,asize from quote where date=2024.05.08,sym in syms
/   .xqa.alignTradeQuote[t;q]
.xqa.alignTradeQuote:{[t;q]
  aj[`sym`time;t;select sym,time,bid,ask,bsize,asize from q]}

/ .xqa.alignmentStats[aligned]
/ Given the output of .xqa.alignTradeQuote, compute alignment statistics.
/ A trade is "aligned" if price matches bid or ask at the time of the trade.
/ Returns a dict: total, aligned, alignedPct, crossedCount
.xqa.alignmentStats:{[aligned]
  total:count aligned;
  nAligned:count where (aligned`price)=(aligned`bid) or (aligned`price)=(aligned`ask);
  crossed:count where (aligned`bid)>=(aligned`ask);
  `total`aligned`alignedPct`crossedCount!(total;nAligned;.dq.pct[nAligned;total];crossed)}

/ .xqa.quoteToTradeRatio[date; syms; windowMinutes]
/ Compute quote-to-trade ratio per time window.
/ High ratios (>50:1) indicate latency risk zones.
.xqa.quoteToTradeRatio:{[dt;syms;winMin]
  tc:select tradeCount:count i by bucket:`minute$time
     from trade where date=dt, sym in syms;
  qc:select quoteCount:count i by bucket:`minute$time
     from quote where date=dt, sym in syms;
  t:tc lj `bucket xkey qc;
  update ratio:.dq.pct[quoteCount;tradeCount] from t}
