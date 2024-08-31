import pandas as pd
import altair as alt
import streamlit as st
from collections import defaultdict

# Set the title and favicon for the app
st.set_page_config(
    page_title="Referral Patient Tracker",
    page_icon=":hospital:"
)

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

# Mock data for referral patients
data = {
    "id": [1, 2, 3, 4, 5],
    "referral_id": ["R001", "R002", "R003", "R004", "R005"],
    "patient_name": ["John Doe", "Jane Smith", "Alice Brown", "Bob Johnson", "Carol White"],
    "patient_age": [45, 34, 29, 52, 41],
    "patient_mobile": ["9876543210", "8765432109", "7654321098", "6543210987", "5432109876"],
    "tpa_partner": ["Medi Assist", "Paramount Health Services", "FHPL (Family Health Plan Limited)", "Health India TPA", "Star Health"]
}

# Convert mock data into DataFrame
df = pd.DataFrame(data)

# Convert TPA codes to names in the DataFrame
def map_tpa_names(df):
    """Maps TPA codes to TPA names."""
    df['tpa_partner'] = df['tpa_partner'].map(tpa_names)
    return df

df = map_tpa_names(df)

# Display editable table
edited_df = st.data_editor(
    df,
    disabled=["id"],  # Don't allow editing the 'id' column
    num_rows="dynamic",  # Allow appending/deleting rows
    key="referrals_table",
)

# Check if there are uncommitted changes
has_uncommitted_changes = any(len(v) for v in st.session_state.referrals_table.values())

# Function to handle mock data updates (no actual database involved)
def update_data():
    """Simulates updating the referral patient data."""
    changes = st.session_state.referrals_table
    if changes["edited_rows"]:
        deltas = changes["edited_rows"]
        for i, delta in deltas.items():
            row_dict = df.iloc[i].to_dict()
            row_dict.update(delta)
            df.iloc[i] = row_dict

    if changes["added_rows"]:
        new_rows = pd.DataFrame(changes["added_rows"])
        df = pd.concat([df, new_rows], ignore_index=True)

    if changes["deleted_rows"]:
        df.drop(index=changes["deleted_rows"], inplace=True)
        df.reset_index(drop=True, inplace=True)

    st.session_state.referrals_table = df

st.button(
    "Commit changes",
    type="primary",
    disabled=not has_uncommitted_changes,
    on_click=update_data
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