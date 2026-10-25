# Data dictionary: court_disposal_2023_metro.csv

| Column | Meaning (NCRB column) |
|---|---|
| table | IPC (18B.1) or SLL (18B.3) |
| sl_code, crime_head | NCRB serial number and crime head name |
| parent_code | serial of the parent head (3.1A -> 3.1); empty for top-level |
| row_type | detail (analyse these), parent (has children), subtotal, grand_total |
| group | subtotal group the head rolls up into |
| pending_prev (3) | cases pending trial from previous year |
| sent_for_trial (4) | cases sent for trial during the year |
| total_for_trial (5) | = 3 + 4 |
| abated, withdrawn, compounded, plea_bargain, quashed (6-10) | disposed without trial, by type |
| disposed_without_trial (11) | = 6 + 7 + 8 + 9 + 10 |
| stayed_or_record_room (12) | stayed or sent to record room (not counted as disposed) |
| conv_prev_year, conv_current_year, convicted (13-15) | convictions; 15 = 13 + 14 |
| discharged, acquitted (16-17) | trial outcomes |
| trials_completed (18) | = 15 + 16 + 17 |
| disposed_by_courts (19) | = 11 + 18 |
| pending_end (20) | = 5 - 19 |
| conviction_rate_pub, pendency_pct_pub (21-22) | rates as published (empty when undefined) |
