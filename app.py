import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

# Set page config
st.set_page_config(
    page_title="Loyalty Points Calculator",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {padding: 2rem;}
    .stButton>button {background-color: #4CAF50; color: white;}
    .stDownloadButton>button {background-color: #2196F3; color: white;}
    .stFileUploader>div>div>div>div {color: #FF5722;}
    .metric-box {padding: 15px; border-radius: 10px; background: #f0f2f6; margin: 10px 0;}
    .sidebar .sidebar-content {background: #f8f9fa;}
    .param-box {border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

# App title and description
st.title("🎮 Player Loyalty Points Calculator")
st.markdown("""
Analyze player activity data to calculate loyalty points and allocate bonuses to top performers.
Upload your data files or use sample data to get started.
""")

# ==============================================
# SAMPLE DATA LOADING
# ==============================================

def load_sample_data():
    """Create sample dataframes for demonstration"""
    # Sample deposit data
    deposit_data = {
        'User Id': [101, 101, 102, 103, 104, 105, 101, 106, 102, 107],
        'Amount': [5000, 3000, 7000, 2000, 10000, 4000, 6000, 8000, 3000, 5000],
        'Datetime': [
            '01-10-2022 10:00', '05-10-2022 15:30', '02-10-2022 11:15',
            '03-10-2022 09:45', '10-10-2022 14:00', '15-10-2022 16:30',
            '20-10-2022 10:45', '25-10-2022 13:15', '28-10-2022 17:30', '30-10-2022 18:00'
        ]
    }
    
    # Sample withdrawal data
    withdrawal_data = {
        'User Id': [101, 102, 103, 104, 105, 101, 106, 107],
        'Amount': [2000, 3000, 1000, 5000, 2000, 1000, 4000, 2000],
        'Datetime': [
            '08-10-2022 11:00', '12-10-2022 14:30', '14-10-2022 10:15',
            '18-10-2022 16:45', '22-10-2022 12:00', '25-10-2022 09:30',
            '27-10-2022 15:15', '29-10-2022 17:00'
        ]
    }
    
    # Sample gameplay data
    gameplay_data = {
        'User Id': [101, 101, 102, 103, 104, 105, 106, 107, 101, 102, 103, 104, 105, 106, 107],
        'Games Played': [15, 20, 30, 10, 25, 18, 22, 12, 25, 35, 15, 30, 20, 28, 18],
        'Datetime': [
            '01-10-2022 10:30', '02-10-2022 11:00', '03-10-2022 09:30',
            '04-10-2022 14:00', '05-10-2022 16:30', '06-10-2022 12:45',
            '07-10-2022 10:15', '08-10-2022 15:30', '09-10-2022 11:00',
            '10-10-2022 14:30', '11-10-2022 09:00', '12-10-2022 16:00',
            '13-10-2022 13:45', '14-10-2022 10:30', '15-10-2022 17:00'
        ]
    }
    
    return (
        pd.DataFrame(deposit_data),
        pd.DataFrame(withdrawal_data),
        pd.DataFrame(gameplay_data)
    )

# ==============================================
# SIDEBAR - FILE UPLOAD AND PARAMETERS
# ==============================================

with st.sidebar:
    st.header("📁 Data Source")
    
    # Data source selection
    data_source = st.radio(
        "Choose data source:",
        ["Upload your own files", "Use sample data"],
        index=0
    )
    
    if data_source == "Upload your own files":
        # File uploaders
        deposit_file = st.file_uploader("Deposit Data (CSV)", type=["csv"])
        withdrawal_file = st.file_uploader("Withdrawal Data (CSV)", type=["csv"])
        gameplay_file = st.file_uploader("Gameplay Data (CSV)", type=["csv"])
    else:
        deposit_file, withdrawal_file, gameplay_file = None, None, None
        st.success("Sample data will be used for demonstration")
    
    st.markdown("---")
    st.header("⚙️ Settings")
    month_to_analyze = st.selectbox(
        "Select Month to Analyze",
        ["October 2022", "November 2022", "December 2022"],
        index=0
    )
    
    bonus_pool = st.number_input(
        "Bonus Pool Amount (₹)", 
        min_value=1000, 
        max_value=1000000, 
        value=50000
    )
    
    st.markdown("---")
    st.header("🧮 Points Parameters")
    
    with st.expander("Configure Points Calculation"):
        st.markdown("**Deposit Parameters**")
        deposit_multiplier = st.slider(
            "Deposit Multiplier (per ₹)", 
            min_value=0.0, 
            max_value=0.1, 
            value=0.01, 
            step=0.001,
            format="%.3f"
        )
        
        st.markdown("**Withdrawal Parameters**")
        withdrawal_multiplier = st.slider(
            "Withdrawal Multiplier (per ₹)", 
            min_value=-0.01, 
            max_value=0.01, 
            value=0.005, 
            step=0.001,
            format="%.3f"
        )
        
        st.markdown("**Frequency Parameters**")
        frequency_multiplier = st.slider(
            "Frequency Multiplier (per net deposit)", 
            min_value=0.0, 
            max_value=0.01, 
            value=0.001, 
            step=0.0001,
            format="%.4f"
        )
        
        st.markdown("**Gameplay Parameters**")
        gameplay_multiplier = st.slider(
            "Gameplay Multiplier (per game)", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.2, 
            step=0.01
        )
        
        daily_bonus = st.slider(
            "Daily Play Bonus (points per distinct day)", 
            min_value=0, 
            max_value=10, 
            value=0, 
            step=1
        )
        
        st.markdown("**Advanced**")
        deposit_cap = st.number_input(
            "Maximum Deposit Points", 
            min_value=0, 
            max_value=100000, 
            value=0,
            help="Set to 0 for no cap"
        )

# ==============================================
# DATA PROCESSING FUNCTIONS
# ==============================================

def load_data(file):
    """Load CSV file with error handling"""
    if file is not None:
        try:
            return pd.read_csv(file)
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return None
    return None

def process_data(df, name):
    """Process uploaded data with datetime conversion"""
    if df is None:
        return None
        
    if 'Datetime' not in df.columns:
        st.error(f"{name} data must contain a 'Datetime' column")
        return None
        
    df['Datetime'] = pd.to_datetime(df['Datetime'], format='%d-%m-%Y %H:%M', errors='coerce')
    invalid_dates = df['Datetime'].isna().sum()
    
    if invalid_dates > 0:
        st.warning(f"Removed {invalid_dates} rows with invalid dates from {name} data")
        df = df.dropna(subset=['Datetime'])
    
    return df

def calculate_loyalty_points(user_data, start_date, end_date):
    """Calculate loyalty points for a user in given date range"""
    points = {
        'User Id': user_data['User Id'],
        'Total Points': 0,
        'From Deposits': 0,
        'From Withdrawals': 0,
        'From Frequency': 0,
        'From Games': 0,
        'From Daily Bonus': 0,
        'Total Deposits': 0,
        'Total Withdrawals': 0,
        'Games Played': 0,
        'Distinct Days': 0
    }
    
    # Filter user's activity within date range
    user_deposits = deposit[
        (deposit['User Id'] == user_data['User Id']) & 
        (deposit['Datetime'] >= start_date) & 
        (deposit['Datetime'] <= end_date)
    ]
    
    user_withdrawals = withdrawal[
        (withdrawal['User Id'] == user_data['User Id']) & 
        (withdrawal['Datetime'] >= start_date) & 
        (withdrawal['Datetime'] <= end_date)
    ]
    
    user_games = gameplays[
        (gameplays['User Id'] == user_data['User Id']) & 
        (gameplays['Datetime'] >= start_date) & 
        (gameplays['Datetime'] <= end_date)
    ]
    
    # Calculate components
    deposit_amt = user_deposits['Amount'].sum()
    withdrawal_amt = user_withdrawals['Amount'].sum()
    num_deposits = len(user_deposits)
    num_withdrawals = len(user_withdrawals)
    games_played = user_games['Games Played'].sum()
    
    # Calculate distinct days played
    distinct_days = len(user_games['Datetime'].dt.normalize().unique())
    
    # Calculate points components
    deposit_points = deposit_multiplier * deposit_amt
    if deposit_cap > 0:
        deposit_points = min(deposit_points, deposit_cap)
    
    withdrawal_points = withdrawal_multiplier * withdrawal_amt
    frequency_points = frequency_multiplier * max(num_deposits - num_withdrawals, 0)
    game_points = gameplay_multiplier * games_played
    daily_bonus_points = daily_bonus * distinct_days
    
    total_points = (deposit_points + withdrawal_points + 
                   frequency_points + game_points + daily_bonus_points)
    
    # Update points dictionary
    points.update({
        'Total Points': total_points,
        'From Deposits': deposit_points,
        'From Withdrawals': withdrawal_points,
        'From Frequency': frequency_points,
        'From Games': game_points,
        'From Daily Bonus': daily_bonus_points,
        'Total Deposits': deposit_amt,
        'Total Withdrawals': withdrawal_amt,
        'Games Played': games_played,
        'Num Deposits': num_deposits,
        'Num Withdrawals': num_withdrawals,
        'Distinct Days': distinct_days
    })
    
    return points

# ==============================================
# MAIN APP LOGIC
# ==============================================

# Check if we should use sample data
use_sample_data = data_source == "Use sample data"

if use_sample_data or (deposit_file and withdrawal_file and gameplay_file):
    # Load and process data
    if use_sample_data:
        deposit, withdrawal, gameplays = load_sample_data()
        deposit = process_data(deposit, "Deposit")
        withdrawal = process_data(withdrawal, "Withdrawal")
        gameplays = process_data(gameplays, "Gameplay")
    else:
        deposit = process_data(load_data(deposit_file), "Deposit")
        withdrawal = process_data(load_data(withdrawal_file), "Withdrawal")
        gameplays = process_data(load_data(gameplay_file), "Gameplay")
    
    if deposit is not None and withdrawal is not None and gameplays is not None:
        # Determine month to analyze
        if month_to_analyze == "October 2022":
            start_date = datetime(2022, 10, 1)
            end_date = datetime(2022, 10, 31, 23, 59, 59)
        elif month_to_analyze == "November 2022":
            start_date = datetime(2022, 11, 1)
            end_date = datetime(2022, 11, 30, 23, 59, 59)
        else:  # December 2022
            start_date = datetime(2022, 12, 1)
            end_date = datetime(2022, 12, 31, 23, 59, 59)
        
        # Get all unique users
        all_users = pd.DataFrame({
            'User Id': list(set(deposit['User Id']).union(
                set(withdrawal['User Id'])).union(
                set(gameplays['User Id'])))
        })
        
        # Calculate loyalty points for all users
        with st.spinner("Calculating loyalty points..."):
            results = []
            for _, user in all_users.iterrows():
                results.append(calculate_loyalty_points(user, start_date, end_date))
            
            points_df = pd.DataFrame(results)
            monthly_rankings = points_df.sort_values(
                ['Total Points', 'Games Played'], 
                ascending=[False, False]
            )
            monthly_rankings['Rank'] = range(1, len(monthly_rankings)+1)
        
        # ==============================================
        # DASHBOARD DISPLAY
        # ==============================================
        
        st.success("Data processed successfully!")
        if use_sample_data:
            st.info("Currently using sample demonstration data")
        st.markdown("---")
        
        # Display current parameters
        with st.expander("Current Points Parameters"):
            st.markdown(f"""
            **Current Formula:**
            ```
            Loyalty Points = 
            ({deposit_multiplier} × Deposit Amount) + 
            ({withdrawal_multiplier} × Withdrawal Amount) + 
            ({frequency_multiplier} × max(Deposits - Withdrawals, 0)) + 
            ({gameplay_multiplier} × Games Played) + 
            ({daily_bonus} × Distinct Days Played)
            ```
            """)
            if deposit_cap > 0:
                st.markdown(f"**Deposit Points Capped at:** {deposit_cap}")
        
        # Key Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Players", len(monthly_rankings))
        with col2:
            st.metric("Average Points", f"{monthly_rankings['Total Points'].mean():.1f}")
        with col3:
            st.metric("Top Player Points", f"{monthly_rankings.iloc[0]['Total Points']:.1f}")
        
        # Points Breakdown
        st.subheader("🔍 Points Breakdown")
        st.write("How top players earned their points:")
        top_players = monthly_rankings.head(10).copy()
        top_players['Deposit %'] = (top_players['From Deposits'] / top_players['Total Points']) * 100
        top_players['Gameplay %'] = (top_players['From Games'] / top_players['Total Points']) * 100
        top_players['Other %'] = 100 - top_players['Deposit %'] - top_players['Gameplay %']
        
        st.dataframe(
            top_players[[
                'Rank', 'User Id', 'Total Points', 
                'From Deposits', 'From Games', 'From Daily Bonus',
                'Deposit %', 'Gameplay %'
            ]].style.format({
                'Total Points': '{:.1f}',
                'From Deposits': '{:.1f}',
                'From Games': '{:.1f}',
                'From Daily Bonus': '{:.1f}',
                'Deposit %': '{:.1f}%',
                'Gameplay %': '{:.1f}%'
            }),
            height=400
        )
        
        # Bonus Allocation
        st.subheader("💰 Bonus Allocation")
        
        # Create allocation methods
        top_50 = monthly_rankings.head(50).copy()
        
        # Method 1: Proportional
        top_50['Proportional'] = (top_50['Total Points'] / top_50['Total Points'].sum()) * bonus_pool
        
        # Method 2: Tiered
        top_50['Tiered'] = 0
        top_50.loc[top_50['Rank'] <= 10, 'Tiered'] = bonus_pool * 0.3 / 10  # Top 10 get 30% of pool
        top_50.loc[(top_50['Rank'] > 10) & (top_50['Rank'] <= 30), 'Tiered'] = bonus_pool * 0.4 / 20  # Next 20 get 40%
        top_50.loc[top_50['Rank'] > 30, 'Tiered'] = bonus_pool * 0.3 / 20  # Last 20 get 30%
        
        # Method 3: Hybrid
        points_weight = 0.5
        games_weight = 0.3
        deposit_weight = 0.2
        
        top_50['Hybrid'] = (
            (points_weight * top_50['Total Points'] / top_50['Total Points'].sum()) +
            (games_weight * top_50['Games Played'] / top_50['Games Played'].sum()) +
            (deposit_weight * top_50['Total Deposits'] / top_50['Total Deposits'].sum())
        ) * bonus_pool
        
        # Display allocation comparison
        st.write("Comparison of bonus allocation methods:")
        allocation_comparison = top_50.head(10)[[
            'Rank', 'User Id', 'Total Points', 
            'Proportional', 'Tiered', 'Hybrid'
        ]].rename(columns={
            'Proportional': 'Proportional (₹)',
            'Tiered': 'Tiered (₹)',
            'Hybrid': 'Hybrid (₹)'
        })
        
        st.dataframe(
            allocation_comparison.style.format({
                'Total Points': '{:.1f}',
                'Proportional (₹)': '₹{:.2f}',
                'Tiered (₹)': '₹{:.2f}',
                'Hybrid (₹)': '₹{:.2f}'
            }),
            height=400
        )
        
        # Visualization
        st.subheader("📊 Loyalty Points Distribution")
        tab1, tab2, tab3 = st.tabs(["By Points", "By Games", "By Deposits"])
        
        with tab1:
            st.bar_chart(monthly_rankings.head(20), x='User Id', y='Total Points')
        with tab2:
            st.bar_chart(monthly_rankings.head(20), x='User Id', y='Games Played')
        with tab3:
            st.bar_chart(monthly_rankings.head(20), x='User Id', y='Total Deposits')
        
        # Download buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="Download Full Rankings (CSV)",
                data=monthly_rankings.to_csv(index=False).encode('utf-8'),
                file_name=f"loyalty_rankings_{month_to_analyze.replace(' ', '_')}.csv",
                mime='text/csv'
            )
        
        with col2:
            st.download_button(
                label="Download Bonus Allocation (CSV)",
                data=top_50.to_csv(index=False).encode('utf-8'),
                file_name=f"bonus_allocation_{month_to_analyze.replace(' ', '_')}.csv",
                mime='text/csv'
            )
        
else:
    st.warning("Please upload all three data files or select sample data to proceed")
    st.markdown("""
    **Sample Data Format:**
    - All files should contain a 'User Id' column
    - Deposit/Withdrawal files need 'Amount' column
    - Gameplay file needs 'Games Played' column
    - All need 'Datetime' column in format DD-MM-YYYY HH:MM
    """)

# Add footer
st.markdown("---")
st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: white;
    color: black;
    text-align: center;
}
</style>
<div class="footer">
<p>Loyalty Points Calculator | Made with Streamlit</p>
</div>
""", unsafe_allow_html=True)