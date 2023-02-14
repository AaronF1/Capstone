import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
today = datetime.today()

# Read in the data
data = pd.read_csv('/Users/aaronfleishman/Desktop/IE_University/MBD/Courses/Captsone/Data_for_streamlit/clean_sample_data_capstone_project.csv')

# Create the main title for the dashboard
st.title("Radio Link Investment Decision Tool")

# create a graph which shows the number of concessions per owner and make it interactive so when an owner is selected, that same slection flows to the side filter owner


# Create the options on the left side of the dashboard
st.sidebar.title("Filter Options")

owner = st.sidebar.multiselect("Select Owner:", ["Select All"] + data["Owner"].unique().tolist())
municipality = st.sidebar.multiselect("Select Municipality:", ["Select All"] + data["Municipality"].unique().tolist())
frequency_ghz = st.sidebar.multiselect("Select Frequency GHZ:", ["Select All"] + data["Frequency GHZ"].unique().tolist())
frequency_ghz_rounded = st.sidebar.multiselect("Select Frequency GHZ Rounded:", ["Select All"] + data["Frequency GHZ rounded"].unique().tolist())
number_of_concession = st.sidebar.multiselect("Select Number of Concession:", ["Select All"] + data["Number of concession"].unique().tolist())
concession_in_municipality = st.sidebar.multiselect("Select Number of Concession in Municipality:", ["Select All"] + data["# of concession in municipality"].unique().tolist())
owner_in_municipality = st.sidebar.multiselect("Select Number of Owner in Municipality:", ["Select All"] + data["# of owner in municipality"].unique().tolist())
population = st.sidebar.multiselect("Select Population:", ["Select All"] + data["Population"].unique().tolist())

import streamlit as st

# Define default weights for each factor
default_weights = {
    'number_of_concession_owned': 0,
    'number_of_concession_opened_last_2_years': 0,
    'average_time_until_termination': 0,
    'average_days_since_last_opening': 0,
    'number_of_concession_owned_with_frequency_between_15_and_23': 0,
    'small_village': 0,
}

# Create the sidebar options

concession_weight = st.sidebar.slider('Concession Owned Weight', 0, 10, 0)
concession_opened_weight = st.sidebar.slider('Concession Opened Weight', 0, 10, 0)
avg_time_weight = st.sidebar.slider('Average Time until Termination Weight', 0, 10, 0)
avg_days_weight = st.sidebar.slider('Average Days since Last Opening Weight', 0, 10, 0)
frequency_weight = st.sidebar.slider('Frequency Weight', 0, 10, 0)
small_village_weight = st.sidebar.slider('Small Village Weight', 0, 10, 0)

# Create the range sliders for ALL HERE 

# Filter the data based on the selected options
filtered_data = data
if "Select All" not in owner:
    filtered_data = filtered_data[filtered_data["Owner"].isin(owner)]
if "Select All" not in municipality:
    filtered_data = filtered_data[filtered_data["Municipality"].isin(municipality)]
if "Select All" not in frequency_ghz_rounded:
    filtered_data = filtered_data[filtered_data["Frequency GHZ rounded"].isin(frequency_ghz_rounded)]
if "Select All" not in number_of_concession:
    filtered_data = filtered_data[filtered_data["Number of concession"].isin(number_of_concession)]
if "Select All" not in concession_in_municipality:
    filtered_data = filtered_data[filtered_data["# of concession in municipality"].isin(concession_in_municipality)]
if "Select All" not in owner_in_municipality:
    filtered_data = filtered_data[filtered_data["# of owner in municipality"].isin(owner_in_municipality)]
if "Select All" not in population:
    filtered_data = filtered_data[filtered_data["Population"].isin(population)]

filtered_data['days_since_last_opening'] = today - pd.to_datetime(filtered_data['Concession opening'])
filtered_data['days_since_last_opening'] = filtered_data['days_since_last_opening'].dt.days
filtered_data['Concession termination'] = pd.to_datetime(filtered_data['Concession termination'] , errors='coerce')
filtered_data['Concession termination'] = pd.to_datetime(filtered_data['Concession termination'])
today = datetime.today()
filtered_data['time_until_termination'] = pd.to_datetime(filtered_data['Concession termination']) - today
filtered_data['time_until_termination'] = filtered_data['time_until_termination'].dt.days
# for each owner I want to create a column that is equal to the number of concessions owned by that owner
filtered_data['number_of_concessions_owned'] = filtered_data.groupby('Owner')['Owner'].transform('count')
# I want to create a column for each owner that is equal to the number of concession opened in the last 730 days
filtered_data['number_of_concessions_opened_last_2_years'] = filtered_data.groupby('Owner')['days_since_last_opening'].transform(lambda x: (x < 730).sum())
# I want to create a column for each owner that is equal to the average number of days until concession termination for all the concessions owned by that owner
filtered_data['average_time_until_termination'] = filtered_data.groupby('Owner')['time_until_termination'].transform('mean')
# I want to create a column for each owner that is equal to the average number of days since last opening for all the concessions owned by that owner
filtered_data['average_days_since_last_opening'] = filtered_data.groupby('Owner')['days_since_last_opening'].transform('mean')
frequency_min = 15
frequency_max = 23
# for each owner create a column that is equal to the number of concessions owned by that owner that have a frequency between 15 and 23
filtered_data['number_of_concessions_owned_with_frequency_between_15_and_23'] = filtered_data.groupby('Owner')['Frequency GHZ rounded'].transform(lambda x: ((x >= frequency_min) & (x <= frequency_max)).sum())
# for each owner create a column call small village that counts the number of concessions that are catalogued as small villge in the Population column for each owner
filtered_data['small_village'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'small village').sum())
filtered_data['village'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'village').sum())
filtered_data['small city'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'small city').sum())
filtered_data['medium city'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'medium city').sum())
filtered_data['large city'] = filtered_data.groupby('Owner')['Population'].transform(lambda x: (x == 'large city').sum())


