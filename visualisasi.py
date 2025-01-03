import pandas as pd
import numpy as np
from PIL import Image
import streamlit as st
import altair as alt
from datetime import datetime
import plotly.express as px
from sodapy import Socrata


# Import the community data files.
df_communities = pd.read_csv("data_files/communities.csv")

# API access
# Website: https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2/data_preview

def call_data(start_date, end_date, crime_type, community):
    """Makes a call to the chicago crime API. """

    client = Socrata("data.cityofchicago.org", None)
    results = client.get("ijzp-q8t2",
                         select="id, case_number, block, primary_type, description, location_description, arrest, date, community_area, fbi_code,"
                                "year, latitude, longitude",
                         where=f"date > '{start_date}' AND date < '{end_date}' AND primary_type = '{crime_type}' AND community_area = '{community}'",
                         limit=250000,
                         order="date DESC")

    return results


def crime_names():
    """Returns a list of the available crimes to choose from."""

    keep_crimes = {'Primary Type': ['THEFT', 'ASSAULT', 'SEX OFFENSE', 'BURGLARY','MOTOR VEHICLE THEFT',
                                    'OFFENSE INVOLVING CHILDREN', 'CRIMINAL TRESPASS', 'ROBBERY',
                                    'CRIMINAL SEXUAL ASSAULT', 'STALKING', 'HOMICIDE', 'KIDNAPPING',
                                    'DOMESTIC VIOLENCE']}

    df_crime_type = pd.DataFrame(keep_crimes)

    return df_crime_type


def convert_community(chosen_community, df_communities):
    """Converts the chosen community to a number that can be called in the API."""

    community_row = df_communities[df_communities['Community'] == chosen_community]
    community_area_number = community_row.iloc[0]['Community Area']

    return community_area_number


@st.cache_data
def clean_crimes(crime_df, neighborhoods, crime, start_date= "2018-01-01", end_date="2024-01-01"):
    """Combines the crime, demographic and neightborhoods dataframe into one."""

    # Convert 'Date' column to date time
    crime_df['date'] = pd.to_datetime(crime_df['date'], format='mixed')

    # Apply filter to dataframe
    mask_1 = crime_df['date'] >= start_date
    mask_2 = crime_df['date'] < end_date

    crime_df = crime_df.loc[mask_1 & mask_2].sort_values(by='date')

    # Create columns with hour, day, month, year
    crime_df['hour'] = crime_df['date'].dt.hour
    crime_df['day'] = crime_df['date'].dt.day
    crime_df['month'] = crime_df['date'].dt.month
    crime_df['year'] = crime_df['date'].dt.year

    # Create a feature based on time of day
    conditions = [
        (crime_df['hour'] >= 0) & (crime_df['hour'] < 4),
        (crime_df['hour'] >= 4) & (crime_df['hour'] < 8),
        (crime_df['hour'] >= 8) & (crime_df['hour'] < 12),
        (crime_df['hour'] >= 12) & (crime_df['hour'] < 16),
        (crime_df['hour'] >= 16) & (crime_df['hour'] < 20),
        (crime_df['hour'] >= 20)
    ]

    values = ['12am to 4am', '4am to 8am', '8am to 12pm', '12pm to 4pm', '4pm to 8pm',
              '8pm to 12am']

    crime_df['Time of Day'] = np.select(conditions, values)

    # Filter for only the crime of interest.
    crime_df = crime_df.loc[crime_df['primary_type'] == crime]

    # Rename the column Community in the Commnities dataframe
    neighborhoods = neighborhoods.rename(columns={"Community Area": "community_area"})

    # Make the community_area a string in neightborhoods.
    neighborhoods['community_area'] = neighborhoods['community_area'].astype(str)

    # Add the communities to the dataframe.
    crime_df_1 = pd.merge(crime_df, neighborhoods, on='community_area', how='outer')

    # Remove NA columns where id = NaN.  This is from the discrepancy between the current date and the
    # chosen end date.
    crime_df_2 = crime_df_1.dropna(subset="id")

    # Obtain the total number of crimes
    crime_total = len(crime_df_2)

    return crime_df_2, crime_total

