import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

delay_pipeline, cost_pipeline, partners, vehicles = None, None, [], []

def train_dynamic_models():
    global delay_pipeline, cost_pipeline, partners, vehicles
    try:
        df = pd.read_csv("Delivery_Logistics.csv")
        df['delayed'] = df['delayed'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
        
        # --- TRUE ML WAY: Prior Alignment via Resampling ---
        # Separate the classes
        df_on_time = df[df['delayed'] == 0]
        df_delayed = df[df['delayed'] == 1]
        
        # Target a ~18% delay rate for the classifier's baseline
        # Formula: delayed_target = (target_rate / (1 - target_rate)) * on_time_count
        target_rate = 0.18
        target_delayed_count = int((target_rate / (1.0 - target_rate)) * len(df_on_time))
        
        # Safely downsample the delayed class
        if len(df_delayed) > target_delayed_count:
            df_delayed_sampled = df_delayed.sample(n=target_delayed_count, random_state=42)
        else:
            df_delayed_sampled = df_delayed
            
        # Recombine and shuffle exclusively for the classifier
        df_class = pd.concat([df_on_time, df_delayed_sampled]).sample(frac=1, random_state=42)
        # ---------------------------------------------------
        
        leakage_cols = ['delivery_id', 'delivery_time_hours', 'expected_time_hours', 'delivery_status', 'delivery_rating', 'delayed', 'delivery_cost']
        
        # Split datasets: Use balanced data for classifier, full data for cost regressor
        X_class = df_class.drop(columns=[col for col in leakage_cols if col in df_class.columns])
        y_delay = df_class['delayed']
        
        X_reg = df.drop(columns=[col for col in leakage_cols if col in df.columns])
        y_cost = df['delivery_cost']
        
        cat_cols = X_reg.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols = X_reg.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        preprocessor = ColumnTransformer(transformers=[
            ('num', StandardScaler(), num_cols), 
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols)
        ])
        
        # Apply structured regularization to the Random Forest
        delay_pipeline = Pipeline([
            ('preprocessor', preprocessor), 
            ('classifier', RandomForestClassifier(
                n_estimators=100, 
                max_depth=5, 
                min_samples_leaf=10, 
                random_state=42
            ))
        ])
        
        cost_pipeline = Pipeline([
            ('preprocessor', preprocessor), 
            ('regressor', RandomForestRegressor(n_estimators=50, random_state=42))
        ])
        
        # Train on their respective datasets
        delay_pipeline.fit(X_class, y_delay)
        cost_pipeline.fit(X_reg, y_cost)
        
        partners = df['delivery_partner'].unique().tolist()
        vehicles = df['vehicle_type'].unique().tolist()
        print("Dynamic models trained with Prior Alignment.")
    except Exception as e:
        print(f"Error training dynamic models: {e}")

def evaluate_carriers(shipment_profile):
    if delay_pipeline is None: train_dynamic_models()
    options = []
    for partner in partners:
        for vehicle in ['van', 'truck', 'bike']:
            if vehicle not in vehicles: continue
            
            test_case = pd.DataFrame([{
                'delivery_partner': partner, 'package_type': shipment_profile['package_type'],
                'vehicle_type': vehicle, 'delivery_mode': shipment_profile['delivery_mode'],
                'region': shipment_profile['region'], 'weather_condition': shipment_profile['weather_condition'],
                'distance_km': float(shipment_profile['distance_km']), 'package_weight_kg': float(shipment_profile['package_weight_kg'])
            }])
            
            pred_cost = cost_pipeline.predict(test_case)[0]
            pred_delay_prob = delay_pipeline.predict_proba(test_case)[0][1]
            
            options.append({'Carrier': partner.capitalize(), 'Vehicle': vehicle.capitalize(), 'Est_Cost': round(pred_cost, 2), 'Delay_Probability': round(pred_delay_prob * 100, 1)})
            
    results_df = pd.DataFrame(options)
    reliable = results_df[results_df['Delay_Probability'] < 50.0]
    best_routes = reliable.sort_values(by='Est_Cost') if not reliable.empty else results_df.sort_values(by=['Delay_Probability', 'Est_Cost'])
    return best_routes.to_dict(orient='records')
