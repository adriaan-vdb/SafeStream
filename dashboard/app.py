"""SafeStream Streamlit moderator dashboard.

TODO(stage-7): Implement real-time log streaming (tail -f style)
TODO(stage-7): Add rolling toxic-message ratio plotting
TODO(stage-7): Add buttons to trigger gifts and disconnect users
TODO(stage-7): Create moderator interface for chat management
"""

import glob
import json
import time
from datetime import datetime

import altair as alt
import pandas as pd
import requests
import streamlit as st

# Optional: watchdog for file tailing
try:
    # from watchdog.events import FileSystemEventHandler
    # from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

# Suppress pandas warnings
import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")

LOG_GLOB = "logs/*.jsonl"
METRICS_URL = "http://localhost:8000/metrics"
PINK = "#ff0050"

st.set_page_config(
    page_title="SafeStream Moderator Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for dark mode and TikTok pink accents ---
CUSTOM_CSS = f"""
<style>
body, .stApp {{ background: #181818 !important; color: #fff !important; }}
[data-testid="stMetricValue"] {{ color: {PINK} !important; }}
.stButton>button {{ border: 2px solid {PINK}; color: #fff; background: #181818; }}
.stButton>button:hover {{ background: {PINK}; color: #fff; }}
.stTextInput>div>input {{ border: 2px solid {PINK}; }}
.stDataFrame th, .stDataFrame td {{ border-color: {PINK} !important; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Data Source Selection ---
data_source = st.sidebar.radio("Data Source", ["Log File Tail", "Metrics API Poll"])

# --- DataFrame State ---
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()


# --- Helper: Parse log line ---
def parse_log_line(line):
    try:
        data = json.loads(line)
        ts = data.get("ts") or data.get("timestamp") or datetime.now().isoformat()
        user = data.get("user") or data.get("from") or ""
        msg = data.get("message") or data.get("msg")
        toxic = data.get("toxic", False)
        score = data.get("score", 0.0)
        gift = data.get("gift_id") or data.get("gift")
        amount = data.get("amount")
        return {
            "ts": ts,
            "user": user,
            "msg": msg,
            "toxic": toxic,
            "score": score,
            "gift": gift,
            "amount": amount,
        }
    except Exception:
        return None


# --- Data Fetching ---
def fetch_log_tail():
    files = sorted(glob.glob(LOG_GLOB), reverse=True)
    if not files:
        return pd.DataFrame(
            columns=["ts", "user", "msg", "toxic", "score", "gift", "amount"]
        )
    latest = files[0]
    rows = []
    try:
        with open(latest) as f:
            for line in f.readlines()[-200:]:
                parsed = parse_log_line(line)
                if parsed:
                    rows.append(parsed)
    except Exception:
        pass
    return pd.DataFrame(rows)


def fetch_metrics_poll():
    try:
        r = requests.get(METRICS_URL, timeout=1)
        if r.ok:
            m = r.json()
            now = datetime.now().isoformat()
            return pd.DataFrame(
                [
                    {
                        "ts": now,
                        "user": "-",
                        "msg": None,
                        "toxic": None,
                        "score": None,
                        "gift": None,
                        "amount": None,
                        "viewer_count": m.get("viewer_count", 0),
                        "gift_count": m.get("gift_count", 0),
                        "toxic_pct": m.get("toxic_pct", 0.0),
                    }
                ]
            )
    except Exception:
        pass
    return pd.DataFrame()


# --- Main Data Update Loop ---
def update_data():
    if data_source == "Log File Tail":
        st.session_state.df = fetch_log_tail()
    else:
        st.session_state.df = fetch_metrics_poll()


# --- UI: Top KPIs ---
def render_kpis(df):
    if data_source == "Log File Tail":
        viewer_count = "-"
        # Fix pandas warning by using a safer approach
        if not df.empty and "amount" in df:
            amount_series = df["amount"].dropna()
            gift_count = (
                int(amount_series.astype(int).sum()) if not amount_series.empty else 0
            )
        else:
            gift_count = 0
        toxic_pct = (
            (df["toxic"].sum() / len(df) * 100)
            if (not df.empty and df["toxic"].notnull().any())
            else 0.0
        )
    else:
        # Metrics poll
        viewer_count = int(df["viewer_count"].iloc[-1]) if not df.empty else 0
        gift_count = int(df["gift_count"].iloc[-1]) if not df.empty else 0
        toxic_pct = float(df["toxic_pct"].iloc[-1]) if not df.empty else 0.0
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Viewers", viewer_count)
    kpi2.metric("Total Gifts", gift_count)
    kpi3.metric("Toxic %", f"{toxic_pct:.1f}%")


# --- UI: Rolling Table with Filtering ---
def render_table(df):
    st.subheader("Recent Messages")
    filter_user = st.text_input("Filter by username", "", key="filter_user_input")
    filter_toxic = st.checkbox("Show only toxic", False, key="filter_toxic_checkbox")
    filtered = df.copy()
    if filter_user:
        filtered = filtered[
            filtered["user"].str.contains(filter_user, case=False, na=False)
        ]
    if filter_toxic:
        filtered = filtered[filtered["toxic"]]

    def highlight_toxic(row):
        return ["background-color: #ffcccc;" if row.toxic else "" for _ in row]

    if not filtered.empty:
        st.dataframe(
            filtered.tail(200).style.apply(highlight_toxic, axis=1),
            use_container_width=True,
        )
    else:
        st.info("No messages to display.")


# --- UI: Charts ---
def render_charts(df):
    st.subheader("Analytics")
    # Line: Toxic % over time
    if not df.empty and "ts" in df and "toxic" in df:
        df_time = df.copy()
        df_time["ts"] = pd.to_datetime(df_time["ts"], errors="coerce")
        df_time = df_time.dropna(subset=["ts"])
        if not df_time.empty:
            df_time = df_time.sort_values("ts")
            window = 60
            df_time["toxic_rolling"] = (
                df_time["toxic"]
                .rolling(window=min(window, len(df_time)), min_periods=1)
                .mean()
                * 100
            )
            chart = (
                alt.Chart(df_time)
                .mark_line(color=PINK)
                .encode(
                    x=alt.X("ts:T", title="Time"),
                    y=alt.Y("toxic_rolling:Q", title="Toxic % (rolling)"),
                )
                .properties(height=200)
            )
            st.altair_chart(chart, use_container_width=True)
    # Bar: Top gifters
    if not df.empty and "user" in df and "amount" in df:
        df_gift = df[df["amount"].notnull() & df["user"].notnull()]
        if not df_gift.empty:
            top_gifters = (
                df_gift.groupby("user")["amount"].sum().nlargest(10).reset_index()
            )
            bar = (
                alt.Chart(top_gifters)
                .mark_bar(color=PINK)
                .encode(
                    x=alt.X("amount:Q", title="Gift Amount"),
                    y=alt.Y("user:N", sort="-x", title="User"),
                    tooltip=["user", "amount"],
                )
                .properties(height=200)
            )
            st.altair_chart(bar, use_container_width=True)


# --- UI: Admin Actions ---
def render_actions():
    st.subheader("Admin Actions")
    username = st.text_input("Username to moderate", "", key="moderate_username_input")
    col1, col2 = st.columns(2)
    if col1.button("Kick", use_container_width=True, key="kick_button"):
        if username:
            try:
                r = requests.post(
                    "http://localhost:8000/api/admin/kick", json={"username": username}
                )
                if r.ok:
                    st.success(f"Kicked {username}")
                else:
                    st.error(f"Failed to kick {username}")
            except Exception as e:
                st.error(f"Error: {e}")
    if col2.button("Mute 5 min", use_container_width=True, key="mute_button"):
        if username:
            try:
                r = requests.post(
                    "http://localhost:8000/api/admin/mute", json={"username": username}
                )
                if r.ok:
                    st.success(f"Muted {username} for 5 min")
                else:
                    st.error(f"Failed to mute {username}")
            except Exception as e:
                st.error(f"Error: {e}")


# --- Main App Loop ---
def main():
    st.title("SafeStream Moderator Dashboard")

    # Add auto-refresh control
    col1, col2 = st.columns([3, 1])
    with col2:
        auto_refresh = st.checkbox(
            "Auto-refresh", value=True, key="auto_refresh_checkbox"
        )
        if st.button("Refresh Now", key="manual_refresh_button"):
            st.rerun()

    # Update data
    update_data()

    # Render dashboard components
    render_kpis(st.session_state.df)
    render_table(st.session_state.df)
    render_charts(st.session_state.df)
    render_actions()

    # Auto-refresh every 5 seconds if enabled
    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main()
