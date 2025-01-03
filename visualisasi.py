import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Set page title and description
st.set_page_config(page_title="Chicago Crime Data Visualization", layout="wide")
st.title("Chicago Crime Data Analysis")

# Data URL
data_url = 'https://data.cityofchicago.org/resource/dqcy-ctma.csv'

# Load the data
try:
    df = pd.read_csv(data_url)
    st.write("Data loaded successfully!")
except Exception as e:
    st.error(f"An error occurred: {e}")

# Count total crimes by type
crime_type_counts = df['primary_type'].value_counts()

# Create two columns for layout
col1, col2 = st.columns(2)

# Column 1: Plot Total Crimes by Type
with col1:
    st.subheader("Total Crimes by Type in Chicago")
    crime_type_data = pd.DataFrame({
        "Crime Type": crime_type_counts.index,
        "Count": crime_type_counts.values
    })

    # Plot using Plotly
    fig1 = px.bar(crime_type_data, x="Crime Type", y="Count", 
                  labels={"Count": "Total Number of Crimes"},
                  color_discrete_sequence=["skyblue"])
    fig1.update_layout(xaxis_title="Crime Type", yaxis_title="Total Number of Crimes")
    st.plotly_chart(fig1)

    st.header("Choose a District")
    
    districts = df['district'].dropna().unique().tolist()
    district_selected = st.selectbox("Select District", districts)

    # Filter the dataset based on the selected district
    df_district_filtered = df[df['district'] == district_selected]
    district_counts = df_district_filtered['primary_type'].value_counts()

    district_data = pd.DataFrame({
        "Crime Type": district_counts.index,
        "Count": district_counts.values
    })

    # Plot crime counts by district for the selected district
    fig2 = px.bar(district_data, x="Crime Type", y="Count", 
                  title=f"Crime Counts by District ({district_selected})",
                  labels={"Count": "Total Number of Crimes"},
                  color_discrete_sequence=["lightgreen"])
    fig2.update_layout(xaxis_title="Crime Type", yaxis_title="Total Number of Crimes")
    st.plotly_chart(fig2)

# Column 2: Filter based on location, IUCR, and FBI Code
with col2:
    st.header("Choose a Category to Analyze")

    # Dropdown to choose between 'location_description', 'iucr', or 'fbi_code'
    category_selected = st.selectbox("Select a Category to Analyze", ["Location Description", "IUCR Code", "FBI Code"])

    # Process and visualize data based on selected category
    if category_selected == "Location Description":
        
        location_counts = df['location_description'].value_counts()
        location_data = pd.DataFrame({
            "Location Description": location_counts.index[:10],
            "Count": location_counts.values[:10]
        })

        # Plot using Plotly
        fig3 = px.bar(location_data, x="Location Description", y="Count", 
                      title="Top 10 Crime Locations in Chicago",
                      labels={"Count": "Number of Crimes"},
                      color_discrete_sequence=["salmon"])
        fig3.update_layout(xaxis_title="Location Description", yaxis_title="Number of Crimes")
        st.plotly_chart(fig3)

    elif category_selected == "IUCR Code":
        
        iucr_counts = df['iucr'].value_counts()
        iucr_data = pd.DataFrame({
            "IUCR Code": iucr_counts.index[:10],
            "Count": iucr_counts.values[:10]
        })

        # Plot using Plotly
        fig4 = px.bar(iucr_data, x="IUCR Code", y="Count", 
                      title="Top 10 Crime Types by IUCR Code in Chicago",
                      labels={"Count": "Number of Crimes"},
                      color_discrete_sequence=["salmon"])
        fig4.update_layout(xaxis_title="IUCR Code", yaxis_title="Number of Crimes")
        st.plotly_chart(fig4)

    elif category_selected == "FBI Code":
        
        fbi_counts = df['fbi_code'].value_counts()
        fbi_data = pd.DataFrame({
            "FBI Code": fbi_counts.index[:10],
            "Count": fbi_counts.values[:10]
        })

        # Plot using Plotly
        fig5 = px.bar(fbi_data, x="FBI Code", y="Count", 
                      title="Top 10 Crimes by FBI Code in Chicago",
                      labels={"Count": "Number of Crimes"},
                      color_discrete_sequence=["lightblue"])
        fig5.update_layout(xaxis_title="FBI Code", yaxis_title="Number of Crimes")
        st.plotly_chart(fig5)

    # **NEW FEATURE**: Dropdown for pie chart options (Arrest or Domestic Crime)
    st.header("Pie Chart Analysis")

    pie_chart_selected = st.selectbox("Select Pie Chart Type", ["Arrest", "Domestic Crime"])

    if pie_chart_selected == "Arrest":
        arrest_counts = df['arrest'].value_counts()

        arrest_data = pd.DataFrame({
            "Status": ["Not Arrested", "Arrested"],
            "Count": arrest_counts.values
        })

        # Plot using Plotly
        fig6 = px.pie(arrest_data, names="Status", values="Count", 
                      title="Distribution of Crimes Resulting in Arrests in Chicago",
                      color_discrete_sequence=["lightcoral", "lightgreen"])
        st.plotly_chart(fig6)

    elif pie_chart_selected == "Domestic Crime":
        domestic_counts = df['domestic'].value_counts()

        domestic_data = pd.DataFrame({
            "Type": ["Non-Domestic", "Domestic"],
            "Count": domestic_counts.values
        })

        # Plot using Plotly
        fig7 = px.pie(domestic_data, names="Type", values="Count", 
                      title="Domestic vs Non-Domestic Crimes in Chicago",
                      color_discrete_sequence=["lightblue", "lightcoral"])
        st.plotly_chart(fig7)

# Drop rows with missing coordinates
coordinates_df = df.dropna(subset=['latitude', 'longitude'])

# Map visualization
st.header("Crime Locations in Chicago")
st.write("The map below shows the locations of reported crimes in Chicago.")

# Plotly map
fig = px.scatter_mapbox(
    coordinates_df,
    lat="latitude",
    lon="longitude",
    hover_name="primary_type",
    hover_data={"location_description": True, "arrest": True, "domestic": True},
    color_discrete_sequence=["purple"],
    title="Crime Locations in Chicago",
    height=600,
    zoom=10
)

# Set the map style
fig.update_layout(mapbox_style="carto-positron")
fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

# Display the map
st.plotly_chart(fig)