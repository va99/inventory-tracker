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

    DB_FILENAME = Path(__file__).parent / "patient_tracker.db"
    db_already_exists = DB_FILENAME.exists()

    conn = sqlite3.connect(DB_FILENAME)
    db_was_just_created = not db_already_exists

    return conn, db_was_just_created

def initialize_data(conn):
    """Initializes the referral patient tracker table with some data."""
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS patient_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tpa_name TEXT,
            price REAL,
            bed_units_used INTEGER,
            bed_units_available INTEGER,
            cost_price REAL,
            reorder_point INTEGER,
            description TEXT
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO patient_tracker
            (tpa_name, price, bed_units_used, bed_units_available, cost_price, reorder_point, description)
        VALUES
            -- TPAs
            ('TPA A', 15000, 115, 15, 8000, 16, 'Third Party Administrator A'),
            ('TPA B', 20000, 93, 8, 12000, 10, 'Third Party Administrator B'),
            ('TPA C', 25000, 12, 18, 15000, 8, 'Third Party Administrator C'),
            ('TPA D', 27500, 11, 14, 18000, 5, 'Third Party Administrator D'),
            ('TPA E', 22500, 11, 9, 13000, 5, 'Third Party Administrator E'),

            -- Miscellaneous
            ('TPA F', 20000, 34, 16, 10000, 10, 'Third Party Administrator F'),
            ('TPA G', 15000, 6, 19, 8000, 15, 'Third Party Administrator G'),
            ('TPA H', 22500, 3, 12, 13000, 8, 'Third Party Administrator H'),
            ('TPA I', 25000, 8, 8, 15000, 5, 'Third Party Administrator I'),
            ('TPA J', 17500, 5, 10, 10000, 8, 'Third Party Administrator J')
        """
    )
    conn.commit()

def load_data(conn):
    """Loads the referral patient data from the database."""
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM patient_tracker")
        data = cursor.fetchall()
    except:
        return None

    df = pd.DataFrame(
        data,
        columns=[
            "id",
            "tpa_name",
            "price",
            "bed_units_used",
            "bed_units_available",
            "cost_price",
            "reorder_point",
            "description",
        ],
    )

    return df

def update_data(conn, df, changes):
    """Updates the referral patient data in the database."""
    cursor = conn.cursor()

    if changes["edited_rows"]:
        deltas = st.session_state.patient_tracker_table["edited_rows"]
        rows = []

        for i, delta in deltas.items():
            row_dict = df.iloc[i].to_dict()
            row_dict.update(delta)
            rows.append(row_dict)

        cursor.executemany(
            """
            UPDATE patient_tracker
            SET
                tpa_name = :tpa_name,
                price = :price,
                bed_units_used = :bed_units_used,
                bed_units_available = :bed_units_available,
                cost_price = :cost_price,
                reorder_point = :reorder_point,
                description = :description
            WHERE id = :id
            """,
            rows,
        )

    if changes["added_rows"]:
        cursor.executemany(
            """
            INSERT INTO patient_tracker
                (id, tpa_name, price, bed_units_used, bed_units_available, cost_price, reorder_point, description)
            VALUES
                (:id, :tpa_name, :price, :bed_units_used, :bed_units_available, :cost_price, :reorder_point, :description)
            """,
            (defaultdict(lambda: None, row) for row in changes["added_rows"]),
        )

    if changes["deleted_rows"]:
        cursor.executemany(
            "DELETE FROM patient_tracker WHERE id = :id",
            ({"id": int(df.loc[i, "id"])} for i in changes["deleted_rows"]),
        )

    conn.commit()

# -----------------------------------------------------------------------------
# Draw the actual page, starting with the referral patient table.

# Set the title that appears at the top of the page.
"""
# :hospital: Referral Patient Tracker

**Welcome to the Referral Patient Tracker!**
This page reads and writes directly from/to our patient tracker database.
"""

st.info(
    """
    Use the table below to add, remove, and edit TPAs.
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
        # Show currency symbol before price columns.
        "price": st.column_config.NumberColumn(format="₹%.2f"),
        "cost_price": st.column_config.NumberColumn(format="₹%.2f"),
    },
    key="patient_tracker_table",
)

has_uncommitted_changes = any(len(v) for v in st.session_state.patient_tracker_table.values())

st.button(
    "Commit changes",
    type="primary",
    disabled=not has_uncommitted_changes,
    # Update data in database
    on_click=update_data,
    args=(conn, df, st.session_state.patient_tracker_table),
)

# -----------------------------------------------------------------------------
# Now some cool charts

# Add some space
""
""
""

st.subheader("Bed Units Available", divider="red")

need_to_reorder = df[df["bed_units_available"] < df["reorder_point"]].loc[:, "tpa_name"]

if len(need_to_reorder) > 0:
    items = "\n".join(f"* {name}" for name in need_to_reorder)

    st.error(f"We're running dangerously low on the following TPAs:\n {items}")

""
""

st.altair_chart(
    # Layer 1: Bar chart.
    alt.Chart(df)
    .mark_bar(
        orient="horizontal",
    )
    .encode(
        x="bed_units_available",
        y="tpa_name",
    )
    # Layer 2: Chart showing the reorder point.
    + alt.Chart(df)
    .mark_point(
        shape="diamond",
        filled=True,
        size=50,
        color="salmon",
        opacity=1,
    )
    .encode(
        x="reorder_point",
        y="tpa_name",
    ),
    use_container_width=True,
)

st.caption("NOTE: The :diamonds: location shows the reorder point.")

""
""
""

# -----------------------------------------------------------------------------

st.subheader("Top Empanelled TPAs", divider="orange")

""
""

st.altair_chart(
    alt.Chart(df)
    .mark_bar(orient="horizontal")
    .encode(
        x="bed_units_used",
        y=alt.Y("tpa_name").sort("-x"),
    ),
    use_container_width=True,
)