def plot_crime_time_series(df):
    """
    Plots a line chart of recorded crimes annually from the cleaned data.

    Args:
        df (pd.DataFrame): Cleaned crime data with 'year' column.

    Returns:
        alt.Chart: An Altair line chart.
    """
    # Group data by year and count crimes per year
    annual_crime_counts = df.groupby("month").size().reset_index(name="crime_count")

    # Create a line chart
    line_chart = (
        alt.Chart(annual_crime_counts)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:O", title="Month"),
            y=alt.Y("crime_count:Q", title="Number of Crimes"),
            tooltip=["month", "crime_count"]
        )
        .properties(width=400, height=300)
    )

    return line_chart

def plot_arrest_ratio(df):
    """
    Plots a bar chart showing the ratio of crimes resulting in an arrest.

    Args:
        df (pd.DataFrame): Cleaned crime data with 'arrest' column.

    Returns:
        alt.Chart: An Altair bar chart.
    """
    # Calculate the total and arrested counts
    arrest_counts = df['arrest'].value_counts().reset_index()
    arrest_counts.columns = ['arrest', 'count']

    # Calculate the ratio
    arrest_counts['ratio'] = arrest_counts['count'] / arrest_counts['count'].sum()
    arrest_counts['percentage'] = (arrest_counts['ratio'] * 100).round(2)

    # Bar chart
    bars = (
        alt.Chart(arrest_counts)
        .mark_bar()
        .encode(
            x=alt.X("arrest:N", title="Arrest Made"),
            y=alt.Y("count:Q", title="Counts"),
            color=alt.Color("arrest:N", title="Arrest Made"),
            tooltip=["arrest", "count", "percentage"]
        )
    )

    # Text labels for percentages
    text = (
        alt.Chart(arrest_counts)
        .mark_text(dy=-10, fontSize=14, color="black")
        .encode(
            x=alt.X("arrest:N"),
            y=alt.Y("ratio:Q"),
            text=alt.Text("percentage:Q", format=".1f")
        )
    )

    chart = (bars + text).properties(width=400, height=300)
    return chart

def plot_community_time_day(df):
    """Determines and plots the number of crimes in the community by the time of day."""

    # Order for the x_axis
    order = ['12am to 4am', '4am to 8am', '8am to 12pm', '12pm to 4pm', '4pm to 8pm', '8pm to 12am']

    # Plot the crimes by time of day
    fig = px.histogram(df, x='Time of Day', category_orders={'Time of Day': order})
    # Set the pie chart size.
    fig.update_layout(width=400, height=350)

    return fig

def location_description(df):
    """Plots a histogram of the location of most likely occurrence."""

    value_counts = df['location_description'].value_counts()

    # Does a breakdown of occurrence for each crime.
    fig = px.pie(df, values=value_counts.values, names=value_counts.index)
    fig.update_layout(width=450, height=400)
    # Removes the labels
    fig.update_traces(textposition='inside', textinfo='none')

    return fig

def crime_map(df):
    """Plots a map of the different crime locations"""

    latitude = df['latitude']
    longitude = df['longitude']
    coordinates_data = {'latitude': latitude, 'longitude': longitude}
    df_coordinates = pd.DataFrame(coordinates_data)

    df_coordinates['latitude'] = df_coordinates['latitude'].astype(float)
    df_coordinates['longitude'] = df_coordinates['longitude'].astype(float)

    # drop any NaN values
    df_coordinates = df_coordinates.dropna()

    color = '#4dffff'
    size = 25

    return df_coordinates, color, size



