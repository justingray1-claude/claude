"""
Retirement Monte Carlo — Streamlit Dashboard
=============================================
Run with:  streamlit run finances/dashboard.py
"""

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# Allow importing from sibling file
sys.path.insert(0, str(Path(__file__).parent))
from retirement_sim import run_simulation

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retirement Simulator",
    page_icon="📈",
    layout="wide",
)

st.title("Retirement Monte Carlo Simulator")
st.caption("Adjust the dials to see how changes affect your probability of success.")

# ── Sidebar controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Your Numbers")

    st.subheader("Portfolio")
    invest_portfolio = st.slider(
        "Invested assets (401k + brokerage)",
        min_value=250_000,
        max_value=10_000_000,
        value=2_200_000,
        step=50_000,
        format="$%d",
    )
    cash_buffer = st.slider(
        "Cash buffer (HYSA / savings)",
        min_value=0,
        max_value=1_000_000,
        value=200_000,
        step=10_000,
        format="$%d",
    )

    st.subheader("Spending")
    annual_spend = st.slider(
        "Annual spending",
        min_value=20_000,
        max_value=300_000,
        value=80_000,
        step=5_000,
        format="$%d",
    )

    st.subheader("Ages")
    current_age = st.slider("Current age", min_value=30, max_value=70, value=45)
    target_age = st.slider("Target age (money must last to)", min_value=75, max_value=105, value=90)

    st.subheader("Market Assumptions (Real / Inflation-Adjusted)")
    mean_return = st.slider(
        "Average annual return",
        min_value=1.0,
        max_value=12.0,
        value=6.0,
        step=0.5,
        format="%.1f%%",
    )
    std_return = st.slider(
        "Return volatility (std dev)",
        min_value=2.0,
        max_value=25.0,
        value=12.0,
        step=0.5,
        format="%.1f%%",
    )
    cash_yield = st.slider(
        "Cash buffer real yield",
        min_value=0.0,
        max_value=5.0,
        value=2.0,
        step=0.25,
        format="%.2f%%",
    )

    n_sims = st.select_slider(
        "Simulations",
        options=[10_000, 25_000, 50_000, 100_000],
        value=50_000,
    )

# ── Run primary simulation ────────────────────────────────────────────────────
results = run_simulation(
    invest_portfolio=invest_portfolio,
    cash_buffer=cash_buffer,
    annual_spend=annual_spend,
    current_age=current_age,
    target_age=target_age,
    mean_real_return=mean_return / 100,
    std_real_return=std_return / 100,
    cash_yield_real=cash_yield / 100,
    n_simulations=n_sims,
    random_seed=42,
)

sr = results["success_rate"] * 100
total_assets = invest_portfolio + cash_buffer
wr = annual_spend / total_assets * 100
years = target_age - current_age
fv = results["final_values"]
fa = results["failure_ages"]

# ── Success rate — big hero number ───────────────────────────────────────────
color = "#2ecc71" if sr >= 90 else "#f39c12" if sr >= 80 else "#e74c3c"

col_hero, col_stats = st.columns([1, 2])

with col_hero:
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sr,
        number={"suffix": "%", "font": {"size": 52}},
        title={"text": "Probability of Success", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 80], "color": "#fadbd8"},
                {"range": [80, 90], "color": "#fdebd0"},
                {"range": [90, 100], "color": "#d5f5e3"},
            ],
            "threshold": {
                "line": {"color": "#2c3e50", "width": 3},
                "thickness": 0.75,
                "value": 90,
            },
        },
    ))
    gauge.update_layout(height=280, margin=dict(t=40, b=10, l=30, r=30))
    st.plotly_chart(gauge, use_container_width=True)

with col_stats:
    st.subheader("Key Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Assets", f"${total_assets:,.0f}")
    m2.metric("Annual Spend", f"${annual_spend:,.0f}")
    m3.metric("Withdrawal Rate", f"{wr:.1f}%", delta=f"{'Safe' if wr < 4 else 'High'}", delta_color="normal" if wr < 4 else "inverse")
    m4.metric("Years in Retirement", f"{years}")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Successes", f"{results['successes']:,}")
    m6.metric("Failures", f"{n_sims - results['successes']:,}")
    if len(fv):
        m7.metric("Median Portfolio at 90", f"${np.median(fv):,.0f}")
        m8.metric("10th Pct at 90", f"${np.percentile(fv, 10):,.0f}")

