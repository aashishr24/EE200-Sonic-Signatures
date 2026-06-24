import streamlit as st
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris, load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="ML Model UI", layout="wide")

st.title("🤖 Machine Learning Model Interface")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox(
    "Choose Mode:",
    ["📊 Demo with Built-in Data", "📤 Upload Your Data"]
)

# ============ DEMO MODE ============
if app_mode == "📊 Demo with Built-in Data":
    st.subheader("Demo: Built-in Datasets")
    
    col1, col2 = st.columns(2)
    
    with col1:
        dataset_type = st.radio("Select Dataset:", ["Classification (Iris)", "Regression (Diabetes)"])
    
    with col2:
        if dataset_type == "Classification (Iris)":
            model_type = st.selectbox("Select Model:", ["Logistic Regression", "Random Forest"])
        else:
            model_type = st.selectbox("Select Model:", ["Linear Regression", "Random Forest"])
    
    # Load data
    if dataset_type == "Classification (Iris)":
        data = load_iris()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = pd.Series(data.target, name="Target")
        task = "classification"
    else:
        data = load_diabetes()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = pd.Series(data.target, name="Target")
        task = "regression"
    
    st.write(f"**Dataset Shape:** {X.shape}")
    st.write("**First few rows:**")
    st.dataframe(X.head())
    
    # Split data
    test_size = st.slider("Test Size:", 0.1, 0.5, 0.2)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    
    # Scale data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    if st.button("🚀 Train Model", key="train_demo"):
        with st.spinner("Training model..."):
            if task == "classification":
                if model_type == "Logistic Regression":
                    model = LogisticRegression(max_iter=1000)
                else:
                    model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                if model_type == "Linear Regression":
                    model = LinearRegression()
                else:
                    model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            
            st.success("✅ Model trained successfully!")
            
            # Display results
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Model Performance")
                if task == "classification":
                    accuracy = accuracy_score(y_test, y_pred)
                    st.metric("Accuracy", f"{accuracy:.4f}")
                    st.write("**Classification Report:**")
                    st.text(classification_report(y_test, y_pred))
                else:
                    mse = mean_squared_error(y_test, y_pred)
                    rmse = np.sqrt(mse)
                    st.metric("RMSE", f"{rmse:.4f}")
                    st.metric("MSE", f"{mse:.4f}")
            
            with col2:
                st.subheader("📊 Visualizations")
                if task == "classification":
                    # Confusion Matrix
                    fig, ax = plt.subplots(figsize=(8, 6))
                    cm = confusion_matrix(y_test, y_pred)
                    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
                    ax.set_title("Confusion Matrix")
                    ax.set_ylabel("True Label")
                    ax.set_xlabel("Predicted Label")
                    st.pyplot(fig)
                else:
                    # Prediction vs Actual
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.scatter(y_test, y_pred, alpha=0.6)
                    ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
                    ax.set_xlabel("Actual Values")
                    ax.set_ylabel("Predicted Values")
                    ax.set_title("Predictions vs Actual")
                    st.pyplot(fig)

# ============ UPLOAD MODE ============
else:
    st.subheader("Upload Your Own Data")
    
    uploaded_file = st.file_uploader("Upload CSV file:", type=['csv'])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("**Data Preview:**")
        st.dataframe(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Shape:** {df.shape}")
            st.write(f"**Columns:** {list(df.columns)}")
        
        with col2:
            st.write("**Data Types:**")
            st.write(df.dtypes)
        
        if df.isnull().sum().sum() > 0:
            st.warning("⚠️ Missing values detected!")
            st.write(df.isnull().sum())
        
        # Select features and target
        columns = df.columns.tolist()
        col1, col2 = st.columns(2)
        
        with col1:
            feature_cols = st.multiselect("Select Features:", columns)
        with col2:
            target_col = st.selectbox("Select Target:", columns)
        
        if feature_cols and target_col:
            X = df[feature_cols].fillna(df[feature_cols].mean())
            y = df[target_col]
            
            col1, col2 = st.columns(2)
            with col1:
                task_type = st.radio("Task Type:", ["Classification", "Regression"])
            with col2:
                if task_type == "Classification":
                    model_choice = st.selectbox("Model:", ["Logistic Regression", "Random Forest"])
                else:
                    model_choice = st.selectbox("Model:", ["Linear Regression", "Random Forest"])
            
            test_size = st.slider("Test Size:", 0.1, 0.5, 0.2)
            
            if st.button("🚀 Train Model", key="train_upload"):
                with st.spinner("Training model..."):
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
                    
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)
                    
                    if task_type == "Classification":
                        if model_choice == "Logistic Regression":
                            model = LogisticRegression(max_iter=1000)
                        else:
                            model = RandomForestClassifier(n_estimators=100, random_state=42)
                    else:
                        if model_choice == "Linear Regression":
                            model = LinearRegression()
                        else:
                            model = RandomForestRegressor(n_estimators=100, random_state=42)
                    
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    
                    st.success("✅ Model trained successfully!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📈 Results")
                        if task_type == "Classification":
                            accuracy = accuracy_score(y_test, y_pred)
                            st.metric("Accuracy", f"{accuracy:.4f}")
                        else:
                            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                            st.metric("RMSE", f"{rmse:.4f}")
                    
                    with col2:
                        st.subheader("🔍 Predictions")
                        results_df = pd.DataFrame({
                            "Actual": y_test.values,
                            "Predicted": y_pred
                        })
                        st.dataframe(results_df.head(10))

st.markdown("---")
st.markdown("Built with Streamlit 🎈 | ML Models using scikit-learn 🤖")
