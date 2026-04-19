"""
Premier League Player Stats Dashboard
======================================
Run with:  streamlit run soccer/pl_dashboard.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from pl_data import STAT_TYPES, fetch_player_stats, get_seasons

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PL Player Stats",
    page_icon="⚽",
    layout="wide",
)

# ── Helpers ───────────────────────────────────────────────────────────────────
POS_MAP = {
    "All":        None,
    "Forwards":   "F",
    "Midfielders":"M",
    "Defenders":  "D",
    "Goalkeepers":"G",
}

LEADERBOARD_COLS = {
    "name":             "Player",
    "team":             "Team",
    "position":         "Position",
    "appearances":      "Apps",
    "mins_played":      "Mins",
    "goals":            "Goals",
    "goal_assist":      "Assists",
    "goal_involvements":"G+A",
    "total_scoring_att":"Shots",
    "shot_conversion":  "Conv %",
    "big_chance_created":"Big Chances",
    "total_pass":       "Passes",
    "total_tackle":     "Tackles",
    "tackle_success":   "Tackle %",
    "interception":     "Interceptions",
    "saves":            "Saves",
    "yellow_card":      "YC",
    "red_card":         "RC",
}

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner="Fetching Premier League data…")
def load_data(season_id: int) -> pd.DataFrame:
    return fetch_player_stats(season_id)


@st.cache_data(ttl=86400, show_spinner=False)
def load_seasons() -> dict:
    return get_seasons()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ PL Player Stats")
    st.divider()

    seasons = load_seasons()
    season_label = st.selectbox("Season", list(seasons.keys()), index=1)
    season_id = seasons[season_label]

    st.divider()
    pos_choice = st.radio("Position", list(POS_MAP.keys()), horizontal=True)
    min_mins = st.slider("Min. minutes played", 0, 3000, 200, step=50)

    df_raw = load_data(season_id)

    teams = sorted(df_raw["team"].dropna().unique().tolist())
    selected_teams = st.multiselect("Teams", teams, default=[])

    st.divider()
    st.caption("Data: Premier League API · No API key required")

# ── Filter ────────────────────────────────────────────────────────────────────
df = df_raw.copy()
if POS_MAP[pos_choice]:
    df = df[df["position_short"] == POS_MAP[pos_choice]]
if selected_teams:
    df = df[df["team"].isin(selected_teams)]
df = df[df["mins_played"] >= min_mins]

# ── Header ────────────────────────────────────────────────────────────────────
st.title(f"Premier League Player Stats — {season_label}")
st.caption(f"{len(df)} players shown · {int(df['goals'].sum())} goals · {int(df['goal_assist'].sum())} assists")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_board, tab_player, tab_compare = st.tabs(["📊 Leaderboard", "👤 Player Profile", "⚖️ Compare"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — LEADERBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with tab_board:
    sort_by = st.selectbox(
        "Sort by",
        options=list(LEADERBOARD_COLS.keys())[3:],
        format_func=lambda k: LEADERBOARD_COLS[k],
        index=2,   # goals
    )

    show_cols = list(LEADERBOARD_COLS.keys())
    display = (
        df[show_cols]
        .rename(columns=LEADERBOARD_COLS)
        .sort_values(LEADERBOARD_COLS[sort_by], ascending=False)
        .reset_index(drop=True)
    )
    display.index += 1

    st.dataframe(
        display,
        use_container_width=True,
        height=600,
        column_config={
            "Player":       st.column_config.TextColumn(width="medium"),
            "Team":         st.column_config.TextColumn(width="small"),
            "Conv %":       st.column_config.NumberColumn(format="%.1f%%"),
            "Tackle %":     st.column_config.NumberColumn(format="%.1f%%"),
            "Goals":        st.column_config.NumberColumn(),
            "Assists":      st.column_config.NumberColumn(),
        },
    )

    st.divider()

    # ── Summary scatter ──────────────────────────────────────────────────────
    st.subheader("Goals vs Assists")
    scatter_df = df[df["appearances"] >= 5].copy()
    fig_scatter = px.scatter(
        scatter_df,
        x="goal_assist",
        y="goals",
        color="team",
        size="mins_played",
        hover_name="name",
        hover_data={"team": True, "appearances": True, "mins_played": True,
                    "goals": True, "goal_assist": True},
        labels={"goal_assist": "Assists", "goals": "Goals"},
        height=480,
    )
    fig_scatter.update_traces(marker=dict(opacity=0.75, line=dict(width=0.5, color="white")))
    fig_scatter.update_layout(margin=dict(t=20, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PLAYER PROFILE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_player:
    player_names = df.sort_values("goals", ascending=False)["name"].tolist()
    selected_name = st.selectbox("Select player", player_names)

    player = df[df["name"] == selected_name].iloc[0]

    # ── Hero stats ────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Goals",       int(player["goals"]))
    c2.metric("Assists",     int(player["goal_assist"]))
    c3.metric("G+A",         int(player["goal_involvements"]))
    c4.metric("Apps",        int(player["appearances"]))
    c5.metric("Minutes",     f"{int(player['mins_played']):,}")
    c6.metric("Shots",       int(player["total_scoring_att"]))

    st.caption(
        f"**{player['team']}** · {player['position']} · "
        f"{player['nationality']} · #{int(player['shirt']) if player['shirt'] else '—'}"
    )
    st.divider()

    # ── Row 1: Bar chart + Per-90 radar ──────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Key Stats vs League")
        stats_to_show = [
            ("goals",           "Goals"),
            ("goal_assist",     "Assists"),
            ("total_scoring_att","Shots"),
            ("big_chance_created","Big Chances"),
            ("total_tackle",    "Tackles"),
            ("interception",    "Interceptions"),
        ]
        # Filter to relevant position
        league_df = df_raw[df_raw["mins_played"] >= 500]

        bars = []
        for col, label in stats_to_show:
            player_val = float(player[col])
            league_avg = float(league_df[col].mean())
            league_max = float(league_df[col].max())
            bars.append({
                "stat": label,
                "player": player_val,
                "avg": round(league_avg, 1),
                "max": round(league_max, 1),
            })

        bar_df = pd.DataFrame(bars)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="League Avg",
            x=bar_df["stat"],
            y=bar_df["avg"],
            marker_color="#546e7a",
            opacity=0.6,
        ))
        fig_bar.add_trace(go.Bar(
            name=selected_name.split()[-1],
            x=bar_df["stat"],
            y=bar_df["player"],
            marker_color="#e74c3c",
        ))
        fig_bar.update_layout(
            barmode="group",
            height=340,
            margin=dict(t=20, b=10),
            legend=dict(orientation="h", y=1.08),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_r:
        st.subheader("Per-90 Min Profile")
        # Radar chart with per-90 stats
        p90_metrics = {
            "Goals p90":        "goals_p90",
            "Assists p90":      "assists_p90",
            "Shots p90":        "shots_p90",
            "Tackles p90":      "tackles_p90",
            "Passes p90 /100":  "passes_p90",
        }

        # Normalise each metric 0-1 vs full squad
        radar_vals = []
        radar_labels = []
        for label, col in p90_metrics.items():
            col_max = df_raw[col].quantile(0.95)
            val = min(float(player[col]) / max(col_max, 0.01), 1.0)
            # Special: passes divide by 100 for display
            if "100" in label:
                val = min(float(player[col]) / 100 / max(col_max / 100, 0.01), 1.0)
            radar_vals.append(round(val, 3))
            radar_labels.append(label.replace(" /100", ""))

        radar_vals_closed = radar_vals + [radar_vals[0]]
        radar_labels_closed = radar_labels + [radar_labels[0]]

        fig_radar = go.Figure(go.Scatterpolar(
            r=radar_vals_closed,
            theta=radar_labels_closed,
            fill="toself",
            fillcolor="rgba(231,76,60,0.2)",
            line=dict(color="#e74c3c", width=2),
            name=selected_name.split()[-1],
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1], showticklabels=False)),
            height=340,
            margin=dict(t=30, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ── Row 2: Shot conversion + discipline ──────────────────────────────────
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("Shooting")
        goals = int(player["goals"])
        shots = int(player["total_scoring_att"])
        missed = shots - goals
        fig_donut = go.Figure(go.Pie(
            values=[goals, missed],
            labels=["Goals", "Missed/Saved"],
            hole=0.55,
            marker_colors=["#2ecc71", "#546e7a"],
        ))
        fig_donut.update_layout(
            height=260,
            margin=dict(t=10, b=10, l=10, r=10),
            annotations=[dict(text=f"{player['shot_conversion']}%", font_size=18, showarrow=False)],
            showlegend=True,
            legend=dict(orientation="h", y=-0.1),
        )
        fig_donut.update_traces(textinfo="none")
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_b:
        st.subheader("Discipline")
        fig_disc = go.Figure()
        fig_disc.add_trace(go.Bar(
            x=["Yellow Cards", "Red Cards", "Fouls", "Offsides"],
            y=[player["yellow_card"], player["red_card"],
               player["fouls"], player["total_offside"]],
            marker_color=["#f39c12", "#e74c3c", "#3498db", "#9b59b6"],
        ))
        fig_disc.update_layout(height=260, margin=dict(t=10, b=10), showlegend=False)
        st.plotly_chart(fig_disc, use_container_width=True)

    with col_c:
        st.subheader("Defensive")
        fig_def = go.Figure()
        fig_def.add_trace(go.Bar(
            x=["Tackles", "Tackles Won", "Interceptions", "Clearances", "Aerials"],
            y=[player["total_tackle"], player["won_tackle"],
               player["interception"], player["total_clearance"],
               player["total_aerial_won"]],
            marker_color="#3498db",
        ))
        fig_def.update_layout(height=260, margin=dict(t=10, b=10), showlegend=False)
        st.plotly_chart(fig_def, use_container_width=True)

    # ── Full stat table ───────────────────────────────────────────────────────
    with st.expander("Full stat breakdown"):
        stat_rows = [
            {"Category": "Attacking",   "Stat": "Goals",            "Value": int(player["goals"])},
            {"Category": "Attacking",   "Stat": "Assists",           "Value": int(player["goal_assist"])},
            {"Category": "Attacking",   "Stat": "Goal Involvements", "Value": int(player["goal_involvements"])},
            {"Category": "Attacking",   "Stat": "Shots",             "Value": int(player["total_scoring_att"])},
            {"Category": "Attacking",   "Stat": "Shot Conversion",   "Value": f"{player['shot_conversion']}%"},
            {"Category": "Attacking",   "Stat": "Big Chances Missed","Value": int(player["big_chance_missed"])},
            {"Category": "Attacking",   "Stat": "Offsides",          "Value": int(player["total_offside"])},
            {"Category": "Creativity",  "Stat": "Big Chances Created","Value": int(player["big_chance_created"])},
            {"Category": "Creativity",  "Stat": "Through Balls",     "Value": int(player["total_through_ball"])},
            {"Category": "Creativity",  "Stat": "Crosses",           "Value": int(player["total_cross"])},
            {"Category": "Creativity",  "Stat": "Passes",            "Value": int(player["total_pass"])},
            {"Category": "Defending",   "Stat": "Tackles",           "Value": int(player["total_tackle"])},
            {"Category": "Defending",   "Stat": "Tackles Won",       "Value": int(player["won_tackle"])},
            {"Category": "Defending",   "Stat": "Tackle Success",    "Value": f"{player['tackle_success']}%"},
            {"Category": "Defending",   "Stat": "Interceptions",     "Value": int(player["interception"])},
            {"Category": "Defending",   "Stat": "Clearances",        "Value": int(player["total_clearance"])},
            {"Category": "Defending",   "Stat": "Aerials Won",       "Value": int(player["total_aerial_won"])},
            {"Category": "Goalkeeping", "Stat": "Clean Sheets",      "Value": int(player["clean_sheet"])},
            {"Category": "Goalkeeping", "Stat": "Saves",             "Value": int(player["saves"])},
            {"Category": "Discipline",  "Stat": "Yellow Cards",      "Value": int(player["yellow_card"])},
            {"Category": "Discipline",  "Stat": "Red Cards",         "Value": int(player["red_card"])},
            {"Category": "Discipline",  "Stat": "Fouls",             "Value": int(player["fouls"])},
            {"Category": "Playing Time","Stat": "Appearances",       "Value": int(player["appearances"])},
            {"Category": "Playing Time","Stat": "Minutes Played",    "Value": f"{int(player['mins_played']):,}"},
        ]
        st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMPARE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("Head-to-Head Comparison")
    all_names = df.sort_values("goals", ascending=False)["name"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        p1_name = st.selectbox("Player 1", all_names, index=0, key="cmp1")
    with col2:
        p2_name = st.selectbox("Player 2", all_names, index=1 if len(all_names) > 1 else 0, key="cmp2")

    p1 = df[df["name"] == p1_name].iloc[0]
    p2 = df[df["name"] == p2_name].iloc[0]

    compare_stats = [
        ("goals",             "Goals"),
        ("goal_assist",       "Assists"),
        ("goal_involvements", "G+A"),
        ("total_scoring_att", "Shots"),
        ("shot_conversion",   "Shot Conv %"),
        ("big_chance_created","Big Chances"),
        ("total_pass",        "Passes"),
        ("total_tackle",      "Tackles"),
        ("tackle_success",    "Tackle %"),
        ("interception",      "Interceptions"),
        ("total_clearance",   "Clearances"),
        ("saves",             "Saves"),
        ("yellow_card",       "Yellow Cards"),
        ("fouls",             "Fouls"),
        ("appearances",       "Apps"),
        ("mins_played",       "Minutes"),
    ]

    # Side-by-side metric cards
    ca, cb = st.columns(2)
    ca.markdown(f"### {p1_name}\n*{p1['team']} · {p1['position']}*")
    cb.markdown(f"### {p2_name}\n*{p2['team']} · {p2['position']}*")

    for col, label in compare_stats:
        v1 = float(p1[col])
        v2 = float(p2[col])
        delta1 = f"+{v1 - v2:.1f}" if v1 > v2 else (f"{v1 - v2:.1f}" if v1 < v2 else "—")
        delta2 = f"+{v2 - v1:.1f}" if v2 > v1 else (f"{v2 - v1:.1f}" if v2 < v1 else "—")
        ca.metric(label, f"{v1:g}", delta=delta1 if delta1 != "—" else None,
                  delta_color="normal" if v1 >= v2 else "inverse")
        cb.metric(label, f"{v2:g}", delta=delta2 if delta2 != "—" else None,
                  delta_color="normal" if v2 >= v1 else "inverse")

    st.divider()

    # Radar comparison
    st.subheader("Radar Comparison")
    radar_cats = ["goals_p90", "assists_p90", "shots_p90", "tackles_p90", "passes_p90"]
    radar_labels = ["Goals p90", "Assists p90", "Shots p90", "Tackles p90", "Passes p90"]

    def normalise(val, col):
        col_max = df_raw[col].quantile(0.95)
        return min(float(val) / max(float(col_max), 0.01), 1.0)

    v1s = [normalise(p1[c], c) for c in radar_cats]
    v2s = [normalise(p2[c], c) for c in radar_cats]

    fig_cmp = go.Figure()
    for vals, name, color in [(v1s + [v1s[0]], p1_name.split()[-1], "#e74c3c"),
                               (v2s + [v2s[0]], p2_name.split()[-1], "#3498db")]:
        fig_cmp.add_trace(go.Scatterpolar(
            r=vals,
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            name=name,
            line=dict(color=color, width=2),
        ))
    fig_cmp.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], showticklabels=False)),
        height=420,
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)
