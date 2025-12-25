import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------------------------------------
# 1. Page Config & Title
# ---------------------------------------------------------
st.set_page_config(page_title="Inventory Manager", layout="wide")

st.title("🛒 Sales Data Analysis & Inventory Optimization App")
st.markdown("""
<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
    <strong>Status:</strong> Universal Data Adapter Active. <br>
    Supports: <em>Walmart Kaggle Format</em> AND <em>Supermarket Sales Format</em>.
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Data Loading & Processing (The "Universal Adapter")
# ---------------------------------------------------------
@st.cache_data
def load_and_process_data(file):
    # 1. Read Data (Try CSV first, then Excel)
    try:
        df = pd.read_csv(file)
    except Exception:
        df = pd.read_excel(file)
    
    # 2. Clean Column Names (Remove spaces, Title Case)
    # e.g., "Product line " -> "Product Line"
    df.columns = [c.strip().title() for c in df.columns]
    
    # 3. Define Intelligent Mapping (Your Logic + Enhancements)
    # We map various possible names to our Standard Internal Names
    column_mapping = {
        # Standard: 'Store'
        'Branch': 'Store', 
        'Store Name': 'Store',
        
        # Standard: 'SKU' (We treat Product Line or Dept as SKU for analysis)
        'Product Line': 'SKU', 
        'Dept': 'SKU',
        'Category': 'SKU',

        # Standard: 'Quantity' (Crucial for EOQ)
        'Qty': 'Quantity',
        'Sales Qty': 'Quantity',
        
        # Standard: 'Price'
        'Unit Price': 'Price',
        'Price Per Unit': 'Price',
        
        # Standard: 'Date'
        'Invoice Date': 'Date'
    }
    
    # Apply renaming only for columns that exist
    df = df.rename(columns=column_mapping)
    
    # 4. Data Validation & Filling Gaps
    # Check Date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        st.error("❌ Critical Error: No 'Date' column found.")
        return None

    # Check Quantity (If missing, try to derive from Total / Price)
    if 'Quantity' not in df.columns:
        if 'Total' in df.columns and 'Price' in df.columns:
            df['Quantity'] = (df['Total'] / df['Price']).astype(int)
        elif 'Weekly_Sales' in df.columns:
            # Fallback for old Walmart data (Simulate Price)
            np.random.seed(42)
            df['Price'] = np.random.randint(10, 100, size=len(df))
            df['Quantity'] = (df['Weekly_Sales'] / df['Price']).astype(int)
    
    # Ensure Quantity is positive
    if 'Quantity' in df.columns:
        df = df[df['Quantity'] > 0]

    # Ensure SKU column exists
    if 'SKU' not in df.columns:
        st.error("❌ Error: Could not identify a Product/Dept column.")
        return None

    return df

# ---------------------------------------------------------
# 3. Main App Logic
# ---------------------------------------------------------

# File Uploader
uploaded_file = st.file_uploader("📂 Upload your Sales Data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Load Data using the Adapter
    df = load_and_process_data(uploaded_file)
    
    if df is not None:
        st.success(f"✅ Data Successfully Adapted! Analyzed {len(df)} transactions.")
        
        # --- Sidebar Controls ---
        st.sidebar.header("⚙️ Supply Chain Parameters")
        
        # Select SKU
        sku_list = sorted(df['SKU'].unique().astype(str))
        selected_sku = st.sidebar.selectbox("Select Product Line / Category", sku_list)
        
        # Parameters
        holding_cost = st.sidebar.slider("Holding Cost %", 0.1, 0.5, 0.2, 0.05)
        lead_time = st.sidebar.slider("Lead Time (Days)", 1, 30, 7)
        ordering_cost = st.sidebar.number_input("Fixed Ordering Cost ($)", value=50)

        # --- Calculations ---
        # Filter data for selected SKU
        sku_data = df[df['SKU'] == selected_sku].sort_values('Date')
        
        # Aggregate Daily Sales (in case of multiple orders per day)
        daily_sales = sku_data.groupby('Date')['Quantity'].sum().reset_index()
        
        if len(daily_sales) > 0:
            # Metrics
            avg_daily_demand = daily_sales['Quantity'].mean()
            if 'Price' in sku_data.columns:
                avg_price = sku_data['Price'].mean()
            else:
                avg_price = 50 # Fallback default
            
            # EOQ Calculation
            annual_demand = avg_daily_demand * 365
            eoq = np.sqrt((2 * annual_demand * ordering_cost) / (avg_price * holding_cost))
            
            # Safety Stock Calculation (Simple Formula)
            safety_stock = avg_daily_demand * lead_time * 1.65 # 95% service level
            reorder_point = (avg_daily_demand * lead_time) + safety_stock
            
            # Total Inventory Cost (Estimated)
            total_cost = (annual_demand/eoq)*ordering_cost + (eoq/2)*avg_price*holding_cost

            # --- Dashboard Display ---
            st.markdown(f"### 📊 Optimization Results: {selected_sku}")
            
            # Key Metrics Row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📦 Economical Order Qty (EOQ)", f"{int(eoq)} units", delta="Batch Size")
            col2.metric("🛡️ Safety Stock", f"{int(safety_stock)} units", delta="Buffer")
            col3.metric("⚠️ Reorder Point", f"{int(reorder_point)} units", delta="Trigger Level")
            col4.metric("💰 Est. Annual Cost", f"${int(total_cost):,}", help="Ordering + Holding Costs")

            # Charts
            tab1, tab2 = st.tabs(["📈 Demand Trend", "📋 Raw Data"])
            
            with tab1:
                fig = px.line(daily_sales, x='Date', y='Quantity', 
                              title=f'Daily Demand Velocity - {selected_sku}',
                              markers=True)
                fig.update_traces(line_color='#1f77b4')
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                st.dataframe(sku_data.head(100))
                
        else:
            st.warning("Not enough data to calculate metrics for this product.")
            
else:
    st.info("👆 Please upload a file to start.")
