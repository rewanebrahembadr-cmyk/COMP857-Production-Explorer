# COMP857 production planning explorer

A supplementary Streamlit app for investigating the production LP in the group project. The interface uses British English. It is a separate deployment package: it contains no submitted report, student IDs, or complete assessment notebook.

## What it does

- Solves the baseline and shows resource use, binding constraints and local shadow prices.
- Re-solves one-resource changes, the profit coefficient of A, simultaneous resource changes, and minimum production of C.
- Compares re-optimised profit with the baseline plan or the original dual prediction, as appropriate.
- Explains why a local shadow-price prediction can fail and when there are alternative optimal plans.
- Checks 267 live results against exported Gurobi notebook references.
- Downloads experiment and validation tables as CSV files.

Live optimisation uses **SciPy/HiGHS**, not Gurobi. Gurobi is not a dependency and no Gurobi licence is needed for this app. The mathematical formulation is the same as the notebook. Sensitivity ranges are explained using the original basis, not claimed to be attributes returned by SciPy.

## Run locally

Use Python **3.12**. From the folder containing `app.py`:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

The browser address is printed by Streamlit. The first visit to the joint experiment solves 1,023 small LPs; Streamlit caches this curve for subsequent visits.

## Upload to GitHub and deploy

1. Extract this package. Create a GitHub repository, for example `comp857-production-explorer`.
2. Upload the **contents** of this folder so that `app.py`, `model.py` and `requirements.txt` are at the repository root. Include `data/`, `tests/`, `.streamlit/` and `.github/`.
3. In Streamlit Community Cloud, sign in with the GitHub account that can access the repository and choose **Create app**.
4. Select the repository and branch. Set the main file path to **`app.py`**.
5. In the advanced deployment settings, select **Python 3.12**, then deploy.
6. Open the resulting `.streamlit.app` address. Check Overview, the joint counterexample and Validation before sharing it.

If you uploaded the whole enclosing folder instead, use `COMP857_Streamlit_GitHub/app.py` as the main file path. Keeping the files at the repository root is simpler.

No API keys, secrets or credentials are required. Do not upload the report or full notebook merely to make the app work. Repository visibility and access to the shared app should follow your university's rules. Creating a public repository also publishes its code and reference data.

The package is ready for deployment, but does **not** include an already published app link. An owner must connect their GitHub repository to Streamlit and complete deployment. Community Cloud can suspend idle apps, so open and check the app before a demonstration.

## File guide

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface, Plotly charts and cached experiments |
| `model.py` | LP formulation, solving, dual-sign conversion and basis calculations |
| `requirements.txt` | Pinned direct dependencies tested for this package |
| `.streamlit/config.toml` | Beige and teal theme and server settings |
| `data/notebook_reference_cases.csv` | The 267 Gurobi comparison cases |
| `data/provenance.json` | Source identifiers, notebook hash and case selection |
| `tests/test_model.py` | Numerical, feasibility and notebook regression checks |
| `tests/test_app.py` | Streamlit interaction checks using AppTest |
| `.github/workflows/tests.yml` | Runs the checks on GitHub pushes and pull requests |
| `DEPLOY_AR.md` | Deployment instructions in Arabic |

## Numerical interpretation

For the original data, profit is **£2,929.60** at **(33.2, 22.4, 8)**. Baseline shadow prices are local. They are valid for a one-resource change only within their applicable range. The original basis calculations certify joint feasibility only while all candidate basic values are non-negative and objective coefficients remain fixed.

At **269.5 machine hours and 124 staff hours**, the old prediction is **£3,170.40** but the old basis suggests **B = -5.9**. The feasible optimum is **£2,840** at **(50, 0, 8)**. The old dual value remains an upper bound. The compensating case **(190, 160)** shows the opposite: a joint change can preserve the basis even though one capacity lies outside its individual range.

At coefficient breakpoints, two solvers may choose different optimal quantities. Reference checks therefore compare profit and constraint feasibility, not equality of plans at every tie. The app checks against a fixed export, not a live Gurobi process. Agreement does not establish that shared input data are correct, nor does it independently prove sensitivity ranges.

All slider controls retain the original fixed unit requirements. Infeasible cases show no production plan or fabricated zero profit. Charts join solved samples; live metrics solve the exact selected input. Heatmap colours are deterministic profit values or prediction gaps, not probabilities. Source reports and the main notebook remain the authoritative assessment submission.

## Documentation

- [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [SciPy linprog](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)
- [Gurobi constraint attributes](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/constraintlinear.html)
- [Gurobi variable attributes](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/variable.html)

Any required acknowledgement of assistance should accurately cover work on this supplementary app as well as the report and notebook.
