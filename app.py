import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATA_URL = (
    "https://media.githubusercontent.com/media/fjarlaegur/data_visualisation_project/main/Motor_Vehicle_Collisions_-_Crashes.csv?token=A6J3IEQMADD5NSSKQHCP4N3GELW3A"
)


st.title("Motor Vehicle Collisions in NYC")
st.markdown("### This application is a Streamlit dashboard that can be used "
            "to analyze motor vehicle collisions in NYC :sunglasses:")


@st.cache_data(persist=True)  # CACHE DECORATOR
# SO IT WON'T EXEC EVERY TIME WE RERUN THE APP
# IT WILL ONLY RERUN COMPUTATIONS IF CODE OR CODE INPUT HAS CHANGED
def load_data(num_of_rows):
    data = pd.read_csv(DATA_URL, nrows=num_of_rows)
    data["date/time"] = pd.to_datetime(data["CRASH_DATE"] + " " + data["CRASH_TIME"])
    data.drop(columns=["CRASH_DATE", "CRASH_TIME"], inplace=True)
    data.dropna(subset=["LATITUDE", "LONGITUDE"], inplace=True)
    column_order = ["date/time"] + [col for col in data.columns if col != "date/time"]
    data = data[column_order]
    # removing empty lines from selected columns
    # because a map cannot have no coordinates
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)  # special method for
    # renaming columns
    return data


data = load_data(100000)
original_data = data


st.header("Where were the most people injured?")
injured_people = st.slider("Number of people injured in vehicle collisions", 0, 19)
midpoint = (np.average(data["latitude"]), np.average(data["longitude"]))
map_data = data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how="any")
st.map(map_data, latitude=midpoint[0], longitude=midpoint[1], zoom=5)


st.header("How many collisions occur during the given time of day?")
hour = st.selectbox("Hour to look at", range(0, 24), 0, placeholder="Choose time")
data = data[data["date/time"].dt.hour == hour]


st.header(f"Vehicle collisions between {hour}:00 and {(hour + 1) % 24}:00")
# calculating the midpoint of all locations from the dataset so the map
# would be centered
# need to read pydeck docs about layers
st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data=data[["date/time", "latitude", "longitude"]],
            #  important to keep long lat in this order
            get_position=["longitude", "latitude"],
            radius=100,
            #  makes the map 3D
            extruded=True,
            pickable=True,
            elevation_scale=4,
            elevation_range=[0, 1000],
        ),
    ],
))


st.subheader(f"Breakdown by minute between {hour}:00 and {(hour + 1) % 24}:00")
filtered = data[
    (data["date/time"].dt.hour >= hour) & (data["date/time"].dt.hour < (hour + 1))
]
hist = np.histogram(filtered["date/time"].dt.minute, bins=60, range=(0, 60))[0]
chart_data = pd.DataFrame({"minute": range(60), "crashes": hist})
fig = px.bar(chart_data, x="minute", y="crashes", hover_data=["minute", "crashes"], height=400)
st.write(fig)


st.header("Top 5 streets by affected road users")
select = st.selectbox("Affected road users", ["Pedestrians", "Cyclists", "Motorists", "All road users"])
if select == "Pedestrians":
    by_pedestrians = original_data.query("injured_pedestrians >= 1")[["on_street_name", "injured_pedestrians"]]
    st.write(by_pedestrians.sort_values(by="injured_pedestrians", ascending=False).dropna(how="any")[:5])
elif select == "Cyclists":
    by_cyclists = original_data.query("injured_cyclists >= 1")[["on_street_name", "injured_cyclists"]]
    st.write(by_cyclists.sort_values(by="injured_cyclists", ascending=False).dropna(how="any")[:5])
elif select == "Motorists":
    by_motorists = original_data.query("injured_motorists >= 1")[["on_street_name", "injured_motorists"]]
    st.write(by_motorists.sort_values(by="injured_motorists", ascending=False).dropna(how="any")[:5])
else:
    by_everyone = original_data.query("injured_persons >= 1")[["on_street_name", "injured_persons"]]
    st.write(by_everyone.sort_values(by="injured_persons", ascending=False).dropna(how="any")[:5])


if st.checkbox("Show Raw Data", False):
    st.subheader("Raw Data")
    st.write(data)
