# Reference data

`notebook_reference_cases.csv` is a compact export of Gurobi results from `Bassam_project_group_Report_Final.ipynb`.

It uses the same selection as the notebook's independent comparison in cell 75:

| Experiment | Cases |
|---|---:|
| Machine hours | 51 |
| Staff hours | 43 |
| Unit profit of A | 99 |
| Minimum requirement for C | 48 |
| Joint resource sample | 26 |
| Total | 267 |

The joint sample takes every 40th row of the 1,023-row joint experiment, starting with index zero. Full input data, profit and one Gurobi-selected plan are retained for each case. Alternative optima mean another solver need not return identical quantities.

`provenance.json` records the exact source notebook hash and the reference CSV hash. The app uses the CSV for a fresh profit and feasibility comparison. Neither this reference export nor the web app replaces the original notebook or the independent algebraic checks of sensitivity ranges.
