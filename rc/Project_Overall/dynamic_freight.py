import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import warnings

# Suppress minor warnings for cleaner console output
warnings.filterwarnings('ignore')

def build_models(file_path="Delivery_Logistics.csv"):
    print("Loading data and training routing engine models...")
    
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.")
        return None, None, None
        
    # Preprocessing target variables
    # Convert 'delayed' to binary for the Classifier
    df['delayed'] = df['delayed'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
    
    # Define features (X) and our two targets (y_delay, y_cost)
    # We drop targets and post-delivery leakage columns from X
    leakage_cols = ['delivery_id', 'delivery_time_hours', 'expected_time_hours', 
                    'delivery_status', 'delivery_rating', 'delayed', 'delivery_cost']
    
    X = df.drop(columns=[col for col in leakage_cols if col in df.columns])
    y_delay = df['delayed']
    y_cost = df['delivery_cost']
    
    # Identify column types for the pipeline
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

    # Create a shared preprocessing step
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
        ])

    # Model 1: Binary Classifier for Delay Likelihood
    delay_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=50, random_state=42))
    ])

    # Model 2: Regressor for Shipping Cost
    cost_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=50, random_state=42))
    ])

    # Train both models on the full dataset for the routing engine
    delay_pipeline.fit(X, y_delay)
    cost_pipeline.fit(X, y_cost)
    
    # Extract available unique partners and vehicles to use in the routing logic
    partners = df['delivery_partner'].unique().tolist()
    vehicles = df['vehicle_type'].unique().tolist()
    
    print("Models trained successfully!\n")
    return delay_pipeline, cost_pipeline, partners, vehicles

def recommend_best_carrier(delay_model, cost_model, partners, vehicles, shipment_profile):
    """
    Evaluates all carriers for a given shipment profile and recommends the best one.
    """
    print(f"--- Routing Engine: Evaluating Options ---")
    print(f"Profile: {shipment_profile['distance_km']}km, {shipment_profile['package_weight_kg']}kg, "
          f"{shipment_profile['package_type']} ({shipment_profile['delivery_mode']})")
    
    options = []
    
    # Generate a theoretical route for every partner and their typical vehicle type
    for partner in partners:
        # Defaulting to a sensible vehicle per partner or iterating through standard ones
        # For simplicity in this engine, we'll check 'van' and 'truck' for each
        for vehicle in ['van', 'truck']:
            if vehicle not in vehicles:
                continue
                
            # Create a dataframe for the single prediction instance
            test_case = pd.DataFrame([{
                'delivery_partner': partner,
                'package_type': shipment_profile['package_type'],
                'vehicle_type': vehicle,
                'delivery_mode': shipment_profile['delivery_mode'],
                'region': shipment_profile['region'],
                'weather_condition': shipment_profile['weather_condition'],
                'distance_km': shipment_profile['distance_km'],
                'package_weight_kg': shipment_profile['package_weight_kg']
            }])
            
            # Predict Cost
            pred_cost = cost_model.predict(test_case)[0]
            
            # Predict Delay Probability (likelihood of class 1)
            pred_delay_prob = delay_model.predict_proba(test_case)[0][1]
            
            options.append({
                'Carrier': partner.capitalize(),
                'Vehicle': vehicle.capitalize(),
                'Est_Cost': pred_cost,
                'Delay_Probability': pred_delay_prob
            })
            
    # Convert options to a DataFrame for easy sorting and ranking
    results_df = pd.DataFrame(options)
    
    # RANKING LOGIC: 
    # 1. Filter out options with a > 50% chance of delay (unreliable).
    # 2. Sort the remaining by Lowest Cost.
    # 3. If all are > 50% delayed, just sort by lowest delay probability.
    reliable_options = results_df[results_df['Delay_Probability'] < 0.50]
    
    if not reliable_options.empty:
        best_routes = reliable_options.sort_values(by='Est_Cost', ascending=True)
    else:
        best_routes = results_df.sort_values(by=['Delay_Probability', 'Est_Cost'], ascending=[True, True])
        
    print("\nAvailable Carrier Options (Ranked):")
    # Formatting for cleaner output
    best_routes['Est_Cost'] = best_routes['Est_Cost'].apply(lambda x: f"${x:.2f}")
    best_routes['Delay_Probability'] = best_routes['Delay_Probability'].apply(lambda x: f"{x*100:.1f}%")
    print(best_routes.to_string(index=False))
    
    print("\n🏆 RECOMMENDATION:")
    top_pick = best_routes.iloc[0]
    print(f"Use {top_pick['Carrier']} via {top_pick['Vehicle']}.")
    print(f"Expected Cost: {top_pick['Est_Cost']} | Risk of Delay: {top_pick['Delay_Probability']}")
    print("-" * 50)

if __name__ == "__main__":
    # 1. Initialize models
    delay_model, cost_model, partners, vehicles = build_models()
    
    if delay_model is not None:
        # 2. Define a test shipment profile (Simulating user input)
        # You can easily swap these out with Python input() prompts if you prefer interactivity.
        test_shipment_1 = {
            'distance_km': 120.5,
            'package_weight_kg': 15.2,
            'package_type': 'electronics',
            'delivery_mode': 'express',
            'region': 'north',
            'weather_condition': 'rainy'
        }
        
        test_shipment_2 = {
            'distance_km': 450.0,
            'package_weight_kg': 85.0,
            'package_type': 'furniture', # Assuming this exists or falls into OHE 'ignore'
            'delivery_mode': 'standard',
            'region': 'south',
            'weather_condition': 'clear'
        }
        
        # 3. Run the engine for our profiles
        recommend_best_carrier(delay_model, cost_model, partners, vehicles, test_shipment_1)
        print("\n")
        recommend_best_carrier(delay_model, cost_model, partners, vehicles, test_shipment_2)
