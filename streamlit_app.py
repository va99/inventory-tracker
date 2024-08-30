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
            ('R005', 'Carol White', 41, '5432109876', 'TPA2')
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

def add_hospital_to_db(conn, name, description, city, state, total_beds, tpas):
    """Adds new hospital details to the database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_name TEXT,
            description TEXT,
            city TEXT,
            state TEXT,
            total_beds INTEGER,
            empanelled_tpas TEXT
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO hospitals (hospital_name, description, city, state, total_beds, empanelled_tpas)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, description, city, state, total_beds, ", ".join(tpas))
    )
    conn.commit()

# -----------------------------------------------------------------------------
# Define TPA options (Mock Data from Doctor App)
tpa_options = ["TPA1", "TPA2", "TPA3"]

# Form for adding hospital information
if 'form_submitted' not in st.session_state:
    st.session_state['form_submitted'] = False

if not st.session_state['form_submitted']:
    st.sidebar.header("Add New Hospital Information")

    with st.sidebar.form(key='hospital_form'):
        st.header("Hospital Information Form")
        hospital_name = st.text_input("Hospital Name")
        description = st.text_area("A brief description", max_chars=300)
        city = st.text_input("City")
        state = st.text_input("State")
        total_beds = st.number_input("Total Bed Units", min_value=1)
        
        # Multi-selection list for Empanelled TPA
        empanelled_tpas = st.multiselect("Empanelled TPA", options=tpa_options)
        
        submit_button = st.form_submit_button(label='Submit')
        
        if submit_button:
            try:
                add_hospital_to_db(conn, hospital_name, description, city, state, total_beds, empanelled_tpas)
                st.session_state['form_submitted'] = True
                st.experimental_rerun()  # Refresh the app to show the new screen
            except Exception as e:
                st.error(f"Error occurred while submitting the form: {e}")

else:
    # Display a message on the new screen
    st.title(f"HELLO {hospital_name}")
    st.write("Thank you for submitting your details. The hospital has been added.")
    st.write("You can now navigate to the referral tracking screen from the sidebar.")

# -----------------------------------------------------------------------------
# Home screen content if form has been submitted
if st.session_state['form_submitted']:
    st.title(f"HELLO {hospital_name}")

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
        x=alt.X('Count', title='Number of Referrals'),
        y=alt.Y('TPA Partner', sort='-x', title='TPA Partner'),
        color='TPA Partner'
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