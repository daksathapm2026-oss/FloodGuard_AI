import streamlit as st
import pandas as pd
import pydeck as pdk
import joblib
import requests

st.set_page_config(
    page_title="FloodGuard AI",
    page_icon="🌊",
    layout="wide"
)

# =========================================================
# LOAD MODEL
# =========================================================

model = joblib.load("flood_model.pkl")

coordinates = {
    "Chennai": (13.0827, 80.2707),
    "Tambaram": (12.9249, 80.1000),
    "Coimbatore": (11.0168, 76.9558),
    "Madurai": (9.9252, 78.1198),
    "Tiruchirappalli": (10.7905, 78.7047)
}

location_data = {
    "Chennai": {
        "rainfall": 5.05,
        "soil_moisture": 16.5,
        "water_level": 9.404,
        "elevation": 3,
        "warning": "Scattered rain — 26–50% stations"
    },
    "Tambaram": {
        "rainfall": 5.05,
        "soil_moisture": 18.9,
        "water_level": 9.432,
        "elevation": 38,
        "warning": "Scattered rain — 26–50% stations"
    },
    "Coimbatore": {
        "rainfall": 5.05,
        "soil_moisture": 25.3,
        "water_level": 303.295,
        "elevation": 431,
        "warning": "Scattered rain — 26–50% stations"
    },
    "Madurai": {
        "rainfall": 5.05,
        "soil_moisture": 15.6,
        "water_level": 117.95,
        "elevation": 132,
        "warning": "Scattered rain — 26–50% stations"
    },
    "Tiruchirappalli": {
        "rainfall": 5.05,
        "soil_moisture": 10.7,
        "water_level": 81.047,
        "elevation": 81,
        "warning": "Scattered rain — 26–50% stations"
    }
}

# =========================================================
# WEATHER DATA
# =========================================================

def get_weather_data(region, forecast_hours=24):

    lat, lon = coordinates[region]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,soil_moisture_0_to_1cm",
        "forecast_hours": forecast_hours,
        "timezone": "Asia/Kolkata"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    rainfall_values = data["hourly"]["precipitation"]
    soil_values = data["hourly"]["soil_moisture_0_to_1cm"]

    rainfall = sum(
        float(x)
        for x in rainfall_values
        if x is not None
    )

    valid_soil = [
        float(x)
        for x in soil_values
        if x is not None
    ]

    soil_moisture = (
        valid_soil[0] * 100
        if valid_soil
        else None
    )

    return rainfall, soil_moisture, rainfall_values


# =========================================================
# CWC WATER LEVEL
# =========================================================

def get_cwc_water_level(region):

    district_map = {
        "Chennai": "Chennai",
        "Tambaram": "Chengalpattu",
        "Coimbatore": "Coimbatore",
        "Madurai": "Madurai",
        "Tiruchirappalli": "Tiruchirappalli"
    }

    district = district_map.get(region)

    try:

        df = pd.read_csv(
            "data/cwc_water_level.csv"
        )

        df.columns = df.columns.str.strip()

        df = df[
            df["State"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "tamil nadu"
        ]

        df = df[
            df["District"]
            .astype(str)
            .str.strip()
            .str.lower()
            == district.lower()
        ]

        water_col = (
            "River Water Level Telemetry Hourly (meter)"
        )

        df[water_col] = pd.to_numeric(
            df[water_col],
            errors="coerce"
        )

        df["Data Acquisition Time"] = pd.to_datetime(
            df["Data Acquisition Time"],
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                water_col,
                "Data Acquisition Time"
            ]
        )

        if df.empty:
            return None

        df = df.sort_values(
            "Data Acquisition Time"
        )

        return float(
            df.iloc[-1][water_col]
        )

    except Exception:
        return None


# =========================================================
# STYLE
# =========================================================

