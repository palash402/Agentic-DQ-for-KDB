/ Venue tools — MCP tool wrappers for venue/symbol lookups
/ Namespace: .xqa
/ Depends on: stockCodes, venueMap tables in the KDB+ session

/ .xqa.getVenueSyms[`XTKS]
/ Returns list of all symbol identifiers traded on the given venue.
/ Requires stockCodes table with columns: sym, venue
.xqa.getVenueSyms:{[venue]
  exec sym from stockCodes where venue=venue}

/ .xqa.getVenueHours[`XTKS]
/ Returns a table row with the latest session boundaries and UTC offset
/ for the given venue. Uses the most recent date in venueMap.
/ Requires venueMap table with columns:
/   venue, date, tradingStart, tradingEnd, lunchStart, lunchEnd, utcOffset
.xqa.getVenueHours:{[venue]
  select venue,date,tradingStart,tradingEnd,lunchStart,lunchEnd,utcOffset
  from venueMap
  where venue=venue, date=max date}

/ .xqa.getVenueSessionBounds[`XTKS]
/ Convenience: returns a dict with named session time boundaries
/ Keys: preOpen, morningStart, lunchStart, lunchEnd, afternoonEnd, postClose
.xqa.getVenueSessionBounds:{[venue]
  t:first .xqa.getVenueHours[venue];
  `preOpen`morningStart`lunchStart`lunchEnd`afternoonEnd!
    (t`tradingStart;t`tradingStart;t`lunchStart;t`lunchEnd;t`tradingEnd)}
