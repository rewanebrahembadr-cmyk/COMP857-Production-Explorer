"""Supplementary COMP857 explorer. Run with: streamlit run app.py"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from model import (BASE_CAPACITIES, BASE_PLAN, BASE_PROFIT, BASIS_INVERSE,
                   BASIC_NAMES, PRODUCTS, RESOURCES, G, solve, constraint_rows,
                   baseline_basis_values, baseline_basis_is_feasible,
                   baseline_prediction, solution_record, coefficient_plans,
                   alternative_plans)

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="COMP857 | Production planning", layout="wide")
COLOURS = {"A": "#285E64", "B": "#AF7C31", "C": "#986356"}
st.markdown("""<style>
 .block-container {max-width:1280px;padding-top:2rem;padding-bottom:2rem;}
 h1,h2,h3 {letter-spacing:-0.025em;}
 [data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;}
 [data-testid="stSidebar"] {border-right:1px solid #e4ded3;}
 </style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_solve(capacities=BASE_CAPACITIES, profit_a=48., minimum_c=8.):
    return solve(capacities, profit_a, minimum_c)


@st.cache_data(show_spinner=False)
def resource_curve(index):
    high = (360., 280., 320.)[index]
    special = ([196., 240., 269.5], [124., 180., 224.], [176.4, 200.])[index]
    rows = []
    for v in sorted(set(np.linspace(0, high, 81).tolist() + special)):
        caps = list(BASE_CAPACITIES); caps[index] = v
        s = cached_solve(tuple(caps))
        row = solution_record(s); row["Capacity"] = v
        row["Baseline prediction"] = baseline_prediction(tuple(caps))
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def profit_curve():
    values = sorted(set(np.arange(20., 65.01, .5).tolist() + [30., 470/11, 48., 160/3]))
    rows = []
    for p in values:
        row = solution_record(cached_solve(profit_a=p))
        row["Baseline plan profit"] = float(BASE_PLAN @ [p, 40., 55.])
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def minimum_c_curve():
    rows = []
    for q in np.arange(0., 60.01, 1.):
        row = solution_record(cached_solve(minimum_c=float(q)))
        row["Baseline prediction"] = baseline_prediction(minimum_c=q)
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def joint_curve():
    rows = []
    for m in np.linspace(180., 300., 31):
        for s in np.linspace(100., 260., 33):
            caps = (float(m), float(s), 200.)
            row = solution_record(cached_solve(caps))
            row["Gap"] = baseline_prediction(caps) - row["Profit"]
            rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def validate_reference():
    reference = pd.read_csv(ROOT / "data" / "notebook_reference_cases.csv")
    results = []
    for _, row in reference.iterrows():
        caps = tuple(float(row[k]) for k in ["Machine capacity", "Staff capacity", "Material capacity"])
        s = cached_solve(caps, float(row["Unit profit A"]), float(row["Minimum C requirement"]))
        rhs = np.r_[caps, -s.minimum_c, 0.]
        error = abs(s.profit - row["Profit"]) if s.profit is not None else float("inf")
        violation = max(0., float(np.max(G @ s.plan - rhs)), float(-np.min(s.plan))) if s.plan is not None else float("inf")
        results.append({"Experiment": row["Experiment"], "Case": row["Case"],
                        "Profit difference": error, "Largest violation": violation,
                        "Pass": s.status == "Optimal" and max(error, violation) <= 1e-6})
    return pd.DataFrame(results)


def fmt(value):
    return f"£{value:,.2f}"


def solution_summary(s):
    if s.status != "Optimal":
        if s.status == "Infeasible":
            st.error("No feasible plan: the selected capacities cannot meet all production requirements.")
            st.write("The compulsory C units alone need the following resources.")
            st.dataframe(pd.DataFrame({"Resource": RESOURCES,
                                      "Needed for minimum C": np.array([5., 3., 4.]) * s.minimum_c,
                                      "Available": s.capacities}), hide_index=True, width="stretch")
        else:
            st.error(f"The solver returned {s.status}. No profit or plan is shown.")
        return False
    cols = st.columns(4)
    cols[0].metric("Optimal profit", fmt(s.profit))
    for i, p in enumerate(PRODUCTS):
        cols[i+1].metric(f"Product {p}", f"{s.plan[i]:,.2f} units")
    st.caption("Production quantities are continuous. Values shown to two decimal places are not rounded before solving.")
    return True


def constraints(s):
    st.dataframe(pd.DataFrame(constraint_rows(s)), hide_index=True, width="stretch")
    st.caption("Binding means zero margin within numerical tolerance. A binding constraint can still have a zero shadow price. At a breakpoint, a reported price may describe only one side.")


def download(frame, label, filename):
    st.download_button(label, frame.to_csv(index=False).encode("utf-8"), filename,
                       mime="text/csv", key=filename)


def style_figure(fig, title, height=350):
    fig.update_layout(title=title, height=height, margin=dict(l=30, r=20, t=55, b=35),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF",
                      font=dict(family="Arial", size=13, color="#223A3C"),
                      legend=dict(orientation="h", y=1.1), hovermode="x unified")
    fig.update_xaxes(showgrid=True, gridcolor="#EEEAE2")
    fig.update_yaxes(showgrid=True, gridcolor="#EEEAE2")
    return fig


def charts(frame, x, x_label, selected, breakpoints=(), extra=None):
    profit = go.Figure(go.Scatter(x=frame[x], y=frame["Profit"], name="Re-optimised profit",
                                 line=dict(color=COLOURS["A"], width=3), connectgaps=False))
    if extra:
        profit.add_trace(go.Scatter(x=frame[x], y=frame[extra], name=extra,
                                   line=dict(color="#9D968C", dash="dash")))
    plans = go.Figure()
    for product, dash in zip(PRODUCTS, ["solid", "dash", "dot"]):
        plans.add_trace(go.Scatter(x=frame[x], y=frame[product], name=product,
                                  line=dict(color=COLOURS[product], width=3, dash=dash), connectgaps=False))
    for fig in (profit, plans):
        for b in breakpoints:
            fig.add_vline(x=b, line_dash="dot", line_color="#B8A582")
        fig.add_vline(x=selected, line_color="#AE5B43", line_width=1.5)
        fig.update_xaxes(title=x_label)
    profit.update_yaxes(title="Optimal profit (£)"); plans.update_yaxes(title="Units produced", rangemode="tozero")
    a, b = st.columns(2)
    a.plotly_chart(style_figure(profit, "Profit"), width="stretch")
    b.plotly_chart(style_figure(plans, "Production mix"), width="stretch")
    st.caption("The rust line marks your input. Dotted lines mark analytical breakpoints. Gaps indicate infeasible cases. Curves join solved samples; use the live result for your exact input.")


def reset_inputs():
    for k in list(st.session_state):
        if k != "page":
            del st.session_state[k]


with st.sidebar:
    st.markdown("### COMP857")
    st.caption("Production planning and sensitivity analysis")
    page = st.radio("Explore", ["Overview", "Resources", "Unit profit", "Joint changes", "Minimum C", "Validation and model"], key="page")
    st.button("Reset all inputs", on_click=reset_inputs, width="stretch")
    st.divider()
    st.caption("Supplementary explorer. The report and notebook remain the submitted analysis.")

st.title("Production planning")
st.caption("Change an assumption, inspect the plan and understand where a local prediction stops working.")

if page == "Overview":
    st.header("The starting decision")
    st.write("Choose how many units of A, B and C to produce. All quantities may be fractional. Machine time, staff time and material are limited, C must be at least eight units, and B cannot exceed twice A.")
    s = cached_solve()
    solution_summary(s)
    st.subheader("Resource use at the optimum")
    constraints(s)
    st.write("Machine and staff time are fully used. Material has 23.6 units left. Extra machine time is worth £11.20 per hour locally, against £1.60 for staff time. Neither value is a purchase cost or a rule for unlimited expansion.")
    st.subheader("Data per unit")
    st.dataframe(pd.DataFrame({"Item": ["Machine hours", "Staff hours", "Material units", "Unit profit (£)"],
                              "A": [4, 2, 3, 48], "B": [3, 4, 2, 40], "C": [5, 3, 4, 55]}), hide_index=True, width="stretch")
    st.info("Try Resources for one change, then Joint changes for the counterexample where two individually valid changes fail together.")
    download(pd.DataFrame([solution_record(s)]), "Download baseline result", "baseline_result.csv")

elif page == "Resources":
    st.header("What is another unit of a resource worth?")
    name = st.selectbox("Resource", RESOURCES, key="resource")
    index = RESOURCES.index(name)
    maximum = (360., 280., 320.)[index]
    value = st.slider("Available capacity", 0., maximum, BASE_CAPACITIES[index], .5, key=f"capacity_{index}")
    caps = list(BASE_CAPACITIES); caps[index] = value; caps = tuple(caps)
    s = cached_solve(caps)
    if solution_summary(s):
        prediction = baseline_prediction(caps)
        valid = baseline_basis_is_feasible(caps)
        if valid:
            st.success(f"The original basis is valid here. Its shadow-price prediction is {fmt(prediction)}, matching the re-optimised profit.")
        else:
            st.warning(f"The original basis is no longer feasible. Its extended prediction is {fmt(prediction)}; use the solved profit above.")
        constraints(s)
    ranges = ["196 to 269.5 machine hours", "124 to 224 staff hours", "176.4 material units upwards"][index]
    st.write(f"The baseline sensitivity range for this one-resource change is **{ranges}**, with all other data fixed.")
    edges = ([196., 269.5], [124., 224.], [176.4])[index]
    frame = resource_curve(index)
    charts(frame, "Capacity", f"{name} capacity", value, edges, "Baseline prediction")
    st.caption("The dashed prediction is extended beyond its valid range to show its limitations. Exact equality is certified only while the baseline basis is feasible.")
    if index == 0:
        st.write("Machine-hour values are £12.80 on 40–196, £11.20 on 196–269.5, then zero. Beyond 269.5, staff and material limit the plan.")
    elif index == 1:
        st.write("Staff-hour values are £24 on 24–124, £1.60 on 124–224, then zero. Beyond 224, machines and B ≤ 2A limit the plan.")
    else:
        st.write("There is spare material at the baseline. Increasing it alone does not improve profit. Below 176.4, the plan must change.")
    download(frame, "Download resource curve", "resource_curve.csv")

elif page == "Unit profit":
    st.header("When should the production mix change?")
    p = st.slider("Profit per unit of A (£)", 20., 65., 48., .1, key="profit_a")
    boundary = st.selectbox("Or inspect an exact breakpoint", ["Use slider", "30", "470/11", "160/3"], key="profit_boundary")
    if boundary != "Use slider":
        p = {"30": 30., "470/11": 470/11, "160/3": 160/3}[boundary]
        st.caption(f"Exact coefficient selected: {p:.9f}. The slider is currently overridden.")
    s = cached_solve(profit_a=p)
    solution_summary(s)
    fixed = float(BASE_PLAN @ [p, 40., 55.])
    st.write(f"Keeping baseline quantities at this same unit profit earns **{fmt(fixed)}**. Adapting the plan adds **{fmt(s.profit-fixed)}**.")
    if 470/11 - 1e-7 <= p <= 160/3 + 1e-7:
        st.success("The baseline plan remains optimal at this coefficient. Additional optima may exist at the endpoints.")
    else:
        st.info("This coefficient is outside the baseline range. Re-optimisation can improve on the old quantities.")
    charts(profit_curve(), "Unit profit A", "Unit profit of A (£)", p,
           [30., 470/11, 160/3], "Baseline plan profit")
    st.dataframe(pd.DataFrame(coefficient_plans()), hide_index=True, width="stretch")
    alternatives = alternative_plans(p)
    if alternatives:
        rows = [{**dict(zip(PRODUCTS, q)), "Profit": float(q @ [p, 40., 55.])} for q in alternatives]
        st.subheader("Different plans with the same optimal profit")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.write("These are two neighbouring plans and their midpoint. Every convex combination is feasible and has the same profit at this boundary. A different solver may select a different optimum.")
    st.caption("The quantity curves show one optimum per solve and interpolate between sampled coefficients. They do not enumerate all optimal plans at a tie.")
    download(profit_curve(), "Download coefficient experiment", "profit_A_curve.csv")

elif page == "Joint changes":
    st.header("Two valid ranges do not form a valid rectangle")
    preset = st.selectbox("Scenario", ["Custom inputs", "Baseline", "Counterexample: 269.5 machines, 124 staff", "Compensating change: 190 machines, 160 staff"], key="joint_preset")
    if preset == "Custom inputs":
        a, b = st.columns(2)
        m = a.slider("Machine hours", 40., 360., 240., .5, key="joint_machine")
        staff = b.slider("Staff hours", 24., 280., 180., .5, key="joint_staff")
    else:
        m, staff = {"Baseline": (240., 180.),
                    "Counterexample: 269.5 machines, 124 staff": (269.5, 124.),
                    "Compensating change: 190 machines, 160 staff": (190., 160.)}[preset]
        st.write(f"Selected capacities: **{m:g} machine hours** and **{staff:g} staff hours**. Material stays at 200.")
    caps = (m, staff, 200.); s = cached_solve(caps)
    if solution_summary(s):
        prediction = baseline_prediction(caps); valid = baseline_basis_is_feasible(caps)
        st.write(f"Original dual prediction: **{fmt(prediction)}**. Prediction minus optimum: **{fmt(prediction-s.profit)}**.")
        if valid:
            st.success("All baseline basic values remain non-negative. The original basis still gives the optimum.")
        else:
            st.warning("The baseline basis is infeasible. The old dual prediction remains an upper bound, not an achievable plan.")
        st.dataframe(pd.DataFrame({"Baseline basic variable": BASIC_NAMES, "Candidate value": baseline_basis_values(caps)}), hide_index=True, width="stretch")
        st.write("A negative candidate is not an instruction to produce a negative quantity. It means that this basis must be replaced.")
        constraints(s)
    st.subheader("The joint experiment")
    frame = joint_curve(); ms = np.sort(frame["Machine hours"].unique()); ss = np.sort(frame["Staff hours"].unique())
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Optimal profit (£)", "Old prediction minus optimum (£)"), horizontal_spacing=.15)
    xm, ys = np.meshgrid(np.linspace(180, 300, 161), np.linspace(100, 260, 161))
    dm, ds = xm - 240., ys - 180.
    margin = np.minimum.reduce([33.2+.4*dm-.3*ds, 22.4-.2*dm+.4*ds, 23.6-.8*dm+.1*ds, 44.+dm-ds])
    for col, field, scale in [(1, "Profit", "Viridis"), (2, "Gap", "Magma")]:
        z = frame.pivot(index="Staff hours", columns="Machine hours", values=field).reindex(index=ss, columns=ms).to_numpy()
        if field == "Gap":
            z = np.maximum(z, 0.)  # remove floating-point noise for display only
        fig.add_trace(go.Heatmap(x=ms, y=ss, z=z, colorscale=scale, showscale=False, hovertemplate="Machines %{x}<br>Staff %{y}<br>£%{z:,.2f}<extra></extra>"), row=1, col=col)
        fig.add_trace(go.Contour(x=xm[0], y=ys[:, 0], z=margin,
                                contours=dict(start=0, end=0, size=1, coloring="none"),
                                line=dict(color="white", width=2), showscale=False,
                                hoverinfo="skip", showlegend=False), row=1, col=col)
        fig.add_trace(go.Scatter(x=[240.], y=[180.], mode="markers", name="Baseline",
                                marker=dict(color="#F27B62", size=9, line=dict(color="white", width=1)),
                                showlegend=col==1), row=1, col=col)
        if 180 <= m <= 300 and 100 <= staff <= 260:
            fig.add_trace(go.Scatter(x=[m], y=[staff], mode="markers", name="Selected",
                                    marker=dict(color="white", symbol="x", size=10), showlegend=col==1), row=1, col=col)
        fig.update_xaxes(title="Machine hours", row=1, col=col)
        fig.update_yaxes(title="Staff hours", row=1, col=col)
    st.plotly_chart(style_figure(fig, "", 440), width="stretch")
    st.caption("1,023 LP scenarios. White lines mark the baseline basis feasibility boundary. Colours describe profit or prediction error, not probability. The displayed grid covers 180–300 machine hours and 100–260 staff hours.")
    download(frame, "Download joint experiment", "joint_resource_curve.csv")

elif page == "Minimum C":
    st.header("The opportunity cost of compulsory production")
    q = st.slider("Minimum units of C", 0., 60., 8., .5, key="minimum_c")
    s = cached_solve(minimum_c=q)
    if solution_summary(s):
        predicted = baseline_prediction(minimum_c=q)
        if baseline_basis_is_feasible(minimum_c=q):
            st.success(f"For 0 ≤ q ≤ 30, Z(q) = 2976 − 5.8q. The prediction here is {fmt(predicted)}.")
        else:
            st.warning(f"The minimum-C baseline range has been exceeded. Its extension predicts {fmt(predicted)}; use the re-optimised result.")
        constraints(s)
    st.write("C earns £55 per unit. At the baseline, its resources have a local opportunity value of £60.80. Requiring another unit therefore lowers the best total profit by £5.80 within the valid range.")
    charts(minimum_c_curve(), "Minimum C", "Required minimum units of C", q, [30., 48.], "Baseline prediction")
    st.caption("The break at 30 ends the baseline basis range. Requirements above 48 are infeasible with the original capacities, because machine time is insufficient.")
    download(minimum_c_curve(), "Download minimum-C experiment", "minimum_C_curve.csv")

else:
    st.header("Check the computation and inspect the model")
    st.write("This web app solves with SciPy/HiGHS. It does not run Gurobi. The included reference file contains 267 Gurobi results exported from the project notebook. Comparisons use profit and feasibility, since alternative optima can have different quantities.")
    with st.spinner("Comparing live results with the notebook references..."):
        checks = validate_reference()
    a, b, c = st.columns(3)
    a.metric("Reference cases", len(checks))
    b.metric("Cases passed", int(checks["Pass"].sum()))
    c.metric("Largest profit difference", f"{checks['Profit difference'].max():.2e}")
    if checks["Pass"].all():
        st.success("All bundled reference comparisons pass within absolute tolerance 10⁻⁶.")
    else:
        st.error("A reference comparison failed. Inspect the rows below before using the app.")
    st.dataframe(checks.groupby("Experiment", sort=False).agg(Cases=("Pass", "size"), Passed=("Pass", "sum"),
                 Maximum_profit_difference=("Profit difference", "max"), Maximum_violation=("Largest violation", "max")).reset_index(), hide_index=True, width="stretch")
    download(checks, "Download validation results", "reference_validation.csv")
    st.caption("Solver agreement cannot detect a data error shared by both models. These comparisons do not directly validate Gurobi's sensitivity-range attributes.")
    with st.expander("Mathematical formulation"):
        st.latex(r"\max\;48A+40B+55C")
        st.latex(r"\begin{aligned}4A+3B+5C&\le240\\2A+4B+3C&\le180\\3A+2B+4C&\le200\\C&\ge q\\B&\le2A\\A,B,C&\ge0\end{aligned}")
        st.write("The baseline uses q = 8. Resource pages vary one right-hand side; the unit-profit page changes only the coefficient of A.")
    with st.expander("The original basis and sensitivity ranges"):
        st.dataframe(pd.DataFrame(BASIS_INVERSE, index=BASIC_NAMES, columns=["Machines", "Staff", "Material", "Minimum C", "Ratio"]), width="stretch")
        st.latex(r"x_{\mathcal B}^{new}=x_{\mathcal B}^{base}+\mathcal B^{-1}\Delta b")
        st.write("For one resource at a time: machines 196–269.5; staff 124–224; material 176.4 upwards. For A's profit coefficient: 470/11–160/3. These are analytical results from the project, not attributes returned by this app's solver.")
        st.write("A zero basic variable indicates degeneracy. Distinct optimal plans indicate alternative optima. One does not automatically imply the other. At a kink, left and right marginal values can differ.")
    with st.expander("Scope and sources"):
        st.write("The model assumes fixed resource use and profit per unit, divisible products and no resource purchase costs. The heatmap is deterministic, not a risk forecast. Notebook data provenance is recorded in data/provenance.json.")
        st.markdown("- COMP857 assignment brief and supplied lecture materials.\n- [Gurobi linear constraint attributes](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/constraintlinear.html)\n- [Gurobi variable attributes](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/variable.html)\n- [SciPy linprog](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)")

st.divider()
st.caption("Live solver: SciPy/HiGHS. Baseline and analytical checks correspond to the COMP857 notebook. This explorer supplements the report and does not replace its reproducible notebook.")