st.markdown(
"""
<style>

.stApp {
    background-color: #f4f7fb;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}

.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #102a43;
}

.subtitle {
    color: #627d98;
    font-size: 16px;
    margin-bottom: 25px;
}

.hero {
    background: linear-gradient(120deg, #071d49, #0b5fa5);
    padding: 30px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 32px;
    font-weight: 800;
}

.hero-text {
    color: #dbeafe;
    font-size: 15px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #e6edf5;
    box-shadow: 0 5px 18px rgba(0,0,0,0.05);
    margin-bottom: 18px;
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    color: #102a43;
}

.big-number {
    font-size: 28px;
    font-weight: 800;
    color: #102a43;
}

.small-text {
    color: #829ab1;
    font-size: 13px;
}

.high-risk {
    color: #dc2626;
    font-size: 28px;
    font-weight: 800;
}

.warning {
    background: #fff7ed;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #fed7aa;
    color: #9a3412;
}

</style>
""",
unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🌊 FloodGuard AI")

    st.caption(
        "Early Flood Prediction & Mapping"
    )

    st.divider()

    st.markdown("### 📍 Prediction Area")

    region = st.selectbox(
        "Select region",
        list(coordinates.keys())
    )

    forecast = st.selectbox(
        "Prediction period",
        [
            "Next 24 hours",
            "Next 48 hours",
            "Next 72 hours"
        ]
    )

    st.divider()

    st.markdown("### 🗺️ Risk Levels")

    st.write("🟢 Low")
    st.write("🟡 Moderate")
    st.write("🟠 High")
    st.write("🔴 Very High")

    st.divider()

    st.caption("Hackathon Prototype")


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🌊 FloodGuard AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered early flood prediction using '
    'remote sensing and environmental data'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# HERO
# =========================================================

st.markdown(
f"""
<div class="hero">

<div class="hero-title">
Predict floods before they happen.
</div>

<div class="hero-text">

FloodGuard AI combines rainfall,
soil moisture, water level and elevation
to estimate flood risk for {region}.

</div>

</div>
""",
unsafe_allow_html=True
)


selected_data = location_data[region]


# =========================================================
# FORECAST HOURS
# =========================================================

if forecast == "Next 24 hours":
    forecast_hours = 24
elif forecast == "Next 48 hours":
    forecast_hours = 48
else:
    forecast_hours = 72


# =========================================================
# LIVE WEATHER
# =========================================================

try:

    rainfall, soil_moisture, hourly_rainfall = (
        get_weather_data(
            region,
            forecast_hours
        )
    )

    if soil_moisture is None:
        raise ValueError(
            "Soil moisture unavailable"
        )

    weather_status = "Live Open-Meteo data"

except Exception:

    rainfall = selected_data["rainfall"]

    soil_moisture = selected_data[
        "soil_moisture"
    ]

    hourly_rainfall = [
        rainfall / forecast_hours
        for _ in range(forecast_hours)
    ]

    weather_status = (
        "Prototype fallback data"
    )


# =========================================================
# CWC WATER LEVEL
# =========================================================

cwc_water_level = get_cwc_water_level(region)

if cwc_water_level is not None:

    water_level = cwc_water_level

    cwc_status = "Live CWC telemetry"

else:

    water_level = selected_data[
        "water_level"
    ]

    cwc_status = "Prototype fallback"


# =========================================================
# ELEVATION
# =========================================================

elevation = selected_data["elevation"]


# =========================================================
# MODEL INPUT
# =========================================================

model_water_level = min(
    water_level / 20,
    9
)

model_input = pd.DataFrame([
    {
        "rainfall": rainfall,
        "soil_moisture": soil_moisture,
        "water_level": model_water_level,
        "elevation": elevation
    }
])


# =========================================================
# AI PREDICTION
# =========================================================

st.subheader(
    "🤖 FloodGuard AI Prediction"
)

prediction = model.predict(
    model_input
)[0]

probabilities = model.predict_proba(
    model_input
)[0]

no_flood_probability = (
    float(probabilities[0]) * 100
)

flood_probability = (
    float(probabilities[1]) * 100
)


# =========================================================
# RISK CLASSIFICATION
# =========================================================

if flood_probability >= 80:

    risk_level = "VERY HIGH RISK"

    risk_message = (
        "Environmental conditions indicate a very high "
        "prototype flood risk."
    )

elif flood_probability >= 60:

    risk_level = "HIGH RISK"

    risk_message = (
        "Environmental conditions indicate an elevated "
        "prototype flood risk."
    )

elif flood_probability >= 30:

    risk_level = "MODERATE RISK"

    risk_message = (
        "Environmental conditions indicate a moderate "
        "prototype flood risk."
    )

else:

    risk_level = "LOW RISK"

    risk_message = (
        "Current conditions indicate a relatively low "
        "prototype flood risk."
    )


# =========================================================
# MAIN PREDICTION DISPLAY
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🌊 Flood Probability",
        f"{flood_probability:.1f}%"
    )

