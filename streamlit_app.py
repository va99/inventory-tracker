from collections import defaultdict
from pathlib import Path
import sqlite3

import streamlit as st
import altair as alt
import pandas as pd

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Referral Patient Tracker",
    page_icon=":hospital:",  # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

def connect_db():
    """Connects to the sqlite database."""

    DB_FILENAME = Path(__file__).parent / "referral_patient_tracker.db"
    db_already_exists = DB_FILENAME.exists()

    conn = sqlite3.connect(DB_FILENAME)
    db_was_just_created = not db_already_exists

    return conn, db_was_just_created

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
            ('R001', 'John Doe', 45, '9876543210', 'TPA1'),
            ('R002', 'Jane Smith', 34, '8765432109', 'TPA2'),
            ('R003', 'Alice Brown', 29, '7654321098', 'TPA3'),
            ('R004', 'Bob Johnson', 52, '6543210987', 'TPA1'),
            ('R005', 'Carol White', 41, '5432109876', 'TPA2'),
            ('R006', 'David Lee', 37, '4321098765', 'TPA3'),
            ('R007', 'Emily Davis', 26, '3210987654', 'TPA4'),
            ('R008', 'Frank Wilson', 55, '2109876543', 'TPA5'),
            ('R009', 'Grace Martinez', 30, '1098765432', 'TPA6'),
            ('R010', 'Henry Taylor', 48, '9876504321', 'TPA7'),
            ('R011', 'Ivy Anderson', 42, '8765432101', 'TPA8'),
            ('R012', 'Jack Thomas', 31, '7654321097', 'TPA9'),
            ('R013', 'Kara White', 39, '6543210986', 'TPA10'),
            ('R014', 'Leo Harris', 28, '5432109875', 'TPA11'),
            ('R015', 'Mia Clark', 49, '4321098764', 'TPA12'),
            ('R016', 'Noah Lewis', 27, '3210987653', 'TPA13'),
            ('R017', 'Olivia Walker', 33, '2109876542', 'TPA14'),
            ('R018', 'Paul Scott', 40, '1098765431', 'TPA15'),
            ('R019', 'Quinn Adams', 50, '9876543219', 'TPA16'),
            ('R020', 'Rachel Baker', 32, '8765432108', 'TPA17'),
            ('R021', 'Steve Nelson', 44, '7654321096', 'TPA18'),
            ('R022', 'Tina Carter', 38, '6543210985', 'TPA19'),
            ('R023', 'Ursula Mitchell', 25, '5432109874', 'TPA20'),
            ('R024', 'Victor Roberts', 43, '4321098763', 'TPA21'),
            ('R025', 'Wendy Gonzalez', 29, '3210987652', 'TPA22'),
            ('R026', 'Xander Turner', 47, '2109876541', 'TPA23'),
            ('R027', 'Yara Collins', 36, '1098765430', 'TPA24'),
            ('R028', 'Zane Stewart', 53, '9876543218', 'TPA25'),
            ('R029', 'Amy Cooper', 41, '8765432107', 'TPA26'),
            ('R030', 'Ben Simmons', 34, '7654321095', 'TPA27'),
            ('R031', 'Clara Gray', 46, '6543210984', 'TPA28')
        """
    )
    conn.commit()

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

# -----------------------------------------------------------------------------
# Draw the actual page, starting with the referrals table.

# Set the title that appears at the top of the page.
"""
# :hospital: Referral Patient Tracker

**Welcome to the Referral Patient Tracker!**
This page reads and writes directly from/to our referral patient database.
"""

st.info(
    """
    Use the table below to add, remove, and edit patient referrals.
    And don't forget to commit your changes when you're done.
    """
)

# Connect to database and create table if needed
conn, db_was_just_created = connect_db()

# Initialize data.
if db_was_just_created:
    initialize_data(conn)
    st.toast("Database initialized with some sample data.")

# Load data from database
df = load_data(conn)

# Display data with editable table
edited_df = st.data_editor(
    df,
    disabled=["id"],  # Don't allow editing the 'id' column.
    num_rows="dynamic",  # Allow appending/deleting rows.
    column_config={
        "patient_age": st.column_config.NumberColumn(),
        "patient_mobile": st.column_config.TextColumn(),
    },
    key="referrals_table",
)

has_uncommitted_changes = any(len(v) for v in st.session_state.referrals_table.values())

st.button(
    "Commit changes",
    type="primary",
    disabled=not has_uncommitted_changes,
    # Update data in database
    on_click=update_data,
    args=(conn, df, st.session_state.referrals_table),
)

# -----------------------------------------------------------------------------
# Visualization: Bed Occupancy

# Placeholder data for bed occupancy
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
        x=alt.X('Unit', title='Unit'),
        y=alt.Y('Available', title='Available Beds'),
        color='Unit'
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

# -----------------------------------------------------------------------------
# Visualization: Best-Selling TPAs

tpa_data = df['tpa_partner'].value_counts().reset_index()
tpa_data.columns = ['TPA Partner', 'Count']

st.subheader("Best-Selling TPAs")

st.altair_chart(
    alt.Chart(tpa_data)
    .mark_bar()
    .encode(
        x=alt.X('Count', title