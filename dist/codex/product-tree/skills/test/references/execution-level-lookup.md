<execution_level_lookup>

Two lookup tables for Stage 2 execution-level selection: the first maps a spec promise to its minimum level, the second maps a dependency to its minimum level.

| Spec promise                                      | Minimum level | Reason                          |
| ------------------------------------------------- | ------------- | ------------------------------- |
| Prices are calculated correctly                   | `L1`          | Pure calculation                |
| User can export data as CSV                       | `L1`          | File I/O with temporary folders |
| CLI processes a product-specific site             | `L2`          | Product-specific binary         |
| Database query returns users                      | `L2`          | Real database required          |
| User completes checkout with a live provider      | `L3`          | Remote provider required        |
| Browser flow works against the live deployed site | `L3`          | Real browser and remote system  |

| Dependency                        | Minimum level |
| --------------------------------- | ------------- |
| None, pure function               | `L1`          |
| Filesystem with temporary folders | `L1`          |
| Standard development tools        | `L1`          |
| Database                          | `L2`          |
| Product-specific binary           | `L2`          |
| External HTTP API or browser API  | `L2` or `L3`  |
| Live third-party service          | `L3`          |
| Real credentials                  | `L3`          |

</execution_level_lookup>
