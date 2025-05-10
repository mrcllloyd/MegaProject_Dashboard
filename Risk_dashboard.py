import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from io import BytesIO
import tempfile

# Load datasets
@st.cache_data
def load_data():
    player_info = pd.read_csv("player_info.csv")
    usage = pd.read_csv("sp1_dw_aggr.csv")

    usage['playerid'] = usage['playerid'].astype(str)
    usage['reportdate'] = pd.to_datetime(usage['date_time'])
    usage['wageramount'] = usage['total_bet']
    usage['holdamount'] = usage['total_bet'] - usage['total_win']
    usage['wagernum'] = usage['txn_count']

    player_info['player_id'] = player_info['player_id'].astype(str)
    merged = usage.merge(player_info, left_on='playerid', right_on='player_id', how='left')
    merged['occupation'] = merged['nature_of_work']

    def classify_risk(row):
        if row['wageramount'] < 5000:
            return "GO (Normal)"
        elif row['wageramount'] < 25000:
            return "LOOK (At Risk)"
        elif row['wageramount'] < 100000:
            return "ACT (Pathological)"
        else:
            return "STOP (Exclude)"

    merged['risk_level'] = merged.apply(classify_risk, axis=1)
    return merged

merged_df = load_data()

# Sidebar
st.sidebar.title("Filters")
date_range = st.sidebar.date_input("Date Range", [merged_df['reportdate'].min(), merged_df['reportdate'].max()])
sp_options = ['All'] + sorted(merged_df['SP_NAME'].dropna().unique().tolist())
selected_sp = st.sidebar.selectbox("Select SP_NAME", sp_options)

start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
filtered = merged_df[(merged_df['reportdate'] >= start_date) & (merged_df['reportdate'] <= end_date)]
if selected_sp != 'All':
    filtered = filtered[filtered['SP_NAME'] == selected_sp]

# Granularity
days_range = (end_date - start_date).days
if days_range <= 7:
    granularity = 'Daily'
    filtered['period'] = filtered['reportdate'].dt.date
elif days_range <= 60:
    granularity = 'Weekly'
    filtered['period'] = filtered['reportdate'].dt.to_period("W").dt.start_time
elif days_range <= 365:
    granularity = 'Monthly'
    filtered['period'] = filtered['reportdate'].dt.to_period("M").dt.start_time
else:
    granularity = 'Yearly'
    filtered['period'] = filtered['reportdate'].dt.to_period("Y").dt.start_time

# Header
st.title(" Player Risk Dashboard")
st.write(f" Date Range: {start_date.date()} to {end_date.date()}  |  SP_NAME: {selected_sp}  |  Granularity: {granularity}")

# Time Series Summary
summary = filtered.groupby('period').agg(
    total_players=('playerid', 'nunique'),
    total_wager=('wageramount', 'sum'),
    total_hold=('holdamount', 'sum')
).reset_index()

st.subheader(f" Wager Trend Over Time for {selected_sp}")
st.line_chart(summary.set_index('period')['total_wager'])

# Player Risk Flags
player_metrics = filtered.groupby(['playerid', 'occupation']).agg(
    total_sessions=('wagernum', 'sum'),
    total_wager=('wageramount', 'sum'),
    avg_bet=('wageramount', 'mean'),
    max_single_bet=('wageramount', 'max'),
    wager_days=('reportdate', 'nunique')
).reset_index()

player_metrics['avg_wager_per_day'] = player_metrics['total_wager'] / player_metrics['wager_days']
player_metrics['big_bet_flag'] = player_metrics['max_single_bet'] >= 100000
player_metrics['high_freq_flag'] = player_metrics['total_sessions'] >= 50
player_metrics['daily_spike_flag'] = player_metrics['avg_wager_per_day'] >= 20000

flag_summary = player_metrics.groupby('occupation')[['big_bet_flag', 'high_freq_flag', 'daily_spike_flag']].sum()

st.subheader(" Risk Flags by Occupation")
if not flag_summary.empty:
    st.bar_chart(flag_summary)

# Risk Level Summary
risk_summary = filtered.groupby('risk_level').agg(
    unique_players=('playerid', 'nunique'),
    total_wager=('wageramount', 'sum'),
    total_hold=('holdamount', 'sum')
).reset_index()

st.subheader(" Risk Level Distribution")
st.dataframe(risk_summary)
st.bar_chart(filtered['risk_level'].value_counts())

# Top Players
st.subheader(f" Top 10 Players by Wager for {selected_sp}")
top_players = filtered.sort_values(by='wageramount', ascending=False).head(10)[[
    'playerid', 'gamename', 'wageramount', 'holdamount', 'risk_level', 'occupation'
]]
st.dataframe(top_players)

# PDF Export with Charts
def create_charts():
    temp_files = {}

    # Chart 1: Wager Trend
    fig1, ax1 = plt.subplots()
    ax1.plot(summary['period'], summary['total_wager'], marker='o')
    ax1.set_title("Wager Trend Over Time")
    ax1.set_ylabel("Total Wager")
    fig1.tight_layout()
    temp1 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig1.savefig(temp1.name)
    temp_files['trend'] = temp1.name

    # Chart 2: Risk Level Distribution
    fig2, ax2 = plt.subplots()
    sns.countplot(data=filtered, x='risk_level', ax=ax2)
    ax2.set_title("Player Count by Risk Level")
    fig2.tight_layout()
    temp2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig2.savefig(temp2.name)
    temp_files['risk'] = temp2.name

    # Chart 3: Risk Flags (optional if empty)
    if not flag_summary.empty:
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        flag_summary.plot(kind='bar', stacked=True, ax=ax3)
        ax3.set_title("Risk Flags by Occupation")
        fig3.tight_layout()
        temp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig3.savefig(temp3.name)
        temp_files['flags'] = temp3.name

    return temp_files

def create_pdf_with_charts():
    charts = create_charts()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Player Risk Dashboard for {selected_sp}", ln=True, align="C")
    pdf.ln(10)

    for idx, row in risk_summary.iterrows():
        line = f"{row['risk_level']}: {row['unique_players']} players | Wager: ₱{row['total_wager']:.2f}"
        pdf.cell(200, 10, txt=line, ln=True)

    for title, path in charts.items():
        pdf.add_page()
        pdf.image(path, x=10, y=20, w=190)

    binary_pdf = pdf.output(dest='S').encode('latin-1')
    return BytesIO(binary_pdf)

if st.button(" Download Full Dashboard (PDF)"):
    pdf_file = create_pdf_with_charts()
    st.download_button(label="Download Dashboard as PDF",
                       data=pdf_file,
                       file_name=f"risk_dashboard_{selected_sp}.pdf",
                       mime="application/pdf")
