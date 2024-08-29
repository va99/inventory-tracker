import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sample data for referrals
referrals_data = {
    'Referral ID': [1, 2, 3, 4, 5],
    'Patient Name': ['John Doe', 'Jane Smith', 'Sam Wilson', 'Anna Johnson', 'Tom Brown'],
    'Age': [34, 29, 45, 50, 62],
    'Mobile Number': ['123-456-7890', '987-654-3210', '555-555-5555', '666-666-6666', '777-777-7777'],
    'TPA Partner': ['TPA1', 'TPA2', 'TPA1', 'TPA3', 'TPA2']
}
referrals_df = pd.DataFrame(referrals_data)

# Sample data for bed occupancy
bed_occupancy_data = {
    'Ward': ['Ward A', 'Ward B', 'Ward C'],
    'Total Beds': [50, 30, 20],
    'Occupied Beds': [20, 15, 10]
}
bed_occupancy_df = pd.DataFrame(bed_occupancy_data)

# Sample data for best-selling TPA
tpa_data = referrals_df['TPA Partner'].value_counts()

# Streamlit app
st.title('MedLeads Referral Management Admin Dashboard')

# Referral Management Table
st.subheader('Referrals Table')
st.dataframe(referrals_df)

# Bed Occupancy Visualization
st.subheader('Bed Occupancy Visualization')
fig, ax = plt.subplots()
bed_occupancy_df.set_index('Ward')[['Total Beds', 'Occupied Beds']].plot(kind='bar', ax=ax)
ax.set_ylabel('Number of Beds')
ax.set_title('Bed Occupancy by Ward')
st.pyplot(fig)

# Best Selling TPA Visualization
st.subheader('Best Selling TPA')
fig, ax = plt.subplots()
tpa_data.plot(kind='pie', autopct='%1.1f%%', ax=ax)
ax.set_ylabel('')
ax.set_title('Best Selling TPA')
st.pyplot(fig)