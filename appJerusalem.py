import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# Page configuration
st.set_page_config(page_title="🔗 Association Rules in Jerusalem", layout="wide")
st.title("🔗 Association Rules in Jerusalem Tourism Activities")

# Function for color by confidence
def get_color_by_confidence(conf):
    if conf >= 0.8:
        return "#800000"  # Dark Bordeaux
    elif conf >= 0.7:
        return "red"
    elif conf >= 0.6:
        return "orange"
    elif conf >= 0.5:
        return "yellow"
    elif conf >= 0.4:
        return "blue"
    else:
        return "gray"

# קואורדינטות מדויקות לפי שמות בעברית מתוך הקובץ
location_coords = {
    "הר הזיתים": (31.77833, 35.24389),
    "הכותל המערבי": (31.7767, 35.2345),
    "הר הבית": (31.77806, 35.23583),
    "גת שמנים": (31.779402, 35.240197),
    "הרובע הארמני": (31.775, 35.2294444),
    "הרובע היהודי": (31.77611111, 35.23222222),
    "הרובע המוסלמי": (31.78083, 35.2325),
    "הרובע הנוצרי": (31.778472, 35.2294),
    "ויה דולורוזה": (31.7794, 35.2320722),
    "כנסיית הקבר": (31.77833, 35.22972),
    "מגדל דוד": (31.77611, 35.22778),
    "מוזיאון יד ושם": (31.7744237, 35.1772481),
    "מוזיאון ישראל": (31.7725, 35.20417),
    "ממילא": (31.77611, 35.22333),
    "קבר דוד המלך": (31.771639, 35.2290139),
    "שוק מחנה יהודה": (31.78556, 35.21222),
    "שער יפו": (31.77661, 35.22755),
    "גן לאומי עיר דוד": (31.77361, 35.23556),
    "גן הקבר": (31.7838528, 35.2299778),
}

# Sidebar filters
st.sidebar.header("🧭 Filters")
age_option = st.sidebar.selectbox("Select Age Group", ["ALL", "Young", "Old"])
religion_option = st.sidebar.selectbox("Select Religion", ["ALL", "Jewish", "Christian"])
continent_option = st.sidebar.selectbox("Select Continent", ["ALL", "Europe", "America"])

# Threshold sliders
min_support = st.sidebar.slider("Minimum Support", 0.0, 1.0, 0.05, 0.01)
min_confidence = st.sidebar.slider("Minimum Confidence", 0.0, 1.0, 0.4, 0.01)

# Filter validation
filters_selected = sum([
    age_option != "ALL",
    religion_option != "ALL",
    continent_option != "ALL"
])

if filters_selected > 1:
    st.warning("Please select only one filter (Age OR Religion OR Continent)")
    st.stop()

# File selection
if age_option == "Young":
    file_name = "association_rules_jerusalem_young.xlsx"
elif age_option == "Old":
    file_name = "association_rules_jerusalem_old.xlsx"
elif religion_option == "Jewish":
    file_name = "association_rules_jerusalem_jewish.xlsx"
elif religion_option == "Christian":
    file_name = "association_rules_jerusalem_christian.xlsx"
elif continent_option == "Europe":
    file_name = "association_rules_jerusalem_europe.xlsx"
elif continent_option == "America":
    file_name = "association_rules_jerusalem_america.xlsx"
else:
    file_name = "association_rules_jerusalem_all.xlsx"

# Load Excel file
try:
    df = pd.read_excel(file_name)
except FileNotFoundError:
    st.error(f"File not found: {file_name}")
    st.stop()

# Filter by source location
available_sources = sorted(df['From'].dropna().unique())
selected_source = st.sidebar.selectbox("Filter by Source Location", ["ALL"] + available_sources)
if selected_source != "ALL":
    df = df[df['From'] == selected_source]

# Apply threshold filters
df = df[(df['Support'] >= min_support) & (df['Confidence'] >= min_confidence)]

# Display metrics
st.markdown("""
### 📊 Association Rules Table
Only rules starting **from** the selected source and meeting threshold criteria are shown below.
""")
st.dataframe(df.reset_index(drop=True), use_container_width=True)

# Map
st.markdown("""
### 🗺️ Interactive Map of Associations
- **Line Thickness** = Support Level
- **Line Color** = Confidence Level
- **Arrow Direction** = Rule Direction
""")
m = folium.Map(location=[31.7767, 35.2345], zoom_start=13)

for _, row in df.iterrows():
    from_place = row['From']
    to_place = row['To']
    if from_place in location_coords and to_place in location_coords:
        coords_from = location_coords[from_place]
        coords_to = location_coords[to_place]

        # Draw line with arrow marker
        folium.PolyLine(
            locations=[coords_from, coords_to],
            popup=(
                f"<b>{from_place} ➝ {to_place}</b><br>"
                f"Support: {row['Support']:.2f}<br>"
                f"Confidence: {row['Confidence']:.2f}<br>"
                f"Lift: {row['Lift']:.2f}"
            ),
            tooltip=f"{from_place} → {to_place}\nSupport: {row['Support']:.2f}, Confidence: {row['Confidence']:.2f}",
            weight=2 + row['Support'] * 15,
            color=get_color_by_confidence(row['Confidence'])
        ).add_to(m)

        # Add direction arrow at midpoint
        mid_lat = (coords_from[0] + coords_to[0]) / 2
        mid_lon = (coords_from[1] + coords_to[1]) / 2
        folium.RegularPolygonMarker(
            location=(mid_lat, mid_lon),
            number_of_sides=3,
            radius=6,
            color=get_color_by_confidence(row['Confidence']),
            fill=True,
            fill_color=get_color_by_confidence(row['Confidence']),
            rotation=45
        ).add_to(m)

folium_static(m)

# Legend
st.markdown("""
---
#### 🎨 Color Legend (Confidence)
- **Dark Bordeaux** ≥ 0.8  
- **Red**: 0.7–0.79  
- **Orange**: 0.6–0.69  
- **Yellow**: 0.5–0.59  
- **Blue**: 0.4–0.49  
- **Gray**: < 0.4  
""")
