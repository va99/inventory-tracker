import pandas as pd
import altair as alt
import streamlit as st
import sqlite3
from pathlib import Path

# Set the title and favicon for the app
st.set_page_config(
    page_title="Referral Patient Tracker",
    page_icon=":hospital:"
)

# Connect to SQLite database
def connect_db():
    """Connects to the SQLite database."""
    DB_FILENAME = Path(__file__).parent / "referral_patient_tracker.db"
    db_already_exists = DB_FILENAME.exists()
    conn = sqlite3.connect(DB_FILENAME)
    db_was_just_created = not db_already_exists
    return conn, db_was_just_created

# Initialize referral patient tracker table with mock data
def initialize_data(conn):
    """Initializes the referral patient tracker table with some data."""
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referral_id TEXT,
            patient_name TEXT,
            patient_age INTEGER,
            patient_mobile TEXT,
            tpa_partner TEXT
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO referrals
            (referral_id, patient_name, patient_age, patient_mobile, tpa_partner)
        VALUES
            ('R001', 'John Doe', 45, '9876543210', 'Medi Assist'),
            ('R002', 'Jane Smith', 34, '8765432109', 'Paramount Health Services'),
            ('R003', 'Alice Brown', 29, '7654321098', 'FHPL (Family Health Plan Limited)'),
            ('R004', 'Bob Johnson', 52, '6543210987', 'Health India TPA'),
            ('R005', 'Carol White', 41, '5432109876', 'Star Health')
        """
    )
    conn.commit()

# Load referral patient data from the database
def load_data(conn):
    """Loads the referral patient data from the database."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM referrals")
        data = cursor.fetchall()
    except:
        return None

    df = pd.DataFrame(
        data,
        columns=[
            "id",
            "referral_id",
            "patient_name",
            "patient_age",
            "patient_mobile",
            "tpa_partner",
        ],
    )
    return df

# Update referral patient data in the database
def update_data(conn, df, changes):
    """Updates the referral patient data in the database."""
    cursor = conn.cursor()

    if changes["edited_rows"]:
        deltas = st.session_state.referrals_table["edited_rows"]
        rows = []
        for i, delta in deltas.items():
            row_dict = df.iloc[i].to_dict()
            row_dict.update(delta)
            rows.append(row_dict)

        cursor.executemany(
            """
            UPDATE referrals
            SET
                referral_id = :referral_id,
                patient_name = :patient_name,
                patient_age = :patient_age,
                patient_mobile = :patient_mobile,
                tpa_partner = :tpa_partner
            WHERE id = :id
            """,
            rows,
        )

    if changes["added_rows"]:
        cursor.executemany(
            """
            INSERT INTO referrals
                (id, referral_id, patient_name, patient_age, patient_mobile, tpa_partner)
            VALUES
                (:id, :referral_id, :patient_name, :patient_age, :patient_mobile, :tpa_partner)
            """,
            (defaultdict(lambda: None, row) for row in changes["added_rows"]),
        )

    if changes["deleted_rows"]:
        cursor.executemany(
            "DELETE FROM referrals WHERE id = :id",
            ({"id": int(df.loc[i, "id"])} for i in changes["deleted_rows"]),
        )

    conn.commit()

# TPA names dictionary
tpa_names = {
    "01": "Medi Assist",
    "02": "Paramount Health Services",
    "03": "FHPL (Family Health Plan Limited)",
    "04": "Health India TPA",
    "05": "Star Health",
    "06": "Apollo Munich",
    "07": "ICICI Lombard",
    "08": "UnitedHealthcare",
    "09": "Religare Health Insurance",
    "10": "HDFC ERGO",
    "11": "Max Bupa Health Insurance",
    "12": "SBI Health Insurance",
    "13": "New India Assurance",
    "14": "Oriental Insurance",
    "15": "National Insurance",
    "16": "United India Insurance",
    "17": "IFFCO Tokio",
    "18": "Cholamandalam MS General Insurance",
    "19": "Bajaj Allianz",
    "20": "Reliance General Insurance"
}

# Convert TPA codes to names in the DataFrame
def map_tpa_names(df):
    """Maps TPA codes to TPA names."""
    df['tpa_partner'] = df['tpa_partner'].map(tpa_names)
    return df

# Initialize Streamlit app
conn, db_was_just_created = connect_db()
if db_was_just_created:
    initialize_data(conn)
    st.toast("Database initialized with some sample data.")

df = load_data(conn)
df = map_tpa_names(df)

# Display editable table
edited_df = st.data_editor(
    df,
    disabled=["id"],  # Don't allow editing the 'id' column
    num_rows="dynamic",  # Allow appending/deleting rows
    key="referrals_table",
)

has_uncommitted_changes = any(len(v) for v in st.session_state.referrals_table.values())

st.button(
    "Commit changes",
    type="primary",
    disabled=not has_uncommitted_changes,
    on_click=update_data,
    args=(conn, df, st.session_state.referrals_table),
)

# Sample data for bed occupancy
bed_occupancy_data = pd.DataFrame({
    'Unit': ['ICU', 'General Ward', 'Emergency', 'Maternity', 'Pediatrics'],
    'Occupied': [10, 30, 5, 8, 15],
    'Total': [15, 50, 10, 12, 20]
})

bed_occupancy_data['Available'] = bed_occupancy_data['Total'] - bed_occupancy_data['Occupied']

st.subheader("Bed Occupancy")

st.altair_chart(
    alt.Chart(bed_occupancy_data)
    .mark_bar()
    .encode(
        x=alt.X('Unit:O', title='Unit'),
        y=alt.Y('Available:Q', title='Available Beds'),
        color='Unit:N'
    )
    .properties(
        title="Bed Occupancy"
    )
    .interactive()
    .configure_axis(
        labelAngle=0
    ),
    use_container_width=True
)

# Sample data for TPA Partners
tpa_data = df['tpa_partner'].value_counts().reset_index()
tpa_data.columns = ['TPA Partner', 'Count']

st.subheader("Best-Selling TPAs")

st.altair_chart(
    alt.Chart(tpa_data)
    .mark_bar()
    .encode(
        x=alt.X('Count:Q', title='Number of Referrals'),
        y=alt.Y('TPA Partner:N', sort='-x', title='TPA Partner'),
        color='TPA Partner:N'
    )
    .properties(
        title="Best-Selling TPAs"
    )
    .interactive()
    .configure_axis(
        labelAngle=0
    ),
    use_container_width=True
)