st.divider()

# ── Row 2: Failure timing + Portfolio distribution ────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("When Do Failures Happen?")
    ages = list(range(current_age + 5, target_age + 1, 5))
    failure_pcts = [(fa < age).sum() / n_sims * 100 for age in ages] if len(fa) else [0] * len(ages)

    fig_fail = go.Figure(go.Bar(
        x=[f"Before {a}" for a in ages],
        y=failure_pcts,
        marker_color=[
            "#e74c3c" if p > 5 else "#f39c12" if p > 2 else "#2ecc71"
            for p in failure_pcts
        ],
        text=[f"{p:.1f}%" for p in failure_pcts],
        textposition="outside",
    ))
    fig_fail.update_layout(
        yaxis_title="% of all simulations",
        yaxis=dict(range=[0, max(max(failure_pcts) * 1.3, 2)]),
        margin=dict(t=20, b=10),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig_fail, use_container_width=True)

with col_r:
    st.subheader(f"Portfolio Value at Age {target_age} (Successful Runs)")
    if len(fv):
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        pct_values = [np.percentile(fv, p) for p in percentiles]
        labels = [f"{p}th" for p in percentiles]

        fig_pct = go.Figure()
        fig_pct.add_trace(go.Bar(
            x=labels,
            y=pct_values,
            marker_color=px.colors.sequential.Blues[1:],
            text=[f"${v/1e6:.1f}M" if v >= 1e6 else f"${v:,.0f}" for v in pct_values],
            textposition="outside",
        ))
        fig_pct.update_layout(
            yaxis_title="Portfolio Value ($)",
            yaxis=dict(tickformat="$,.0f"),
            margin=dict(t=20, b=10),
            height=320,
            showlegend=False,
        )
        st.plotly_chart(fig_pct, use_container_width=True)
    else:
        st.warning("No successful runs to display.")

st.divider()

# ── Row 3: Spending sensitivity + Return sensitivity ─────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Spending Sensitivity")
    with st.spinner("Running sensitivity..."):
        spend_range = range(
            max(20_000, annual_spend - 40_000),
            annual_spend + 50_000,
            5_000,
        )
        spend_rates = []
        spend_labels = []
        for s in spend_range:
            r = run_simulation(
                invest_portfolio=invest_portfolio,
                cash_buffer=cash_buffer,
                annual_spend=s,
                current_age=current_age,
                target_age=target_age,
                mean_real_return=mean_return / 100,
                std_real_return=std_return / 100,
                cash_yield_real=cash_yield / 100,
                n_simulations=5_000,
                random_seed=42,
            )
            spend_rates.append(r["success_rate"] * 100)
            spend_labels.append(s)

    fig_spend = go.Figure()
    fig_spend.add_trace(go.Scatter(
        x=spend_labels,
        y=spend_rates,
        mode="lines+markers",
        line=dict(color="#3498db", width=3),
        marker=dict(size=7),
        name="Success Rate",
    ))
    fig_spend.add_vline(
        x=annual_spend,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"  Current: ${annual_spend:,.0f}",
        annotation_position="top right",
    )
    fig_spend.add_hline(y=90, line_dash="dot", line_color="#2ecc71", annotation_text="  90% target")
    fig_spend.update_layout(
        xaxis_title="Annual Spending ($)",
        yaxis_title="Success Rate (%)",
        xaxis=dict(tickformat="$,.0f"),
        yaxis=dict(range=[0, 105]),
        margin=dict(t=20, b=10),
        height=350,
        showlegend=False,
    )
    st.plotly_chart(fig_spend, use_container_width=True)

