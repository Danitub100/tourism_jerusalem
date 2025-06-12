import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# 🟢 קונפיגורציה כללית לעמוד
st.set_page_config(page_title="🔗 קשרים בין אתרים בירושלים", layout="wide")

# 🔹 באנר עליון
st.markdown("""
    <div style='background-color:#EAF4FF;padding:30px;border-radius:10px;margin-bottom:30px;'>
        <h1 style='color:#003366;text-align:center;'>🔗 קשרים בין אתרים בירושלים</h1>
        <p style='text-align:center;font-size:18px;'>
            מערכת אינטראקטיבית לניתוח תנועת תיירים בין אתרים בירושלים – בחר פילוח, רף סינון, ואתר יעד.
        </p>
    </div>
""", unsafe_allow_html=True)

# פונקציית צבע לפי Confidence
def get_color_by_confidence(conf):
    if conf >= 0.8:
        return "#800000"
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

# 📘 קואורדינטות אתרים
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

# 🗭 פילטרים בצד
st.sidebar.header(":mag_right: סינון נתונים")
age_option = st.sidebar.selectbox(":busts_in_silhouette: בחר קבוצת גיל", ["הכל", "צעירים", "מבוגרים"])
religion_option = st.sidebar.selectbox(":star_of_david: בחר דת", ["הכל", "יהודים", "נוצרים"])
continent_option = st.sidebar.selectbox(":earth_africa: בחר יבשת", ["הכל", "אירופה", "אמריקה"])

support_threshold_percent = st.sidebar.number_input(":bar_chart: רף תמיכה (%)", min_value=0, max_value=100, value=5, step=1)
confidence_threshold_percent = st.sidebar.number_input(":closed_lock_with_key: רף ביטחון (%)", min_value=0, max_value=100, value=40, step=1)

support_threshold = support_threshold_percent / 100
confidence_threshold = confidence_threshold_percent / 100

filters_selected = sum([
    age_option != "הכל",
    religion_option != "הכל",
    continent_option != "הכל"
])
if filters_selected > 1:
    st.warning("אנא בחר רק פילטר אחד (גיל או דת או יבשת)")
    st.stop()

# 🗂️ בחירת קובץ
if age_option == "צעירים":
    file_name = "association_rules_jerusalem_young.xlsx"
elif age_option == "מבוגרים":
    file_name = "association_rules_jerusalem_old.xlsx"
elif religion_option == "יהודים":
    file_name = "association_rules_jerusalem_jewish.xlsx"
elif religion_option == "נוצרים":
    file_name = "association_rules_jerusalem_christian.xlsx"
elif continent_option == "אירופה":
    file_name = "association_rules_jerusalem_europe.xlsx"
elif continent_option == "אמריקה":
    file_name = "association_rules_jerusalem_america.xlsx"
else:
    file_name = "association_rules_jerusalem_all.xlsx"

try:
    df = pd.read_excel(file_name)
except FileNotFoundError:
    st.error(f"שגיאה: הקובץ לא נמצא ({file_name})")
    st.stop()

available_targets = sorted(df['To'].dropna().unique())
selected_target = st.sidebar.selectbox(":round_pushpin: סינון לפי אתר יעד", ["הכל"] + available_targets)
if selected_target != "הכל":
    df = df[df['To'] == selected_target]

df = df[(df['Support'] >= support_threshold) & (df['Confidence'] >= confidence_threshold)]

st.markdown("### 📋 טבלת חוקי אסוציאציה")
if df.empty:
    st.warning("לא נמצאו חוקים התואמים את הקריטריונים שבחרת.")
else:
    df_clean = df.drop(columns=["Lift", "Intersection"], errors='ignore')
    df_clean = df_clean.sort_values(by="Support", ascending=False).reset_index(drop=True)
    df_clean["Support"] = (df_clean["Support"] * 100).round(1).astype(str) + "%"
    df_clean["Confidence"] = (df_clean["Confidence"] * 100).round(1).astype(str) + "%"
    st.dataframe(df_clean, use_container_width=True)

# 🗼 מפה אינטראקטיבית
st.markdown("### 🌍 מפת קשרים אינטראקטיבית")
st.markdown("""
- **עובי הקו** מייצג את רמת ה-Support  
- **צבע הקו** מייצג את ה-Confidence  
- **החצים** מייצגים את כיוון התנועה
""")
m = folium.Map(location=[31.7767, 35.2345], zoom_start=13)

for _, row in df.iterrows():
    from_place = row['From']
    to_place = row['To']
    if from_place in location_coords and to_place in location_coords:
        coords_from = location_coords[from_place]
        coords_to = location_coords[to_place]

        folium.PolyLine(
            locations=[coords_from, coords_to],
            popup=(f"<b>{from_place} ➔ {to_place}</b><br>"
                   f"Support: {row['Support']:.2f}<br>"
                   f"Confidence: {row['Confidence']:.2f}"),
            tooltip=f"{from_place} → {to_place} (Support: {row['Support']:.2f}, Confidence: {row['Confidence']:.2f})",
            weight=2 + row['Support'] * 15,
            color=get_color_by_confidence(row['Confidence'])
        ).add_to(m)

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

# 🔹 מקרא צבעים
st.markdown("""
---
#### 🎨 מקרא צבעים לפי Confidence
- <span style='color:#800000;'>⬤</span>  ≥ 0.8 – בורדו כהה  
- <span style='color:red;'>⬤</span> 0.7–0.79 – אדום  
- <span style='color:orange;'>⬤</span> 0.6–0.69 – כתום  
- <span style='color:yellow;'>⬤</span> 0.5–0.59 – צהוב  
- <span style='color:blue;'>⬤</span> 0.4–0.49 – כחול  
- <span style='color:gray;'>⬤</span> < 0.4 – אפור  
""", unsafe_allow_html=True)
