"""SafeStream Streamlit moderator dashboard.

Database-powered real-time dashboard for chat moderation and analytics.
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

# Suppress pandas warnings
import warnings

import altair as alt
import pandas as pd
import requests
import streamlit as st
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Import database models and service
from app.db.models import GiftEvent, Message, User

warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")

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
data_source = st.sidebar.radio("Data Source", ["Database Query", "Metrics API Poll"])

# --- DataFrame State ---
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()


# --- Database Connection ---
@st.cache_resource
def get_database_engine():
    """Get database engine with caching."""
    database_url = "sqlite+aiosqlite:///safestream.db"
    return create_async_engine(database_url, echo=False)


async def fetch_database_messages():
    """Fetch recent messages from database."""
    engine = get_database_engine()
    async with AsyncSession(engine) as session:
        # Get recent messages with user information
        stmt = (
            select(Message, User)
            .join(User, Message.user_id == User.id)
            .order_by(desc(Message.timestamp))
            .limit(200)
        )
        result = await session.execute(stmt)
        rows = []
        for message, user in result:
            rows.append(
                {
                    "ts": message.timestamp.isoformat(),
                    "user": user.username,
                    "msg": message.message_text,
                    "toxic": message.toxicity_flag,
                    "score": message.toxicity_score or 0.0,
                    "gift": None,
                    "amount": None,
                }
            )

        # Get recent gift events
        gift_stmt = (
            select(GiftEvent, User)
            .join(User, GiftEvent.from_user_id == User.id)
            .order_by(desc(GiftEvent.timestamp))
            .limit(50)
        )
        gift_result = await session.execute(gift_stmt)
        for gift, user in gift_result:
            rows.append(
                {
                    "ts": gift.timestamp.isoformat(),
                    "user": user.username,
                    "msg": None,
                    "toxic": None,
                    "score": None,
                    "gift": gift.gift_id,
                    "amount": gift.amount,
                }
            )

        return pd.DataFrame(rows)


def fetch_metrics_poll():
    """Fetch metrics from API."""
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
    """Update data from selected source."""
    if data_source == "Database Query":
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            st.session_state.df = loop.run_until_complete(fetch_database_messages())
            loop.close()
        except Exception as e:
            st.error(f"Database query failed: {e}")
            st.session_state.df = pd.DataFrame()
    else:
        st.session_state.df = fetch_metrics_poll()


# --- UI: Top KPIs ---
def render_kpis(df):
    """Render key performance indicators."""
    if data_source == "Database Query":
        viewer_count = "-"
        # Calculate gift count from database data
        if not df.empty and "amount" in df:
            amount_series = df["amount"].dropna()
            gift_count = (
                int(amount_series.astype(int).sum()) if not amount_series.empty else 0
            )
        else:
            gift_count = 0
        # Calculate toxic percentage from database data
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
    """Render message table with filtering."""
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
        # Sort by timestamp and show most recent first
        filtered = filtered.sort_values("ts", ascending=False)
        st.dataframe(
            filtered.head(200).style.apply(highlight_toxic, axis=1),
            use_container_width=True,
        )
    else:
        st.info("No messages to display.")


# --- UI: Charts ---
def render_charts(df):
    """Render analytics charts."""
    st.subheader("Analytics")

    # Line: Toxic % over time
    if not df.empty and "ts" in df and "toxic" in df:
        df_time = df[df["toxic"].notnull()].copy()
        if not df_time.empty:
            df_time["ts"] = pd.to_datetime(df_time["ts"], errors="coerce")
            df_time = df_time.dropna(subset=["ts"])
            if not df_time.empty:
                df_time = df_time.sort_values("ts")
                window = min(60, len(df_time))
                df_time["toxic_rolling"] = (
                    df_time["toxic"].rolling(window=window, min_periods=1).mean() * 100
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
            if not top_gifters.empty:
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
    """Render admin action buttons."""
    st.subheader("Admin Actions")
    username = st.text_input("Username to moderate", "", key="moderate_username_input")
    col1, col2 = st.columns(2)

    if col1.button("Kick", use_container_width=True, key="kick_button"):
        if username:
            try:
                r = requests.post(
                    "http://localhost:8000/api/admin/kick",
                    json={"username": username},
                    timeout=5,
                )
                if r.ok:
                    st.success(f"Kicked {username}")
                else:
                    st.error(f"Failed to kick {username}: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

    if col2.button("Mute 5 min", use_container_width=True, key="mute_button"):
        if username:
            try:
                r = requests.post(
                    "http://localhost:8000/api/admin/mute",
                    json={"username": username},
                    timeout=5,
                )
                if r.ok:
                    st.success(f"Muted {username} for 5 min")
                else:
                    st.error(f"Failed to mute {username}: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")


# --- Main App Loop ---
def main():
    """Main dashboard application."""
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
