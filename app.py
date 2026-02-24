import streamlit as st
import pandas as pd
import plotly.express as px

# 1. DATU APSTRĀDE (Lai nebūtu jāizmanto gatavs CSV)
@st.cache_data
def get_clean_data():
    # 1. Ielādējam datus
    orders = pd.read_csv('orders_raw.csv')
    returns = pd.read_excel('returns_messy.xlsx')
    
    # DROŠĪBAS SOLIS: Notīrām kolonnu nosaukumus no atstarpēm
    orders.columns = orders.columns.str.strip()
    returns.columns = returns.columns.str.strip()
    
    # 2. Piespiežam ID būt par tekstu
    orders['Transaction_ID'] = orders['Transaction_ID'].astype(str).str.strip()
    returns['Original_Tx_ID'] = returns['Original_Tx_ID'].astype(str).str.strip()
    
    # 3. Datuma formāta sakārtošana (atrisina iepriekšējo kļūdu)
    orders['Date'] = pd.to_datetime(orders['Date'], dayfirst=True, errors='coerce')
    
    # 4. Apvienojam datus
    df = pd.merge(orders, returns, left_on='Transaction_ID', right_on='Original_Tx_ID', how='left')
    
    # 5. Pārbaudām, kura kolonna satur ieņēmumus (Total_Revenue vai Revenue)
    rev_col = 'Total_Revenue' if 'Total_Revenue' in df.columns else 'Revenue'
    
    # 6. Tīrīšana un aprēķini
    df['Product_Category'] = df['Product_Category'].str.strip().str.title()
    df['Refund_Amount'] = df['Refund_Amount'].fillna(0)
    
    # Izmantojam atrasto ieņēmumu kolonnu
    df['Net_Revenue'] = df[rev_col] - df['Refund_Amount']
    df['is_returned'] = df['Return_ID'].notna()
    
    # Izmetam rindas bez datuma
    df = df.dropna(subset=['Date'])
    
    return df

# 2. IELĀDĒJAM UN PĀRBAUDĀM
try:
    df = get_clean_data()
except Exception as e:
    st.error(f"Datu ielādes kļūda: {e}. Pārliecinies, ka GitHub mapē ir 'orders_raw.csv' un 'returns_messy.xlsx'!")
    st.stop()

# Tālāk seko tava vizualizāciju un KPI sadaļa...

# --- 2. SIDEBAR FILTRI ---
st.sidebar.header("📊 Filtri")
categories = st.sidebar.multiselect(
    "Izvēlies kategorijas:",
    options=df['Product_Category'].unique(),
    default=df['Product_Category'].unique()
)

date_range = st.sidebar.date_input(
    "Laika periods:",
    [df['Date'].min(), df['Date'].max()]
)

# Filtrējam datus
mask = (df['Product_Category'].isin(categories)) & \
       (df['Date'] >= pd.Timestamp(date_range[0])) & \
       (df['Date'] <= pd.Timestamp(date_range[1]))
filtered_df = df[mask]

# --- 3. KPI RINDAS ---
st.title("🚀 Operatīvās situācijas pārskats")
col1, col2, col3 = st.columns(3)

total_rev = filtered_df['Net_Revenue'].sum()
refund_total = filtered_df['Refund_Amount'].sum()
# Aprēķinām atgriezumu % pret ieņēmumiem
refund_rate = (refund_total / total_rev * 100) if total_rev > 0 else 0

col1.metric("Kopējie Neto Ieņēmumi", f"{total_rev:,.2f} €")
col2.metric("Atgrieztā Summa", f"{refund_total:,.2f} €", delta=f"{refund_rate:.1f}% no ieņ.")
col3.metric("Sūdzību skaits (pēc 15.12.)", "110") # Fiksēts cipars no mūsu analīzes

st.markdown("---")

# --- 4. VIZUĀĻI ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Ieņēmumu un atgriešanu dinamika")
    daily_stats = filtered_df.groupby('Date').agg({'Net_Revenue':'sum', 'Refund_Amount':'sum'}).reset_index()
    fig_line = px.line(daily_stats, x='Date', y=['Net_Revenue', 'Refund_Amount'], 
                      color_discrete_map={'Net_Revenue': 'green', 'Refund_Amount': 'red'})
    st.plotly_chart(fig_line, use_container_width=True)

with row1_col2:
    st.subheader("Zaudējumu struktūra (Sunburst)")
    # Izmantojam agregētu tabulu, lai nav saskaldīts
    sun_df = filtered_df[filtered_df['is_returned'] == True].groupby(['Product_Category', 'Product_Name'])['Refund_Amount'].sum().reset_index()
    sun_df = sun_df[sun_df['Refund_Amount'] > 0]
    fig_sun = px.sunburst(sun_df, path=['Product_Category', 'Product_Name'], values='Refund_Amount',
                         color='Product_Category', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_sun, use_container_width=True)

# --- 5. DATU TABULA ---
st.subheader("⚠️ Top problēmprodukti (Pēc atgriešanas summas)")
top_returns = filtered_df[filtered_df['is_returned'] == True].groupby('Product_Name').agg({
    'Refund_Amount': 'sum',
    'Transaction_ID': 'count'
}).rename(columns={'Transaction_ID': 'Atgriešanu skaits'}).sort_values(by='Refund_Amount', ascending=False)


st.dataframe(top_returns.style.format({'Refund_Amount': '{:.2f} €'}), use_container_width=True)