filtered_data2 = filtered_data.groupby('Owner').mean()
# drop the columns that are not needed
filtered_data2 = filtered_data2.drop(['Frequency GHZ rounded', 'days_since_last_opening', 'time_until_termination'], axis=1)

filtered_data_ranking = pd.DataFrame()

# create a column in filtered_data_ranking that is equal to the index of filtered_data2
filtered_data_ranking['Owner'] = filtered_data2.index
# create a rank NBR concession where the owner with the highest score is ranked 1 and the owner with the lowest score is ranked 3
filtered_data_ranking['rank_nbr_concession'] = filtered_data2['number_of_concessions_owned'].rank(ascending=False).values
# create a rank number_of_concessions_opened_last_2_years where the owner with the lowest score is ranked 1 and the owner with the higest score is ranked 3
filtered_data_ranking['rank_number_of_concessions_opened_last_2_years'] = filtered_data2['number_of_concessions_opened_last_2_years'].rank(ascending=True).values
# create a rank average_time_until_termination where the owner with the lowest score is ranked 1 and the owner with the higest score is ranked 3
filtered_data_ranking['rank_average_time_until_termination'] = filtered_data2['average_time_until_termination'].rank(ascending=True).values
# create a rank average_days_since_last_opening where the owner with the highest score is ranked 1 and the owner with the lowest score is ranked 3
filtered_data_ranking['rank_average_days_since_last_opening'] = filtered_data2['average_days_since_last_opening'].rank(ascending=False).values
# create a rank number_of_concessions_owned_with_frequency_between_15_and_23 where the owner with the highest score is ranked 1 and the owner with the lowest score is ranked 3
filtered_data_ranking['rank_number_of_concessions_owned_with_frequency_between_15_and_23'] = filtered_data2['number_of_concessions_owned_with_frequency_between_15_and_23'].rank(ascending=False).values
# create a rank small_village where the owner with the highest score is ranked 1 and the owner with the lowest score is ranked 3
filtered_data_ranking['rank_small_village'] = filtered_data2['small_village'].rank(ascending=False).values

filtered_data = filtered_data.merge(filtered_data_ranking, on="Owner", how='left')

# Define the investment score calculation
def investment_score(row, concession_weight, concession_opened_weight, avg_time_weight, avg_days_weight, frequency_weight, small_village_weight):
    concession_owned = row['rank_nbr_concession'] * concession_weight
    concession_opened = row['rank_number_of_concessions_opened_last_2_years'] * concession_opened_weight
    avg_time = row['rank_average_time_until_termination'] * avg_time_weight
    avg_days = row['rank_average_days_since_last_opening'] * avg_days_weight
    frequency = row['rank_number_of_concessions_owned_with_frequency_between_15_and_23'] * frequency_weight
    small_village = row['rank_small_village'] * small_village_weight
    
    return concession_owned + concession_opened + avg_time + avg_days + frequency + small_village

# Apply the investment score calculation and sort the data
filtered_data['investment_score'] = filtered_data.apply(lambda row: investment_score(row, concession_weight, concession_opened_weight, avg_time_weight, avg_days_weight, frequency_weight, small_village_weight), axis=1)
filtered_data.sort_values(by='investment_score', ascending=True, inplace=True)


# Create the table with the filtered data
st.dataframe(filtered_data)

# Add chart for number of concessions per owner
st.header("Number of Concessions per Owner")
concessions_per_owner = filtered_data.groupby('Owner').size().reset_index(name='counts')
fig = px.bar(concessions_per_owner, x='Owner', y='counts', color='counts')
st.plotly_chart(fig)



import folium
from folium.plugins import MarkerCluster

# Create the map 
map = folium.Map(location=[40.416775, -3.703790], zoom_start=5)

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

