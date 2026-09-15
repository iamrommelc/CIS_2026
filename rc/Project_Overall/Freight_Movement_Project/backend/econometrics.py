import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
import os

def get_econometrics_data():
    working_directory = os.getcwd()
    fullCSVPath = os.path.join(working_directory, "Delivery_Logistics.csv")
    df = pd.read_csv(fullCSVPath)

    # 1. Freight Corridor Clustering (from Kmean.py)
    cluster_data = df[["distance_km", "region"]].dropna()
    preprocessor = ColumnTransformer(
        transformers=[
            ("distance", StandardScaler(), ["distance_km"]),
            ("region", OneHotEncoder(handle_unknown="ignore"), ["region"])
        ]
    )
    X = preprocessor.fit_transform(cluster_data)
    
    kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    df.loc[cluster_data.index, "freight_corridor"] = cluster_labels

    # 2. Corridor Inefficiency Metrics
    df["cost_per_km"] = df["delivery_cost"] / df["distance_km"]
    df["cost_per_km"] = df["cost_per_km"].replace([np.inf, -np.inf], np.nan)
    df["delay_binary"] = df["delayed"].astype(str).str.lower().map({"yes": 1, "no": 0})
    
    corridor_eff = df.groupby("freight_corridor").agg(
        shipments=("delivery_id", "count"),
        avg_cost_per_km=("cost_per_km", "mean"),
        delay_rate=("delay_binary", "mean")
    ).reset_index()
    corridor_eff["delay_rate"] *= 100

    dom_regions = df.groupby("freight_corridor")["region"].agg(lambda x: x.value_counts().idxmax()).reset_index()
    dom_regions.columns = ["freight_corridor", "dominant_region"]
    corridor_eff = corridor_eff.merge(dom_regions, on="freight_corridor")

    # 3. Log-Log Elasticity Model (from Corridor_Pricing_Elasticity.py)
    reg_data = df[(df["distance_km"] > 0) & (df["package_weight_kg"] > 0) & (df["delivery_cost"] > 0)].dropna(
        subset=["distance_km", "package_weight_kg", "delivery_cost", "delivery_partner", "freight_corridor"]
    ).copy()
    reg_data["freight_corridor"] = reg_data["freight_corridor"].astype(int).astype(str)

    model = smf.ols(
        formula="np.log(delivery_cost) ~ np.log(distance_km) + np.log(package_weight_kg) + C(delivery_partner) + C(freight_corridor)",
        data=reg_data
    ).fit(cov_type="HC3")

    dist_elast = model.params["np.log(distance_km)"]
    weight_elast = model.params["np.log(package_weight_kg)"]

    # 4. Carrier Premiums
    carrier_premiums = model.params[model.params.index.str.startswith("C(delivery_partner)")].rename_axis("delivery_partner").reset_index(name="log_premium")
    # Clean string 'C(delivery_partner)[T.fedex]' -> 'fedex'
    carrier_premiums["delivery_partner"] = carrier_premiums["delivery_partner"].str.extract(r"\[T\.(.+)\]")
    carrier_premiums["pct_premium"] = (np.exp(carrier_premiums["log_premium"]) - 1) * 100

    # 5. Overcharging Residuals
    reg_data["residual"] = model.resid
    resid_std = reg_data["residual"].std()
    reg_data["overcharged_flag"] = reg_data["residual"] > 1.5 * resid_std
    
    overcharge_rate = reg_data.groupby("freight_corridor")["overcharged_flag"].mean().reset_index(name="overcharge_pct")
    overcharge_rate["overcharge_pct"] *= 100
    overcharge_rate["freight_corridor"] = overcharge_rate["freight_corridor"].astype(float)

    corridor_eff = corridor_eff.merge(overcharge_rate, on="freight_corridor", how="left")

    return {
        "elasticity": {
            "distance": round(dist_elast, 4),
            "weight": round(weight_elast, 4)
        },
        "premiums": carrier_premiums.dropna().sort_values("pct_premium", ascending=False).to_dict(orient="records"),
        "corridors": corridor_eff.sort_values("avg_cost_per_km", ascending=False).to_dict(orient="records")
    }