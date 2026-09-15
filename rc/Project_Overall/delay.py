import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

def main():
    # 1. Load the dataset
    file_path = "Delivery_Logistics.csv"
    try:
        df = pd.read_csv(file_path)
        print("Dataset loaded successfully!")
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found. Ensure it is in the same directory.")
        return

    # 2. Data Preprocessing
    # Drop columns that are irrelevant or cause "data leakage" (features only known AFTER delivery)
    columns_to_drop = [
        'delivery_id', 
        'delivery_time_hours', # Actual time taken is not known beforehand
        'delivery_status',     # Status is known post-delivery
        'delivery_rating',     # Rating is known post-delivery
        'delivery_cost'
    ]
    
    # Safely drop columns if they exist in the dataframe
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')

    # Convert the target variable 'delayed' into a binary format (1 for yes, 0 for no)
    df['delayed'] = df['delayed'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)

    # Separate features (X) and target (y)
    X = df.drop(columns=['delayed'])
    y = df['delayed']

    # Identify categorical and numerical columns for proper encoding
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

    print(f"Categorical features to encode: {categorical_cols}")
    print(f"Numerical features to scale: {numerical_cols}")

    # 3. Build the Preprocessing Pipeline
    # OneHotEncoder is used for categorical data; StandardScaler is used for numerical data
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', drop='first'), categorical_cols)
        ])

    # 4. Define the Model Pipeline
    # We use a RandomForestClassifier, which is robust and provides probability likelihoods
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    # 5. Split the Data
    # 80% for training, 20% for testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 6. Train the Model
    print("\nTraining the model... This might take a moment.")
    pipeline.fit(X_train, y_train)

    # 7. Evaluate and Predict Likelihoods
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1] # Probability of class 1 (Delayed)

    print("\n--- Model Evaluation ---")
    print(classification_report(y_test, y_pred, target_names=['On Time (0)', 'Delayed (1)']))
    
    # Calculate ROC-AUC score for a better metric on binary classification likelihoods
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"ROC-AUC Score: {roc_auc:.4f}")

    # Displaying the likelihood predictions for the first 5 test samples
    print("\n--- Sample Likelihood Predictions ---")
    sample_results = X_test.head(5).copy()
    sample_results['Actual_Delayed'] = y_test.head(5).values
    sample_results['Predicted_Probability_of_Delay'] = y_pred_proba[:5]
    
    print(sample_results[['Actual_Delayed', 'Predicted_Probability_of_Delay']])

if __name__ == "__main__":
    main()
