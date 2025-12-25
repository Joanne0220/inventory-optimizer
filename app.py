import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------------------------------------
# 1. Page Config & Title
# ---------------------------------------------------------
st.set_page_config(page_title="Inventory Manager", layout="wide")
st.title("🛒 Sales Data Analysis & Inventory Optimization App (Universal Adapter)")

# ---------------------------------------------------------
# 2. Data Loading & Processing (Cached)
# ---------------------------------------------------------
@st.cache_data
def load_and_process_data(file):
    # Read data
    try:
        df = pd.read_csv(file)
    except Exception:
        # Try reading as Excel just in case
        df = pd.read_excel(file)
    
    # --- Key Modification: Column Name Adapter ---
    # Strip whitespace and convert to Title Case
    df.columns = [c.strip().title() for c in df.columns]
    
    # Define column mapping: { "Your Excel Column": "Required Column" }
    # Adapts to the "Supermarket Sales" dataset you uploaded
    column_mapping = {
        'Branch': 'Store',
        'Product Line': 'Dept',
        'Total': 'Weekly_Sales',
        'Sales': 'Weekly_Sales'  # Fallback
    }
    
    # Rename columns based on mapping
    df = df.rename(columns=column_mapping)
    
    # Check for required columns again
    required_columns = ['Store', 'Dept', 'Date', 'Weekly_Sales']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        st.error(f"Cannot recognize data format. Missing columns (or unable to map): {missing_cols}")
        st.info(f"Columns found: {list(df.columns)}")
        st.markdown("Please ensure the file contains `Store/Branch`, `Dept/Product line`, `Weekly_Sales/Total`, `Date`.")
        return None

    # Convert Date format
    df['Date'] = pd.to_datetime(df['Date'])
    
    # --- Core Logic: Generate SKU ---
    # Format: "Store {Store} - Dept {Dept}"
    df['SKU'] = "Store " + df['Store'].astype(str) + " - Dept " + df['Dept'].astype(str)
    
    # --- Core Logic: Simulate Unit Price ---
    # Logic: Generate a fixed random price ($10 - $100) for each Dept.
    # Use index of unique departments as seed to handle string names (like 'Health and beauty')
    unique_depts = df['Dept'].unique()
    price
