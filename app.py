import streamlit as st
import pandas as pd
import plotly.express as px

# 1. DATU IELĀDE (Izmantojam tavu jauno final_data_for_app.csv)
@st.cache_data
def load_final_data():
    # Šis fails tagad satur visus nepieciešamos aprēķinus no Colab
    df = pd.read_csv('final_data_for_app.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Product_Category'] = df['Product_Category'].str.strip().str.title()
    return df

# Mēģinām ielādēt datus
try:
    df = load_final_data()
except Exception as e:
    st.error(f"Kļūda ielādējot final_data_for_app.csv: {e}")
    st.stop()

# --- 2. SIDEBAR FILTRI ---
st.sidebar.header("📊 Filtri")
categories = st.sidebar.multiselect(
    "Izvēlies kategorijas:",
    options=df['Product_Category'].unique(),
    default=df['Product_Category'].unique()
)

# Filtra datumu robežas
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

date_range = st.sidebar.date_input(
    "Laika periods:",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filtrējam datus (drošības pārbaude datumu diapazonam)
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['Product_Category'].isin(categories)) & \
           (df['Date'].dt.date >= start_date) & \
           (df['Date'].dt.date <= end_date)
    filtered_df = df[mask]
else:
    filtered_df = df[df['Product_Category'].isin(categories)]

# --- 3. KPI RINDAS ---
st.title("🚀 Operatīvās situācijas pārskats")
col1, col2, col3 = st.columns(3)

total_rev = filtered_df['Net_Revenue'].sum()
refund_total = filtered_df['Refund_Amount'].sum()
refund_rate = (refund_total / total_rev * 100) if total_rev > 0 else 0

col1.metric("Kopējie Neto Ieņēmumi", f"{total_rev:,.2f} €")
col2.metric("Atgrieztā Summa", f"{refund_total:,.2f} €", delta=f"{refund_rate:.1f}% no ieņ.")
col3.metric("Sūdzību skaits (pēc 15.12.)", "110") 

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





