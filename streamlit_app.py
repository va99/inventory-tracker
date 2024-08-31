import pandas as pd
import altair as alt
import streamlit as st

# Set the title and favicon for the app
st.set_page_config(
    page_title="Referral Patient Tracker",
    page_icon=":hospital:"
)

# Updated TPA names dictionary with more entries
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
    "20": "Reliance General Insurance",
    "21": "Liberty General Insurance",
    "22": "Kotak Mahindra General Insurance",
    "23": "HDFC Life",
    "24": "SBI Life Insurance",
    "25": "Tata AIG",
    "26": "Bharti AXA",
    "27": "Go Digit Insurance",
    "28": "Future Generali",
    "29": "Aditya Birla Health Insurance",
    "30": "Edelweiss Tokio"
}

# Mock data for referral patients with more entries
data = {
    "id": list(range(1, 101)),
    "referral_id": [f"R00{i}" for i in range(1, 101)],
    "patient_name": [
        f"Patient {i}" for i in range(1, 101)
    ],
    "patient_age": [i % 60 + 20 for i in range(1, 101)],
    "patient_mobile": [
        f"99999999{i}" for i in range(1, 101)
    ],
    "tpa_partner": [
        f"{i % 30 + 1:02d}" for i in range(1, 101)
    ]
}

# Convert mock data into DataFrame
df = pd.DataFrame(data)

# Convert TPA codes to names in the DataFrame
def map_tpa_names(df):
    """Maps TPA codes to TPA names."""
    df['tpa_partner'] = df['tpa_partner'].map(tpa_names)
    return df

df = map_tpa_names(df)

# Initialize session state if not already present
if 'df' not in st.session_state:
    st.session_state.df = df
if 'total_patients' not in st.session_state:
    st.session_state.total_patients = 67
if 'total_revenue_inr' not in st.session_state:
    st.session_state.total_revenue_inr = 67 * 1299 * 83.5  # Initialize with the default revenue value

# Display editable table
edited_df = st.data_editor(
    st.session_state.df,
    disabled=["id"],  # Don't allow editing the 'id' column
    num_rows="dynamic",  # Allow appending/deleting rows
    key="referrals_table",
)

# Check if there are uncommitted changes
has_uncommitted_changes = any(len(v) for v in st.session_state.referrals_table.values())

# Function to handle mock data updates
def update_data():
    """Simulates updating the referral patient data."""
    changes = st.session_state.referrals_table
    df = st.session_state.df.copy()  # Work on a copy of the DataFrame

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

    st.session_state.df = df

    # Update patient count and revenue
    st.session_state.total_patients = 67
    st.session_state.total_revenue_inr = 67 * 1299 * 83.5  # Update with fixed patient count

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

# Summary
st.subheader("Summary")
st.markdown(f"### **Total Patients:** {st.session_state.total_patients}")
st.markdown(f"### **Revenue (INR):** ₹{st.session_state.total_revenue_inr:,.2f}")

st.subheader("Bed Occupancy")

# Visualization for bed occupancy
bed_occupancy_chart = alt.Chart(bed_occupancy_data).transform_fold(
    ['Occupied', 'Available'],
    as_=['Status', 'Count']
).mark_bar().encode(
    x=alt.X('Unit:O', title='Unit'),
    y=alt.Y('Count:Q', title='Number of Beds'),
    color='Status:N'
).properties(
    title="Bed Occupancy"
).interactive().configure_axis(
    labelAngle=0
)

st.altair_chart(bed_occupancy_chart, use_container_width=True)

# Sample data for TPA Partners with dynamic entries
tpa_data = st.session_state.df['tpa_partner'].value_counts().reset_index()
tpa_data.columns = ['TPA Partner', 'Count']

st.subheader("Best-Selling TPAs")

# Visualization for best-selling TPAs
tpa_chart = alt.Chart(tpa_data).mark_bar().encode(
    x=alt.X('Count:Q', title='Number of Referrals'),
    y=alt.Y('TPA Partner:N', sort='-x', title='TPA Partner'),
    color='TPA Partner:N'
).properties(
    title="Best-Selling TPAs"
).interactive().configure_axis(
    labelAngle=0
)

st.altair_chart(tpa_chart, use_container_width=True)