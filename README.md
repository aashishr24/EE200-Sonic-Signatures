# EE200 - ML Model Streamlit UI

A simple yet powerful Streamlit web application for training and testing machine learning models.

## Features

✨ **Two Modes:**
- **Demo Mode**: Train models on built-in datasets (Iris for classification, Diabetes for regression)
- **Upload Mode**: Upload your own CSV data and train custom models

🤖 **Supported Models:**
- Classification: Logistic Regression, Random Forest
- Regression: Linear Regression, Random Forest

📊 **Visualizations:**
- Confusion matrices for classification
- Prediction vs. actual plots for regression
- Performance metrics and classification reports

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:
```bash
streamlit run ss.py
```

The app will open at `http://localhost:8501`

### Demo Mode
- Select a dataset (Iris or Diabetes)
- Choose a model
- Adjust test size slider
- Click "Train Model" to train and see results

### Upload Mode
- Upload a CSV file
- Select feature columns and target column
- Choose task type (Classification/Regression)
- Select a model
- Click "Train Model" to train on your data

## Requirements

- Python 3.8+
- See requirements.txt for all dependencies

## License

MIT