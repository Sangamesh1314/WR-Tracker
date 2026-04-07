import streamlit as st
import pandas as pd

# ----------------------------------
# SESSION SETUP
# ----------------------------------
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin123"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = ""

# ----------------------------------
# IF NOT LOGGED IN → SHOW AUTH PAGES ONLY
# ----------------------------------
if not st.session_state.logged_in:

    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    # ---------------- REGISTER ----------------
    if menu == "Register":
        st.title("Create Account")

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):
            if new_user in st.session_state.users:
                st.error("User already exists")
            elif new_user.strip() == "" or new_pass.strip() == "":
                st.warning("Enter valid details")
            else:
                st.session_state.users[new_user] = new_pass
                st.success("Account created successfully")

        st.stop()  # 🚨 CRITICAL

    # ---------------- LOGIN ----------------
    if menu == "Login":
        st.title("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid credentials")

        st.stop()  # 🚨 CRITICAL


# ----------------------------------
# AFTER LOGIN → DASHBOARD ONLY
# ----------------------------------
st.sidebar.success(f"👤 {st.session_state.user}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.rerun()

st.title("WR Tracker Dashboard")

# ----------------------------------
# LOAD DATA
# ----------------------------------
@st.cache_data
def load_data():
    file_path = "wr_tracker_full_dummy.xlsx"
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
        "Signed Date",
        "Start Date",
        "End Date",
        "Current Contract End Date",
        "Current PO End Date / Forecasted Date for PO Consumption",
    ]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


# ----------------------------------
# LOAD
# ----------------------------------
try:
    df = load_data()

    if "selected_wr" not in st.session_state:
        st.session_state.selected_wr = None

    # FILTERS
    st.sidebar.header("Filters")

    wr_list = sorted(df["WR Reference"].dropna().unique().tolist())
    selected_wr = st.sidebar.selectbox("Select WR", ["All"] + wr_list)

    if selected_wr != "All":
        opp_list = sorted(
            df[df["WR Reference"] == selected_wr]["Opp Name"]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        opp_list = sorted(df["Opp Name"].dropna().unique().tolist())

    selected_opp = st.sidebar.selectbox("Select Opp Name", ["All"] + opp_list)

    status_options = df["Status"].dropna().unique()
    status_filter = st.sidebar.multiselect("Status", status_options, default=status_options)

    # DETAILS PAGE
    if st.session_state.selected_wr is not None:
        row = st.session_state.selected_wr

        st.subheader(f"WR Details: {row['WR Reference']}")

        if st.button("Back"):
            st.session_state.selected_wr = None
            st.rerun()

        col1, col2 = st.columns(2)

        with col1:
            st.write("Project:", row["Transform / Project"])
            st.write("TCV:", row["TCV"])
            st.write("Start Date:", row["Start Date"])
            st.write("End Date:", row["End Date"])
            st.write("Risk:", row["Risk to Delivery"])
            st.write("Next Steps:", row["Next Steps"])

        with col2:
            st.write("IBM Owner:", row["IBM Owner"])
            st.write("KD Owner:", row["KD Programme level owner"])
            st.write("PM:", row["KD PM on PCR"])
            st.write("Contract End:", row["Current Contract End Date"])

        st.stop()

    # SUMMARY
    st.subheader("Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total WRs", len(df))
    col2.metric("Signed", df[df["Status"] == "Signed"].shape[0])
    col3.metric("Pending", df[df["Status"] != "Signed"].shape[0])
    col4.metric("On Hold", df[df["Status"] == "On Hold"].shape[0])

    # WR LIST
    st.subheader("WR List")

    if selected_wr == "All" and selected_opp == "All":
        st.info("Please select WR or Opp Name")
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
            for idx, row in filtered_df.iterrows():
                col1, col2 = st.columns([8, 2])

                col1.write(f"{row['WR Reference']} | {row['Opp Name']} | {row['Status']}")

                if col2.button("View", key=f"view_{idx}"):
                    st.session_state.selected_wr = row
                    st.rerun()

    st.markdown("---")

    # ALERTS
    st.subheader("Contract Alerts")

    today = pd.Timestamp.today()

    expiring = df[
        (df["Current Contract End Date"].notna())
        & (df["Current Contract End Date"] >= today)
        & (df["Current Contract End Date"] <= today + pd.Timedelta(days=30))
    ]

    if not expiring.empty:
        st.dataframe(expiring[["WR Reference", "Opp Name", "Current Contract End Date"]])
    else:
        st.info("No contracts expiring")

    st.markdown("---")

    # TABLE
    st.subheader("WR Detailed Table")

    table_search = st.text_input("Search")

    table_df = df.copy()

    if table_search:
        table_df = table_df[
            table_df["WR Reference"].astype(str).str.contains(table_search, case=False)
            | table_df["Opp Name"].astype(str).str.contains(table_search, case=False)
        ]

    st.dataframe(table_df, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
