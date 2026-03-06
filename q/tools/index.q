/ Index constituent tools
/ Namespace: .xqa
/ Depends on: indexMembers table with columns: index, sym

/ .xqa.getIndexSyms[`TOPIX]
/ Returns list of all symbols that are constituents of the given index.
.xqa.getIndexSyms:{[idx]
  exec sym from indexMembers where index=idx}

/ .xqa.getIndexCount[`TOPIX]
/ Returns the constituent count for quick sanity checks.
.xqa.getIndexCount:{[idx]
  count exec sym from indexMembers where index=idx}
