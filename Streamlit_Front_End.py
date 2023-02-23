import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
today = datetime.today()
st.set_option('deprecation.showfileUploaderEncoding', False)
import folium
from folium.plugins import MarkerCluster
import io

# Read in the data
data = pd.read_csv('clean_sample_data_capstone_project.csv')

# Set up the file paths to your images
img_path1 = 'Lineox Logo.png'
img_path2 = 'IE_HST_Logo.png'

# Display the images side by side
col1, col2 = st.beta_columns(2)
with col1:
    st.image(img_path1, use_column_width=True)
with col2:
    st.image(img_path2, use_column_width=True)


# Create the main title for the dashboard
st.title("Radio Link Investment Decision Tool")

# Create the options on the left side of the dashboard
st.sidebar.title("Filter Options")
owner = st.sidebar.multiselect("Select Owner:", ["Select All"] + sorted(data["Owner"].unique().tolist()), default=["Select All"])
municipality = st.sidebar.multiselect("Select Municipality:", ["Select All"] + sorted(data["Municipality"].unique().tolist()), default=["Select All"])
frequencies = sorted(data["Frequency GHZ rounded"].unique())
default_frequencies = [13, 15, 18, 22, 23, 24]
selected_frequencies = st.sidebar.multiselect("Select Frequency GHZ Rounded:", frequencies, default=default_frequencies)
concession_min, concession_max = st.sidebar.slider(
    "Select Number of Concessions Range:",
    min(data["Number of concession"]),
    max(data["Number of concession"]),
    (min(data["Number of concession"]), max(data["Number of concession"])),
    step=1,
)
population = st.sidebar.multiselect("Select Population:", ["Select All"] + sorted(data["Population"].unique().tolist()), default=["Select All"])

# Create the sidebar options
avg_time_weight = st.sidebar.slider('Average Time until Termination Weight', 0, 10, 0)
avg_days_weight = st.sidebar.slider('Average Days since Last Opening Weight', 0, 10, 0)
frequency_weight = st.sidebar.slider('Frequency Weight', 0, 10, 0)

# Filter the data based on the selected options
filtered_data = data
if "Select All" not in owner:
    filtered_data = filtered_data[filtered_data["Owner"].isin(owner)]
if "Select All" not in municipality:
    filtered_data = filtered_data[filtered_data["Municipality"].isin(municipality)]
filtered_data = filtered_data[filtered_data['Frequency GHZ rounded'].isin(selected_frequencies)]
filtered_data = filtered_data[(filtered_data['Number of concession'] >= concession_min) & (filtered_data['Number of concession'] <= concession_max)]
if "Select All" not in population:
    filtered_data = filtered_data[filtered_data["Population"].isin(population)]

filtered_data['days_since_last_opening'] = today - pd.to_datetime(filtered_data['Concession opening'])
filtered_data['days_since_last_opening'] = filtered_data['days_since_last_opening'].dt.days
filtered_data['Concession termination'] = pd.to_datetime(filtered_data['Concession termination'] , errors='coerce')
filtered_data['Concession termination'] = pd.to_datetime(filtered_data['Concession termination'])
today = datetime.today()
filtered_data['time_until_termination'] = pd.to_datetime(filtered_data['Concession termination']) - today
filtered_data['time_until_termination'] = filtered_data['time_until_termination'].dt.days
filtered_data['number_of_concessions_opened_last_2_years'] = filtered_data.groupby('Owner')['days_since_last_opening'].transform(lambda x: (x < 730).sum())
filtered_data['average_time_until_termination'] = filtered_data.groupby('Owner')['time_until_termination'].transform('mean')
filtered_data['average_days_since_last_opening'] = filtered_data.groupby('Owner')['days_since_last_opening'].transform('mean')
filtered_data['number_of_concessions_within_frequency_range'] = filtered_data.groupby('Owner')['Frequency GHZ rounded'].transform(lambda x: x.isin(selected_frequencies).sum())


filtered_data['percentage_of_concessions_within_frequency_range'] = (filtered_data['number_of_concessions_within_frequency_range'] / filtered_data['Number of concession'] * 100).round(2)

filtered_data['small_village'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'small village').sum())
filtered_data['village'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'village').sum())
filtered_data['small city'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'small city').sum())
filtered_data['medium city'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'medium city').sum())
filtered_data['large city'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'large city').sum())


