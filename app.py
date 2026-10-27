# app.py
import streamlit as st
import pandas as pd
import base64
import os
from database import YandexDB
from engine import YandexMapScraper

st.set_page_config(page_title="Yandex Maps Lead Generator", layout="wide")

# ================= [Background Image & Transparent CSS] =================
def apply_custom_css():
    bg_image_path = "bg_map.png"  
    if os.path.exists(bg_image_path):
        with open(bg_image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode()
        bg_css = f"background-image: url('data:image/png;base64,{b64_image}');"
    else:
        bg_css = "background-color: #e5e5e5;"

    st.markdown(f"""
    <style>
    /* 1. Global Background Image */
    [data-testid="stAppViewContainer"] {{
        {bg_css}
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* 2. Overlay to fade the map (Adjust 0.7 for lighter background) */
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(255, 255, 255, 0.7);
        z-index: 0;
    }}
    
    /* 3. Hide Streamlit Defaults */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
        position: relative;
        z-index: 1;
    }}
    header {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* 4. Transparent Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: transparent !important;
        border-radius: 16px !important;
        border: 2px solid rgba(0, 0, 0, 0.2) !important;
        padding: 20px !important;
    }}
    
    /* 5. Transparent Text & Widgets */
    .stMarkdown, p, h1, h2, h3, label, .stSubheader, .main-title {{
        background-color: transparent !important;
        color: #1a1a1a !important;
        text-shadow: 0px 0px 4px rgba(255,255,255,0.8);
    }}
    
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextInput, .stSlider {{
        background-color: transparent !important;
        border-radius: 8px;
    }}
    
    /* Transparent Buttons */
    .stButton > button {{
        background-color: transparent !important;
        color: #196dff !important;
        border: 2px solid #196dff !important;
        font-weight: bold;
        text-shadow: none;
    }}
    .stButton > button:hover {{
        background-color: rgba(25, 109, 255, 0.1) !important;
    }}
    
    .stDownloadButton > button {{
        background-color: transparent !important;
        color: #3bb300 !important;
        border: 2px solid #3bb300 !important;
        font-weight: bold;
    }}
    
    div[data-testid="stMetric"] {{
        background-color: transparent !important;
        text-shadow: 0px 0px 4px rgba(255,255,255,0.8);
    }}
    
    /* Table stays white for readability */
    div[data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 8px;
    }}
    
    .main-title {{
        font-size: 42px !important;
        font-weight: 900 !important;
        display: inline-block;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# ================= [Database & Session Init] =================
db = YandexDB()
if "is_scraping" not in st.session_state:
    st.session_state.is_scraping = False

# ================= Layout =================

# 1. Top Title Zone
with st.container(border=True):
    st.markdown('<div class="main-title">Yandex Maps B2B Lead Generator</div>', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 16px; margin-top: 5px;'>Client Dashboard: Collect and manage your target database directly from the screen without touching the source code.</p>", unsafe_allow_html=True)

st.write("")

# Split into Left and Right columns
col_left, col_right = st.columns([1, 2], gap="large")

# 2. Left Column (Control + History)
with col_left:
    # 2-1. Control Zone
    with st.container(border=True):
        st.subheader("🕹️ Data Collection")
        st.write("")
        input_keyword = st.text_input(
            "Enter keyword to scrape", 
            placeholder="e.g., Стоматология Москва",
            disabled=st.session_state.is_scraping
        )
        input_scroll = st.slider(
            "Scroll depth (iterations)", 
            min_value=1, max_value=50, value=10,
            disabled=st.session_state.is_scraping
        )
        st.write("")
        if st.session_state.is_scraping:
            st.button("⏳ Extracting data...", disabled=True, use_container_width=True)
            st.warning("⚠️ System is currently exploring Yandex Maps.")
        else:
            if st.button("🚀 Start Live Map Extraction", use_container_width=True):
                if input_keyword:
                    st.session_state.is_scraping = True
                    st.rerun()
                else:
                    st.error("⚠️ Please enter a search keyword.")
    
    st.write("")
    
    # 2-2. History Zone
    with st.container(border=True):
        st.subheader("📂 Collection History")
        st.write("")
        existing_keywords = db.fetch_all_keywords()
        if existing_keywords:
            selected_keyword = st.selectbox(
                "Select a keyword project", 
                options=existing_keywords,
                label_visibility="collapsed"
            )
            st.write("")
            if st.button("🗑️ Delete Selected Data", use_container_width=True):
                deleted_count = db.delete_by_keyword(selected_keyword)
                st.success(f"'{selected_keyword}' data ({deleted_count} rows) deleted.")
                st.rerun()
        else:
            st.info("No collection history found.")
            selected_keyword = None

# 3. Right Column (Data Table)
with col_right:
    with st.container(border=True):
        st.subheader("📊 Extracted Data Management Table")
        st.write("")
        if existing_keywords and selected_keyword:
            raw_data = db.fetch_by_keyword(selected_keyword)
            # Map DB columns to English display names
            df = pd.DataFrame(raw_data, columns=["Business Name", "Address", "Phone", "Website", "Rating"])
            
            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Leads", f"{len(df)}")
            c2.metric("With Phone", f"{len(df[df['Phone'] != 'N/A'])}")
            c3.metric("With Website", f"{len(df[df['Website'] != ''])}")
            
            st.divider()
            
            # Data Table (All fields visible with fluid width)
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True, 
                height=520,
                column_config={
                    "Business Name": st.column_config.TextColumn("Business Name", width="small"),
                    "Address": st.column_config.TextColumn("Address", width="medium"),
                    "Phone": st.column_config.TextColumn("Phone", width="small"),
                    "Website": st.column_config.LinkColumn("Website", width="medium"),
                    "Rating": st.column_config.NumberColumn("Rating", format="%.1f ⭐", width="small"),
                }
            )
            
            st.write("")
            csv_bytes = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"📥 Download Data for [{selected_keyword}] (CSV)", 
                data=csv_bytes, 
                file_name=f"{selected_keyword}_leads.csv", 
                mime="text/csv", 
                use_container_width=True
            )
        else:
            st.info("Select a keyword from the 'Collection History' to view data.")

# ================= [Scraper Execution Logic] =================
if st.session_state.is_scraping:
    try:
        with st.spinner(f"Collecting data for '{input_keyword}'..."):
            scraper = YandexMapScraper(keyword=input_keyword, scroll_count=input_scroll)
            scraper.start_sync()
        st.success("💡 Data collection completed successfully!")
    except Exception as e:
        st.error(f"❌ Error occurred: {e}")
    finally:
        st.session_state.is_scraping = False
        st.rerun()