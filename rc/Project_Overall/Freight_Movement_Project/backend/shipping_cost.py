import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

rf_model = None

def train_model():
    global rf_model
    try:
        df = pd.read_csv("Delivery_Logistics.csv")
        df["distance_km"] = df["distance_km"].astype(float)
        df["package_weight_kg"] = df["package_weight_kg"].astype(float)
        df["vehicle_type"] = pd.factorize(df["vehicle_type"].sort_values())[0]
        
        X = df[["distance_km", "package_weight_kg", "vehicle_type"]]
        y = df["delivery_cost"]
        
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
        rf_model = RandomForestRegressor()
        rf_model.fit(X_train, y_train)
        print("Shipping Cost model trained.")
    except Exception as e:
        print(f"Error training cost model: {e}")

def predict_cost(distance, weight, vehicle):
    if rf_model is None: train_model()
    input_data = pd.DataFrame({'distance_km': [float(distance)], 'package_weight_kg': [float(weight)], 'vehicle_type': [float(vehicle)]})
    return rf_model.predict(input_data)[0]
