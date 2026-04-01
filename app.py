import streamlit as st
import pandas as pd

# ----------------------------------
# 🎨 PAGE CONFIG
# ----------------------------------
st.set_page_config(page_title="WR Tracker Dashboard", layout="wide")
st.title("📊 WR Tracker Dashboard")

# ----------------------------------
# 📂 FILE PATH
# ----------------------------------
file_path = "wr_tracker_full_dummy.xlsx"

# ----------------------------------
# 📥 LOAD DATA
# ----------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(file_path)

    df.columns = df.columns.str.replace("\n", " ").str.strip()

    df["TCV"] = (
        df["TCV"].astype(str)
        .str.replace(",", "")
        .str.replace("₹", "")
        .str.strip()
    )
    df["TCV"] = pd.to_numeric(df["TCV"], errors="coerce").fillna(0)

    date_cols = [
        "Signed Date", "Start Date", "End Date",
        "Current Contract End Date",
        "Current PO End Date / Forecasted Date for PO Consumption"
    ]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


# ----------------------------------
# 🚨 LOAD
# ----------------------------------
try:
    df = load_data()

    # ----------------------------------
    # 🔐 SESSION STATE
    # ----------------------------------
    if "selected_wr" not in st.session_state:
        st.session_state.selected_wr = None

    # ----------------------------------
    # 🔍 SIDEBAR FILTERS
    # ----------------------------------
    st.sidebar.header("🔍 Filters")

    wr_list = sorted(df["WR Reference"].dropna().unique().tolist())
    selected_wr = st.sidebar.selectbox("Select WR", ["All"] + wr_list)

    if selected_wr != "All":
        opp_list = sorted(
            df[df["WR Reference"] == selected_wr]["Opp Name"].dropna().unique().tolist()
        )
    else:
        opp_list = sorted(df["Opp Name"].dropna().unique().tolist())

    selected_opp = st.sidebar.selectbox("Select Opp Name", ["All"] + opp_list)

    status_options = df["Status"].dropna().unique()
    status_filter = st.sidebar.multiselect("Status", status_options, default=status_options)

    # ----------------------------------
    # 📄 WR DETAIL PAGE
    # ----------------------------------
    if st.session_state.selected_wr is not None:

        row = st.session_state.selected_wr

        st.subheader(f"📄 WR Details: {row['WR Reference']}")

        if st.button("⬅️ Back"):
            st.session_state.selected_wr = None
            st.rerun()

        st.markdown(
            "<style>.big-font {font-size:18px; font-weight:500;}</style>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"<div class='big-font'><b>Project:</b> {row['Transform / Project']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>TCV:</b> ₹ {row['TCV']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>Start Date:</b> {row['Start Date']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>End Date:</b> {row['End Date']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>Risk:</b> {row['Risk to Delivery']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>Next Steps:</b> {row['Next Steps']}</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"<div class='big-font'><b>IBM Owner:</b> {row['IBM Owner']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>KD Owner:</b> {row['KD Programme level owner']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>PM:</b> {row['KD PM on PCR']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-font'><b>Contract End:</b> {row['Current Contract End Date']}</div>", unsafe_allow_html=True)

        st.stop()

    # ----------------------------------
    # 📌 SUMMARY
    # ----------------------------------
    st.subheader("📌 Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total WRs", len(df))
    col2.metric("Signed", df[df["Status"] == "Signed"].shape[0])
    col3.metric("Pending", df[df["Status"] != "Signed"].shape[0])
    col4.metric("On Hold", df[df["Status"] == "On Hold"].shape[0])

    # ----------------------------------
    # 📋 WR LIST
    # ----------------------------------
    st.subheader("📋 WR List")

    if selected_wr == "All" and selected_opp == "All":
        st.info("🔎 Please select WR or Opp Name from filters")
    else:
        filtered_df = df.copy()

        if selected_wr != "All":
            filtered_df = filtered_df[filtered_df["WR Reference"] == selected_wr]

        if selected_opp != "All":
            filtered_df = filtered_df[filtered_df["Opp Name"] == selected_opp]

        if len(status_filter) != len(status_options):
            filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]

        if filtered_df.empty:
            st.warning("No matching WR found")
        else:
            st.markdown("### ⬇ Click WR below to view details")

            for idx, row in filtered_df.iterrows():
                col1, col2 = st.columns([8, 2])

                col1.markdown(
                    f"<div style='background:#007BFF;color:white;padding:10px;border-radius:8px'>{row['WR Reference']} | {row['Opp Name']} | {row['Status']}</div>",
                    unsafe_allow_html=True
                )

                if col2.button("View", key=f"view_{idx}"):
                    st.session_state.selected_wr = row
                    st.rerun()

    st.markdown("---")

    # ----------------------------------
    # ⚠️ CONTRACT ALERTS
    # ----------------------------------
    st.subheader("⚠️ Contract Alerts")

    today = pd.Timestamp.today()

    expiring = df[
        (df["Current Contract End Date"].notna()) &
        (df["Current Contract End Date"] >= today) &
        (df["Current Contract End Date"] <= today + pd.Timedelta(days=30))
    ].sort_values(by="Current Contract End Date")

    if not expiring.empty:
        st.markdown("### ⏳ Expiring Soon (Next 30 Days)")
        st.dataframe(expiring[["WR Reference", "Opp Name", "Current Contract End Date"]])
    else:
        st.info("No contracts expiring in next 30 days")

    st.markdown("---")

    # ----------------------------------
    # 📋 WR TABLE
    # ----------------------------------
    st.subheader("📋 WR Detailed Table")

    table_search = st.text_input("🔎 Search in table")

    table_df = df.copy()

    if table_search:
        table_df = table_df[
            table_df["WR Reference"].astype(str).str.contains(table_search, case=False) |
            table_df["Opp Name"].astype(str).str.contains(table_search, case=False)
        ]

    st.dataframe(table_df, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")