st.set_page_config(
    page_title="Neighborhood Watch Statistics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

alt.themes.enable("dark")

# Provide initial start and end times for the date inputs.
start_init = "2023-01-01"
end_init = "2024-01-01"

# Convert to datetime.
start_init_1 = pd.to_datetime(start_init)
end_init_1 = pd.to_datetime(end_init)

# Obtain the crime names
primary_crime_names = crime_names()

# Streamlit application UI code below.
# Add a sidebar
with st.sidebar:
    begin_date = st.date_input('Begin Date', start_init_1)
    ending_date = st.date_input('End Date', end_init_1)
    st.text("")
    community_chosen = st.selectbox('Community', options=df_communities['Community'].unique())
    crime_type = st.selectbox('Crime Type', options=primary_crime_names['Primary Type'])
    st.text("")
    data_button = st.button("Update Data")
    st.markdown(
        """
        ### Key Features:
        - View crime statistics by neighborhood, crime type, and time range.
        - Interactive visualizations for time of day and location analysis.
        - Map-based crime hotspot identification.
        """
    )
    

community_chosen_1 = convert_community(community_chosen, df_communities)

# Query the current date
starting_date = "2018-01-01T00:00:00.000"
current_date = datetime.now()
end_date = current_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
end_date_2 = f"{end_date}"


# Obtain the data from the chicago crime API.
results = call_data(starting_date, end_date_2, crime_type, community_chosen_1)
df_crime_1 = pd.DataFrame.from_records(results)

# Convert the datetime to a string
begin_date_1 = begin_date.strftime('%Y-%m-%d')
ending_date_1 = ending_date.strftime('%Y-%m-%d')

# Dashboard Information
st.title('Chicago Neighborhood Crime Dashboard')
st.write('This dashboard provides a comprehensive view of crime data visualization across Chicago neighborhoods in 2023.')

# Create a placeholder for the crime count.
st.subheader(f'Total Reported {crime_type.title()}:')
crimecount_placeholder = st.empty()

# Content on the main colunn.
st.subheader('Table of Data')
# Placeholder for dataframe table
data_placeholder = st.empty()
# Clean the data and create the Time of Day column
new_df, crime_tot = clean_crimes(df_crime_1, df_communities, crime_type, begin_date_1, ending_date_1)
if 'new_df_key_1' not in st.session_state:
    # Add the new dataframe to the current session state.
    st.session_state['new_df_key_1'] = new_df
    data_placeholder = st.empty()
    data_placeholder.dataframe(new_df)
    # Count of Total Crimes and update the value
    crimecount_placeholder.subheader(crime_tot)

st.text("")
st.text("")

# Rows to hold the pie and bar charts.
col1, col2 = st.columns(2)
with col1:
    # Line Plot
    st.subheader('Monthly Crimes Trends')
    lineplot_placeholder = st.empty()
    fig = plot_crime_time_series(st.session_state['new_df_key_1'])
    lineplot_placeholder.altair_chart(fig)

with col2:
    # Bar Chart
    st.subheader('Arrest Ratio')
    bar_chart_placeholder = st.empty()
    fig = plot_arrest_ratio(st.session_state['new_df_key_1'])
    bar_chart_placeholder.altair_chart(fig)

# Rows to hold the pie and bar charts.
col1, col2 = st.columns(2)
with col1:
    # Box Plot
    st.subheader('Time of Day')
    boxplot_placeholder = st.empty()
    fig = plot_community_time_day(st.session_state['new_df_key_1'])
    boxplot_placeholder.plotly_chart(fig)

    #Pie chart
with col2:
    st.subheader('Location Description')
    piechart_placeholder = st.empty()
    fig2 = location_description(st.session_state['new_df_key_1'])
    piechart_placeholder.plotly_chart(fig2)


st.text("")

    # Location Map
create_map = st.empty()
create_map.subheader("Crime Location Map")
df_coordinates, color, size = crime_map(st.session_state['new_df_key_1'])
create_map.map(df_coordinates, color=color, size=size)



# Load the data and update the placeholders when "Update Data" is clicked.
if data_button:
    crimecount_placeholder.subheader(crime_tot)

    new_df, crime_tot = clean_crimes(df_crime_1, df_communities, crime_type, begin_date_1, ending_date_1)
    st.session_state['new_df_key_1'] = new_df
    data_placeholder.dataframe(new_df)

    # Boxplot implementation
    fig = plot_community_time_day(st.session_state['new_df_key_1'])
    boxplot_placeholder.plotly_chart(fig)

    # Piechart implementation
    fig2 = location_description(st.session_state['new_df_key_1'])
    piechart_placeholder.plotly_chart(fig2)

    # Map implementation
    df_coordinates, color, size = crime_map(st.session_state['new_df_key_1'])
    create_map.map(df_coordinates, color=color, size=size)
