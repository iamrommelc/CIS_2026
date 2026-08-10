import pandas as pd
import numpy as np
import data_analysis

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, ConfusionMatrixDisplay
from sklearn.model_selection import RandomizedSearchCV, train_test_split
#from scipy.stats import randint

from sklearn.tree import export_graphviz
#from IPython.display import Image
#import graphviz


def random_forest_classifier(df1,df2):
    #print(df1)
    #print(df2)

    df1["distance_km"] = df1["distance_km"].astype(float)
    df1["package_weight_kg"] = df1["package_weight_kg"].astype(float)
    df1["vehicle_type"] = pd.factorize(df1["vehicle_type"].sort_values())[0]
    df2 = df2.astype(float)
    print(df1)
    print(df2)
    X_train, X_test, y_train, y_test = train_test_split(df1, df2, test_size=0.2, random_state=42)
    rf = RandomForestRegressor()
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    
    print("Average Error:", mean_absolute_error(y_test, y_pred))
    print("R2 Score:", r2_score(y_test, y_pred))

    print("=== Shipping Cost Calculator ===")
    
    
    user_distance = float(input("Enter distance: "))
    user_weight = float(input("Enter package weight: "))
    user_vehicle = float(input("Enter vehicle type in int: "))
    
    
    input_data = pd.DataFrame({
        'distance_km': [user_distance],
        'package_weight_kg': [user_weight],
        'vehicle_type': [user_vehicle]
    })
    
    
    predicted_cost = rf.predict(input_data)
    
    
    print("\n--- Calculation Result ---")
    print(f"Distance: {user_distance} units")
    print(f"Weight:   {user_weight} units")
    print(f"Vehicle:   {user_vehicle} units")
    print(f"Estimated Shipping Cost: {predicted_cost[0]:.2f}")
        
    



if __name__ == "__main__":
    print("Running Machine Learning Tests.....\n")
    df=pd.read_csv("Delivery_Logistics.csv",index_col=0)
    df=df[["distance_km","package_weight_kg","vehicle_type","delivery_cost"]]
    df = df.reset_index(drop=True)
    df1 = df[["distance_km","package_weight_kg","vehicle_type"]]
    df2 = df[["delivery_cost"]]

    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)
    random_forest_classifier(df1,df2)




