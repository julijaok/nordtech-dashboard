import streamlit as st
import pandas as pd
import plotly.express as px

# 1. DATU IELĀDE (Aizstāj ar savu faila nosaukumu)
# Šeit lietotne nolasa datus no diska
@st.cache_data # Šis paātrina lietotni
def load_data():
    # Ja tavs apvienotais fails ir saglabāts kā 'final_data.csv'
    df = pd.read_csv('final_data.csv') 
    df['Date'] = pd.to_datetime(df['Date'])
    df['Product_Category'] = df['Product_Category'].str.strip().str.title()
    return df

# Mēģinām ielādēt datus
try:
    df = load_data()
except FileNotFoundError:
    st.error("Kļūda: Fails 'final_data.csv' netika atrasts! Lūdzu, saglabā savu merged_data tabulu kā CSV failu.")
    st.stop()

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
