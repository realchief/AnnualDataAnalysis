import csv
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import date
import calendar 

import folium
from folium import plugins
from folium.features import DivIcon
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import imgkit

target_string1 = 'Miami'
target_column1 = 20

target_string2 = 'Entire home/apt'
target_column2 = 3

source_counter = 0
with open('E:/Stayd Archive/United States_Monthly_2018-05-16.csv', encoding='UTF-8', newline='\n' ) as f:
    reader = csv.reader(f)

    with open('C:/Users/Alex/Dropbox/Stayd/miami.csv', 'w', newline='', encoding="utf-8") as output_file:
        writer = csv.writer(output_file, delimiter=',')
    
        target_counter = 0
        for row in reader:
            if source_counter == 0:
                writer.writerow(row)
    
            if ( ( target_string1 in row[target_column1] ) & ( target_string2 in row[target_column2] ) ):
                target_counter += 1
                writer.writerow( row ) #[ s.replace('\n','') for s in row]

            source_counter += 1


df = pd.read_csv("C:/Users/Alex/Dropbox/Stayd/miami.csv")
df2 = pd.read_csv("C:/Users/Alex/Dropbox/Stayd/miami_prop.csv")
join_df = df2[["Property ID", "Number of Reviews", "Latitude", "Longitude"]].copy()
combined_df = df.set_index("Property ID").join( join_df.set_index("Property ID"), rsuffix='_verify')

from math import sin, cos, sqrt, atan2, radians
R = 3959 # radius of earth in miles
combined_df["distance"] = np.NaN

lat1 = radians(25.803113)  # Miami Hotel Location
lon1 = radians(-80.185741)

counter=0
for index, row in combined_df.iterrows():
    counter += 1
    if counter % 10000 == 0:
        print(counter) 
    lat2 = radians( row["Latitude"] )
    lon2 = radians( row["Longitude"] )
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    
    combined_df.at[index, "distance"] = distance

# filters
distance_df = combined_df.loc[ combined_df["distance"] < 2 ]
filtered_df = distance_df.reset_index()
filtered_df["# Reservations LTM"] = np.NaN
filtered_df["Res Days LTM"] = np.NaN
filtered_df["Occ Rt LTM"] = np.NaN

for index, row in filtered_df.iterrows():
    if index%1000 == 0:
        print(index)
    range_start = max(0, index-11)
    
    ltm_reservations = 0
    ltm_reservation_days = 0
    ltm_occupancy_rate = 0
    earliest_month = None
    latest_month = None
    for r in range(range_start, index+1):
        if filtered_df.loc[r]["Property ID"] == row["Property ID"]:
            ltm_reservations += filtered_df.loc[r]["Number of Reservations"] 
            ltm_reservation_days += filtered_df.loc[r]["Reservation Days"]
            
            this_month = datetime.strptime( filtered_df.loc[r]["Reporting Month"], "%Y-%m-%d").date()
            if not earliest_month:
                earliest_month = this_month
            else:
                if this_month < earliest_month:
                    earliest_month = this_month

            if not latest_month:
                latest_month = this_month
            else:
                if this_month > latest_month:
                    latest_month = this_month
                    
    latest_month = date(latest_month.year, latest_month.month, calendar.monthrange(latest_month.year, latest_month.month)[1] )
    filtered_df.at[index, "# Reservations LTM"] = ltm_reservations
    filtered_df.at[index, "Res Days LTM"] = ltm_reservation_days
    filtered_df.at[index, "Occ Rt LTM"] = ltm_reservation_days / (latest_month - earliest_month).days


filtered_df.to_csv("C:/Users/Alex/Dropbox/Stayd/miami v2.csv")
base_df = filtered_df

filtered_df = filtered_df.loc[filtered_df["Number of Reviews"] >= 1]  #big filter....
filtered_df = filtered_df.loc[filtered_df["# Reservations LTM"] >= 1]
filtered_df = filtered_df.loc[filtered_df["Occ Rt LTM"] >= 0.2]

filtered_df = filtered_df.loc[((filtered_df["Bedrooms"] == 0) | (filtered_df["Bedrooms"] == 1))]
filtered_df = filtered_df.dropna( subset=["ADR (USD)"])
filtered_df["ADR Norm"] = filtered_df["ADR (USD)"] / filtered_df["ADR (USD)"].sum()


width, height = 650, 500
map = folium.Map(location=[25.803113, -80.185741], zoom_start=14,
                 tiles='OpenStreetMap', width=width, height=height)

heat_dps = filtered_df[ ['Latitude', 'Longitude', 'ADR Norm']].as_matrix()
heat_dps = filtered_df[ ['Latitude', 'Longitude']].as_matrix()
map.add_child(plugins.HeatMap(heat_dps.tolist(), radius=15))


folium.map.Marker(
    [25.799113, -80.175741],
    icon=DivIcon(
        icon_size=(150,36),
        icon_anchor=(0,0),
        html='<div style="font-size: 18pt; color:black">Apr 2018</div>',
        )
    ).add_to(map)
map.save('miami hotel heat v1.html')

unique_months = np.sort( filtered_df["Reporting Month"].unique() )
max_adr = filtered_df["ADR (USD)"].max()
for i, mth in enumerate(unique_months):
    this_month_df = filtered_df.loc[ filtered_df["Reporting Month"] == mth ]
    map = folium.Map(location=[25.803113, -80.185741], zoom_start=14,
                     tiles='OpenStreetMap', width=width, height=height)

    this_month_df["ADR Norm"] = this_month_df["ADR (USD)"] / max_adr  # this_month_df["ADR (USD)"].sum()
    timed_heat_dps = this_month_df[ ['Latitude', 'Longitude', 'ADR Norm']].as_matrix()
    map.add_child( plugins.HeatMap(timed_heat_dps.tolist(), radius=15))
    
    folium.map.Marker(
        [25.799113, -80.175741],
        icon=DivIcon(
            icon_size=(150, 36),
            icon_anchor=(0, 0),
            html='<div style="font-size: 18pt; color:black">' + mth + '</div>',
        )
    ).add_to(map)
    
    map.save('miami hotel heat ' + mth + '.html')
    imgkit.from_file('miami hotel heat ' + mth + '.html', str(i)+".jpg")
    print(str(i) + ":" + mth)