with col2:
    st.metric(
        "✅ No-Flood Probability",
        f"{no_flood_probability:.1f}%"
    )

with col3:
    st.metric(
        "⚠️ Risk Level",
        risk_level
    )

st.info(risk_message)


# =========================================================
# AI INPUT FACTORS
# =========================================================

st.markdown(
    "### 🔍 AI Input Factors"
)

factor1, factor2, factor3, factor4 = (
    st.columns(4)
)

with factor1:
    st.metric(
        "☔ Rainfall",
        f"{rainfall:.1f} mm"
    )

with factor2:
    st.metric(
        "🌱 Soil Moisture",
        f"{soil_moisture:.1f}%"
    )

with factor3:
    st.metric(
        "🌊 Water Level",
        f"{water_level:.2f} m"
    )

with factor4:
    st.metric(
        "🏔️ Elevation",
        f"{elevation:.0f} m"
    )


st.caption(
    "These four environmental factors are supplied "
    "to the Random Forest model to generate the "
    "prototype flood-risk estimate."
)


# =========================================================
# FLOOD RISK FACTORS
# =========================================================

st.subheader(
    "📊 Flood Risk Factors"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "☔ Rainfall",
        f"{rainfall:.1f} mm"
    )

with col2:
    st.metric(
        "🌱 Soil Moisture",
        f"{soil_moisture:.1f}%"
    )

with col3:
    st.metric(
        "🌊 Water Level",
        f"{water_level:.2f} m"
    )

with col4:
    st.metric(
        "🏔️ Elevation",
        f"{elevation:.0f} m"
    )


st.caption(
    "These environmental factors are used by the "
    "FloodGuard AI model to estimate flood risk."
)


# =========================================================
# EXPLANATION
# =========================================================

with st.expander(
    "🧠 How did FloodGuard make this prediction?"
):

    st.write(
        "FloodGuard combines four environmental inputs:"
    )

    st.markdown(
    """
    **1. Rainfall**

    Forecast precipitation provides information
    about incoming water.

    **2. Soil Moisture**

    Wetter soil can reduce infiltration and increase
    surface runoff.

    **3. Water Level**

    River/water-level telemetry provides information
    about current water conditions.

    **4. Elevation**

    Elevation provides geographical context for
    the selected location.

    These inputs are passed to the **Random Forest
    Classifier**, which produces the flood and
    no-flood probabilities displayed above.
    """
    )

    st.warning(
        "Prototype note: the current Random Forest was "
        "trained using sample training data. The "
        "probability should therefore be treated as an "
        "illustrative prototype result, not a scientifically "
        "validated flood forecast."
    )


# =========================================================
# METRICS
# =========================================================

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    st.markdown(
    f"""
    <div class="card">

    <div class="small-text">
    FLOOD PROBABILITY
    </div>

    <div class="big-number">
    {flood_probability:.1f}%
    </div>

    <div class="small-text">
    {risk_level}
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )


with c2:

    st.markdown(
    f"""
    <div class="card">

    <div class="small-text">
    RAINFALL FORECAST
    </div>

    <div class="big-number">
    {rainfall:.1f} mm
    </div>

    <div class="small-text">
    {forecast}
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )


