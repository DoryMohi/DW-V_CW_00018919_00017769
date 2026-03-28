# DW-V_CW_00018919_00017769
📊 PrepWise - Data Wrangling & Visualization App (Streamlit)

An interactive data cleaning, transformation, visualization, and insight generation tool built with Streamlit.

This application allows users to upload datasets, clean and transform data, build visualizations, generate insights, and export results — all in a structured multi-page workflow.

🚀 Features

📁 1. Upload & Overview
	•	Upload CSV datasets
	•	Quick dataset preview
	•	Basic structure inspection

🧹 2. Cleaning Studio
	•	Handle missing values
	•	Convert data types (numeric, categorical, datetime)
	•	Smart parsing for messy data
	•	Feature engineering (custom columns, transformations)

📊 3. Visualization Builder
	•	Multiple chart types:
	•	Histogram
	•	Boxplot
	•	Scatter
	•	Line (with smart time handling)
	•	Bar
	•	Heatmap
	•	Dynamic filtering (categorical, numeric, date)
	•	Automatic time aggregation (month/year logic)
	•	Clean, styled plots with legends and annotations

🧠 4. Insights & Export Dashboard
	•	Dataset overview (rows, columns, missing, duplicates)
	•	Smart statistical insights (mean, median, std, variability)
	•	Categorical analysis (distribution + dominance detection)
	•	Grouped analysis (category vs numeric metrics)
	•	Correlation heatmap with interpretation
	•	Data preview
	•	Export options:
	•	CSV
	•	Excel
	•	JSON
	•	Transformation report generation

🗂 Project Structure 
├── Home.py
├── pages/
│   ├── 1_Upload_overview.py
│   ├── 2_Cleaning_studio.py
│   ├── 3_Visualization_builder.py
│   └── 4_Insights_export.py
│
├── cleaning_core.py
├── feature_engineering.py
├── prepare_dataset.py
├── utils.py
│
├── sample_data/
│   ├── flights_dataset.csv
│   ├── global_ecommerce_sales.csv
│   ├── Healthcare_dataset_main2.csv
│   └── shopping_trends_updated_*.csv
│
├── requirements.txt
├── README.md

⚙️ Installation
	1. Clone or download the project
	2. Navigate to project folder:

       << cd DW-V_CW_00018919_00017769

    3. Create virtual environment (if not already):

       << python3 -m venv venv

    4. Activate environment

       << source venv/bin/activate

    5. Install dependencies

       << pip install -r requirements.txt

    6. Run the app

       << streamlit run Home.py

🧩 Key Design Highlights
	•	Modular architecture (separate pages + utility modules)
	•	Session state management for data persistence
	•	Smart logic for datetime handling (auto aggregation & formatting)
	•	Automatic detection of column types
	•	User-friendly UI with guided workflow
	•	Safe export and reporting system


📌 Notes
	•	ID-like columns (e.g., Customer ID) are automatically excluded from analysis where needed
	•	Date handling adapts based on dataset size (monthly vs yearly aggregation)
	•	Feature engineering supports custom transformations like:
	•	Arithmetic operations
	•	Log transformations
	•	Mean-centered values


🎯 Purpose

This project demonstrates:
	•	Data cleaning pipelines
	•	Interactive data visualization
	•	Exploratory data analysis (EDA)
	•	Streamlit application design
	•	Practical data science workflow integration