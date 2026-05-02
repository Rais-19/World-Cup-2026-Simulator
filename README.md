---
title: WC 2026 Tournament Simulator
emoji: 🏆
colorFrom: green
colorTo: yellow
sdk: streamlit
sdk_version: 1.32.0
app_file: frontend/frontendapp.py
pinned: false
---


> **AI-powered World Cup 2026 prediction engine | 5,000 Monte Carlo simulations | 49,287 historical matches | 4 ML models**

[**🚀 Launch Live Demo**]https://world-cup-2026-simulator-wrgtnp3tssymfinyyzxuvh.streamlit.app/| [**📊 View Full Report**](./WC2026_Full_Technical_Report.pdf) |

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Live Demo](#-live-demo)
- [Technical Stack](#-technical-stack)
- [Results](#-results)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Deployment](#-deployment)
- [Reports](#-reports)
- [Future Work](#-future-work)
- [Author](#-author)
- [License](#-license)

---

##  Overview

The **WC 2026 Tournament Simulator** is a full-stack data science project that predicts the outcomes of the 2026 FIFA World Cup. It combines:

- 📊 **49,287 historical matches** (1916–2024)
- 🤖 **4 machine learning models** (Random Forest + Poisson Regression)
- 🎲 **5,000 Monte Carlo simulations** of the full tournament
- 🌐 **Interactive Streamlit web application** for exploring predictions

**Predicted Champion: Spain (12–15%)** | **Most Likely Final: Spain vs Argentina**

---

##  Key Features

| Feature | Description |
|---------|-------------|
| 🏆 **Champion Probabilities** | Top 15 most likely champions with 95% confidence intervals |
| 📊 **Group Stage Analysis** | Position probabilities for all 12 groups + "Group of Death" detection |
| 🥅 **Knockout Bracket** | Most likely path from Round of 32 to Final |
| 🔍 **Matchup Predictor** | Head-to-head probabilities for any 2 of 48 teams |
| 🎲 **Alternate Realities** | 6 scenarios (Upsets, European Dominance, etc.) with strength slider |
| 🏟️ **Interactive Bracket** | Pick your own winners — bracket cascades automatically |
| 📈 **Team Stats** | Elo ratings, FIFA ranks, stage survival curves |

---

##  Live Demo

| Platform | Link |
|----------|------|
| **Streamlit Cloud** | https://world-cup-2026-simulator-wrgtnp3tssymfinyyzxuvh.streamlit.app/ |
| **GitHub Repository** |https://github.com/Rais-19/World-Cup-2026-Simulator |

---

## 🛠️ Technical Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Processing** | Python, Pandas, NumPy | ETL, cleaning, feature engineering |
| **Machine Learning** | Scikit-learn, Random Forest, Poisson | Match prediction, goals, penalties |
| **Simulation Engine** | Monte Carlo, NumPy Poisson | 5,000 full tournament iterations |
| **Web Application** | Streamlit | 7-page interactive dashboard |
| **Deployment** | Hugging Face Spaces | Always-on public link, zero cold starts |
| **Version Control** | GitHub | Source code & CSV data hosting |

---

##  Results

### Top 10 Most Likely Champions

| Rank | Team | Champion % | Finalist % | Semi-Final % |
|------|------|------------|------------|--------------|
| 1 | 🇪🇸 Spain | **12–15%** | 22–26% | 38–42% |
| 2 | 🇦🇷 Argentina | **11–13%** | 21–25% | 36–40% |
| 3 | 🇫🇷 France | **10–12%** | 19–23% | 34–38% |
| 4 | 🇧🇷 Brazil | **8–10%** | 16–20% | 30–34% |
| 5 | EN England | **7–9%** | 14–18% | 27–31% |
| 6 | 🇩🇪 Germany | **6–8%** | 12–16% | 24–28% |
| 7 | 🇳🇱 Netherlands | **5–7%** | 11–14% | 21–25% |
| 8 | 🇵🇹 Portugal | **4–6%** | 9–12% | 18–22% |
| 9 | 🇧🇪 Belgium | **3–5%** | 7–10% | 15–19% |
| 10 | 🇨🇴 Colombia | **2–4%** | 5–8% | 12–16% |

### Key Discoveries

1. **No team dominates** — Spain wins only 1 in 7 simulations
2. **Elo difference** is 3x more important than recent form
3. **Morocco** upsets top-10 teams ~35% of the time
4. **Colombia** is the tournament's biggest dark horse
5. **Penalty shootouts** are nearly a coin flip (57% prediction accuracy)

---

##  Project Structure
WC2026Simulation/
│
├── frontend/ # Streamlit UI (MAIN for deployment)
│ ├── frontendapp.py # 7-page dashboard (entry point)
│ ├── bracket_page.py # Interactive user bracket
│ └── scenarios_page.py # Alternate reality simulator
│
├── services/ # Backend logic
│ ├── bracket_service.py # Bracket builder, cascade logic
│ ├── prediction_service.py # ML model loading + inference
│ └── results_service.py # CSV data loading + queries
│
├── config/
│ └── tournament_config.py # Groups, FIFA ranks, bracket pairings
│
├── data/ # All simulation outputs
│ ├── champion_probabilities.csv
│ ├── group_stage_summary.csv
│ ├── knockout_bracket.csv
│ ├── matchup_probabilities.csv
│ └── ...
│
├── models/ # Trained ML models (.pkl)
│ ├── match_model.pkl # Random Forest (match outcome)
│ ├── home_goals_model.pkl # Poisson (home xG)
│ ├── away_goals_model.pkl # Poisson (away xG)
│ └── ...
│
├── requirements.txt # Python dependencies
├── README.md 
├── .gitignore
└── WC2026_Full_Technical_Report.pdf 



Available Pages
🏆 Champion Probabilities — View top 15 most likely champions

📊 Group Stage — Analyze group standings and competitiveness

🥅 Knockout Bracket — See the most likely path to the Final

🔍 Matchup Predictor — Compare any two teams head-to-head

🎲 Alternate Realities — Simulate different tournament scenarios

🏟️ Interactive Bracket — Make your own picks and see them cascade

📈 Team Stats — Explore Elo ratings and stage survival curves

🌐 Deployment
The app is deployed on StreamlitCloud: 

URL: https://world-cup-2026-simulator-wrgtnp3tssymfinyyzxuvh.streamlit.app/