with c3:

    st.markdown(
    f"""
    <div class="card">

    <div class="small-text">
    SOIL MOISTURE
    </div>

    <div class="big-number">
    {soil_moisture:.1f}%
    </div>

    <div class="small-text">
    Live environmental input
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )


with c4:

    st.markdown(
    f"""
    <div class="card">

    <div class="small-text">
    ELEVATION
    </div>

    <div class="big-number">
    {elevation:.1f} m
    </div>

    <div class="small-text">
    Terrain elevation
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )


with c5:

    st.markdown(
    f"""
    <div class="card">

    <div class="small-text">
    CWC WATER LEVEL
    </div>

    <div class="big-number">
    {water_level:.2f} m
    </div>

    <div class="small-text">
    {cwc_status}
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )


st.caption(
    f"Weather source status: {weather_status} • "
    f"CWC status: {cwc_status}"
)


# =========================================================
# MAP
# =========================================================

left, right = st.columns([1.7, 1])

with left:

    st.markdown(
    """
    <div class="card">

    <div class="card-title">
    🗺️ Predicted Flood Risk Map
    </div>

    <div class="small-text">
    Demonstration risk visualization for the
    selected region.
    </div>

    </div>
    """,
    unsafe_allow_html=True
    )

    center_lat, center_lon = coordinates[
        region
    ]

    lat_offsets = [
        0.00,
        0.015,
        -0.015,
        0.020,
        -0.020,
        0.010,
        -0.010
    ]

    lon_offsets = [
        0.00,
        0.020,
        -0.020,
        0.030,
        -0.030,
        0.040,
        -0.040
    ]

    risk_values = [
        flood_probability,
        max(0, flood_probability - 5),
        max(0, flood_probability - 10),
        max(0, flood_probability - 15),
        max(0, flood_probability - 20),
        max(0, flood_probability - 8),
        max(0, flood_probability - 18)
    ]

    map_data = pd.DataFrame({

        "latitude": [
            center_lat + x
            for x in lat_offsets
        ],

        "longitude": [
            center_lon + x
            for x in lon_offsets
        ],

        "risk": risk_values
    })


    def risk_color(value):

        if value >= 80:
            return [220, 38, 38, 150]

        elif value >= 60:
            return [249, 115, 22, 150]

        elif value >= 30:
            return [234, 179, 8, 150]

        else:
            return [34, 197, 94, 150]


    map_data["color"] = (
        map_data["risk"].apply(risk_color)
    )

    map_data["radius"] = (
        map_data["risk"] * 18
    )


    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[longitude, latitude]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True
    )


    view = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=10
    )


    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip={
            "text": "Flood Risk: {risk}%"
        }
    )


    st.pydeck_chart(
        deck,
        use_container_width=True
    )


# =========================================================
# PREDICTION PANEL
# =========================================================

with right:

    st.markdown(
    f"""
    <div class="card">

    <div class="small-text">
    CURRENT PREDICTION
    </div>

    <div class="high-risk">
    🌊 {risk_level}
    </div>

    <div class="big-number">
    {flood_probability:.1f}%
    </div>

    <div class="small-text">
    Estimated flood probability
    </div>

    <br>

    <div class="warning">

    ⚠️ <b>Early Warning</b>

    <br><br>

    {risk_level} flood risk detected
    for {region} for the {forecast.lower()}.

    </div>

    </div>
    """,
    unsafe_allow_html=True
    )


    st.markdown(
    f"""
    <div class="card">

    <div class="card-title">
    🤖 Model Information
    </div>

    <br>

    <div class="small-text">
    MODEL
    </div>

    <div class="big-number">
    Random Forest
    </div>

    <br>

    <div class="small-text">
    INPUT VARIABLES
    </div>

    <p>
    Rainfall • Soil Moisture • Water Level • Elevation
    </p>

    </div>
    """,
    unsafe_allow_html=True
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🌊 FloodGuard AI | Early Flood Prediction & Mapping | "
    "Hackathon Prototype"
)
