# Player Risk Dashboard

This is a Streamlit dashboard that visualizes risk levels, wagering behavior, and player metrics for an online gaming platform.

## 📁 Folder Structure
```
your-repo/
│
├── dashboard.py            # Streamlit app source code
├── requirements.txt        # Python dependencies
├── data/
│   ├── player_info.csv     # Player profile and occupation data
│   └── sp1_dw_aggr.csv     # Aggregated player transaction data
```

## 🚀 How to Run Locally
### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### 2. Set Up a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Streamlit App
```bash
streamlit run dashboard.py
```

## 🧮 Features
- Date range filtering
- SP_NAME dropdown filtering
- Time-series trend analysis of total wagers
- Risk classification: GO, LOOK, ACT, STOP
- Risk flag summaries: big bets, high frequency, daily spikes
- Risk level distribution charts
- Top 10 players ranked by wager amount

## 🗂️ Data Description
- `player_info.csv` includes demographic and occupation info per player.
- `sp1_dw_aggr.csv` contains session-level aggregate statistics including wager amount, game name, and player ID.

## 🌐 Deployment on Streamlit Cloud
1. Push your repo to GitHub.
2. Go to [Streamlit Cloud](https://streamlit.io/cloud).
3. Click **"New App"**, select your GitHub repo.
4. Set the app file path to `dashboard.py`.
5. It will auto-install dependencies and launch the app.

## 📄 License
This project is released under the MIT License.