filtered_data2 = filtered_data.groupby('Owner').mean()

df_ranking_normalised = pd.DataFrame()
df_ranking_normalised['Owner'] = filtered_data2.index
df_ranking_normalised['rank_average_time_until_termination'] = (filtered_data2['average_time_until_termination'].values-filtered_data2['average_time_until_termination'].min())/(filtered_data2['average_time_until_termination'].max()-filtered_data2['average_time_until_termination'].min())
df_ranking_normalised['rank_average_days_since_last_opening'] = (filtered_data2['average_days_since_last_opening'].values-filtered_data2['average_days_since_last_opening'].min())/(filtered_data2['average_days_since_last_opening'].max()-filtered_data2['average_days_since_last_opening'].min())
if (filtered_data2['percentage_of_concessions_within_frequency_range'].max()-filtered_data2['percentage_of_concessions_within_frequency_range'].min()) == 0:
    df_ranking_normalised['rank_percentage_of_concessions_within_frequency_range'] = 1
else:
    df_ranking_normalised['rank_percentage_of_concessions_within_frequency_range'] = (filtered_data2['percentage_of_concessions_within_frequency_range'].values-filtered_data2['percentage_of_concessions_within_frequency_range'].min())/(filtered_data2['percentage_of_concessions_within_frequency_range'].max()-filtered_data2['percentage_of_concessions_within_frequency_range'].min())
filtered_data = filtered_data.merge(df_ranking_normalised, on="Owner", how='left')

# Define the investment score calculation
def investment_score(row, avg_time_weight, avg_days_weight, frequency_weight):
    avg_time = row['rank_average_time_until_termination'] * avg_time_weight
    avg_days = row['rank_average_days_since_last_opening'] * avg_days_weight
    frequency = row['rank_percentage_of_concessions_within_frequency_range'] * frequency_weight
    
    return -avg_time + avg_days + frequency

# Apply the investment score calculation and sort the data
filtered_data['investment_score'] = filtered_data.apply(lambda row: investment_score(row, avg_time_weight, avg_days_weight, frequency_weight), axis=1)
filtered_data.sort_values(by='investment_score', ascending=False, inplace=True)

# Create the table with the filtered data
st.dataframe(filtered_data[['Reference', 'Owner', 'Municipality', 'Frequency GHZ rounded', 'Number of concession', 'number_of_concessions_within_frequency_range', 'percentage_of_concessions_within_frequency_range', 'investment_score', 'rank_average_time_until_termination', 'rank_average_days_since_last_opening', 'rank_percentage_of_concessions_within_frequency_range']])

def download_excel(data):
    output = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        output.to_excel(writer, index=False)
    excel_buffer.seek(0)
    return excel_buffer

if st.button('Click Here to Download the Filtered Data as an Excel File'):
    excel_buffer = download_excel(filtered_data)
    st.download_button(
        label="Click Here to Confirm Download of Filtered Data as an Excel File",
        data=excel_buffer,
        file_name="filtered_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# Add chart for number of concessions per owner
st.header("Number of Concessions per Owner Within Selected Concession Range")
concessions_per_owner = filtered_data.groupby('Owner').size().reset_index(name='counts')
fig = px.bar(concessions_per_owner, x='Owner', y='counts', color='counts')
st.plotly_chart(fig)

st.header("Map Showing Midpoint of Muncipalities with Concessions Within Selected Concession Range")
# Create the map 
map = folium.Map(location=[40.416775, -3.703790], zoom_start=5)

# go through filtered_data and only select the rows where longitude and latitude are not null
filtered_data = filtered_data[filtered_data['Longitude'].notna()]

# Create a marker cluster
marker_cluster = MarkerCluster().add_to(map)

# Iterate over the rows of the DataFrame 
for index, row in filtered_data.iterrows():
    # Get the municipality name
    municipality = row['Municipality']
    # Get the number of rows in data_filtered_data2 for that municipality
    num_rows = len(filtered_data[filtered_data['Municipality'] == municipality])
    # Get the coordinates
    latitude = row['Latitude']
    longitude = row['Longitude']
    # Add a marker to the cluster
    folium.CircleMarker(location=[latitude, longitude], radius=num_rows, color='red', fill=True).add_to(marker_cluster)

# Display the map
st.write(map)