with col_b:
    st.subheader("Return Assumption Sensitivity")
    with st.spinner("Running sensitivity..."):
        return_range = np.arange(2.0, 11.5, 0.5)
        return_rates = []
        for ret in return_range:
            r = run_simulation(
                invest_portfolio=invest_portfolio,
                cash_buffer=cash_buffer,
                annual_spend=annual_spend,
                current_age=current_age,
                target_age=target_age,
                mean_real_return=ret / 100,
                std_real_return=std_return / 100,
                cash_yield_real=cash_yield / 100,
                n_simulations=5_000,
                random_seed=42,
            )
            return_rates.append(r["success_rate"] * 100)

    fig_ret = go.Figure()
    fig_ret.add_trace(go.Scatter(
        x=list(return_range),
        y=return_rates,
        mode="lines+markers",
        line=dict(color="#9b59b6", width=3),
        marker=dict(size=7),
    ))
    fig_ret.add_vline(
        x=mean_return,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"  Current: {mean_return:.1f}%",
        annotation_position="top right",
    )
    fig_ret.add_hline(y=90, line_dash="dot", line_color="#2ecc71", annotation_text="  90% target")
    fig_ret.update_layout(
        xaxis_title="Mean Real Return (%)",
        yaxis_title="Success Rate (%)",
        xaxis=dict(tickformat=".1f", ticksuffix="%"),
        yaxis=dict(range=[0, 105]),
        margin=dict(t=20, b=10),
        height=350,
        showlegend=False,
    )
    st.plotly_chart(fig_ret, use_container_width=True)

st.divider()

# ── Row 4: Monte Carlo fan chart ──────────────────────────────────────────────
st.subheader("Portfolio Paths — Monte Carlo Fan")

with st.spinner("Generating fan chart..."):
    n_fan = 500
    fan_years = np.arange(0, years + 1)
    rng_fan = np.random.default_rng(99)
    fan_returns = rng_fan.normal(mean_return / 100, std_return / 100, (n_fan, years))
    fan_portfolios = np.zeros((n_fan, years + 1))
    fan_portfolios[:, 0] = invest_portfolio + cash_buffer

    for yr in range(years):
        fan_portfolios[:, yr + 1] = np.maximum(
            0,
            fan_portfolios[:, yr] * (1 + fan_returns[:, yr]) - annual_spend,
        )

    # Compute percentile bands
    p10 = np.percentile(fan_portfolios, 10, axis=0)
    p25 = np.percentile(fan_portfolios, 25, axis=0)
    p50 = np.percentile(fan_portfolios, 50, axis=0)
    p75 = np.percentile(fan_portfolios, 75, axis=0)
    p90 = np.percentile(fan_portfolios, 90, axis=0)
    age_axis = [current_age + y for y in fan_years]

fig_fan = go.Figure()

# Shaded bands
fig_fan.add_trace(go.Scatter(
    x=age_axis + age_axis[::-1],
    y=list(p90) + list(p10[::-1]),
    fill="toself", fillcolor="rgba(52,152,219,0.10)",
    line=dict(color="rgba(255,255,255,0)"),
    name="10–90th pct",
))
fig_fan.add_trace(go.Scatter(
    x=age_axis + age_axis[::-1],
    y=list(p75) + list(p25[::-1]),
    fill="toself", fillcolor="rgba(52,152,219,0.22)",
    line=dict(color="rgba(255,255,255,0)"),
    name="25–75th pct",
))

# Percentile lines
for y_vals, name, color, dash in [
    (p90, "90th pct", "#2980b9", "dot"),
    (p75, "75th pct", "#3498db", "dash"),
    (p50, "Median",   "#2c3e50", "solid"),
    (p25, "25th pct", "#e67e22", "dash"),
    (p10, "10th pct", "#e74c3c", "dot"),
]:
    fig_fan.add_trace(go.Scatter(
        x=age_axis, y=y_vals,
        mode="lines", name=name,
        line=dict(color=color, width=2, dash=dash),
    ))

fig_fan.add_hline(y=0, line_color="#e74c3c", line_width=1, annotation_text="  $0 — Ruin")
fig_fan.update_layout(
    xaxis_title="Age",
    yaxis_title="Portfolio Value ($)",
    yaxis=dict(tickformat="$,.0f"),
    height=420,
    margin=dict(t=20, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_fan, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.caption(
    "All returns are real (inflation-adjusted). "
    "The bucket strategy models drawing from cash in down years and replenishing in up years. "
    "This is for informational purposes only — not financial advice."
)
