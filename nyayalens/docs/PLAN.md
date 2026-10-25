# NyayaLens: project plan

**Question.** In India's 19 metropolitan cities in 2023, which crime heads (IPC and
special/local laws) have unusual court outcomes, and how confident can we be?

**Data.** NCRB Crime in India 2023: Table 18B.1 (IPC) and Table 18B.3 (SLL), court
disposal by crime head, metropolitan cities (aggregate). One year, ~188 detail crime heads.

| Phase | Work | Output |
|---|---|---|
| 1 (done) | Parse PDFs, tag detail/parent/subtotal rows, validate arithmetic | `data/processed/court_disposal_2023_metro.csv`, validation reports |
| 2 (done) | Rates (conviction, pendency, without-trial, plea, withdrawal, compounding, acquittal share) + Wilson 95% CIs; heads with < 30 completed trials = "insufficient data" | features table |
| 3 (done) | Robust z-score (median/MAD) as main method; Isolation Forest and LOF as comparisons | flags + agreement table |
| 4 (done) | Plain-English reason per flag; bootstrap stability (resample counts) | explanations + stability scores |
| 5 (done) | Streamlit dashboard + Limitations tab | deployed app |
| 6 | README, tests, deploy link | finished repo |

**Rules.** Analyse detail rows only (never parents/subtotals together). Never invent data.
Anomalies are statistical signals, not accusations: differences can come from reporting practice,
case mix and court workload.
