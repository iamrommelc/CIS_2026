import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans

# load data set
df = pd.read_csv(r"C:\Users\SAKSHI\Downloads\TERM 3\CIS\Delivery_Logistics.csv")

# ---------------------------------------------------------------------------
# Step 1: Recreate freight corridors (same K-Means spec as Kmean.py)
# ---------------------------------------------------------------------------
cluster_data = df[["distance_km", "region"]].dropna()

preprocessor = ColumnTransformer(
    transformers=[
        ("distance", StandardScaler(), ["distance_km"]),
        ("region", OneHotEncoder(handle_unknown="ignore"), ["region"])
    ]
)

X = preprocessor.fit_transform(cluster_data)

kmeans = KMeans(n_clusters=6, random_state=42, n_init=20)
cluster_labels = kmeans.fit_predict(X)

df.loc[cluster_data.index, "freight_corridor"] = cluster_labels

# ---------------------------------------------------------------------------
# Step 2: Build the regression sample
# Log-log requires strictly positive distance, weight, and cost
# ---------------------------------------------------------------------------
reg_data = df[
    (df["distance_km"] > 0)
    & (df["package_weight_kg"] > 0)
    & (df["delivery_cost"] > 0)
].dropna(subset=["distance_km", "package_weight_kg", "delivery_cost",
                  "delivery_partner", "freight_corridor"]).copy()

reg_data["freight_corridor"] = reg_data["freight_corridor"].astype(int).astype(str)

print("Regression sample size:", reg_data.shape[0])

# ---------------------------------------------------------------------------
# Step 3: Log-log elasticity model
# ln(cost) = b0 + b1*ln(distance) + b2*ln(weight)
#            + carrier fixed effects + corridor fixed effects
# ---------------------------------------------------------------------------
model = smf.ols(
    formula=(
        "np.log(delivery_cost) ~ np.log(distance_km) + np.log(package_weight_kg) "
        "+ C(delivery_partner) + C(freight_corridor)"
    ),
    data=reg_data
).fit(cov_type="HC3")

print(model.summary())

distance_elasticity = model.params["np.log(distance_km)"]
weight_elasticity = model.params["np.log(package_weight_kg)"]

print(f"\nDistance elasticity: {distance_elasticity:.4f}")
print(f"Weight elasticity:   {weight_elasticity:.4f}")

for elasticity, label in [(distance_elasticity, "distance"), (weight_elasticity, "weight")]:
    if elasticity < 1:
        print(f"-> Economies of scale in {label} (cost rises slower than {label}).")
    elif elasticity > 1:
        print(f"-> Diseconomies of scale in {label} (cost rises faster than {label}).")
    else:
        print(f"-> Cost scales linearly with {label}.")

# ---------------------------------------------------------------------------
# Step 4: Carrier-specific price premiums
# Coefficients on the carrier dummies, relative to the baseline carrier
# ---------------------------------------------------------------------------
carrier_premiums = (
    model.params[model.params.index.str.startswith("C(delivery_partner)")]
    .rename_axis("delivery_partner")
    .reset_index(name="log_premium")
)

carrier_premiums["delivery_partner"] = (
    carrier_premiums["delivery_partner"]
    .str.extract(r"\[T\.(.+)\]")
)

carrier_premiums["pct_premium_vs_baseline"] = (
    (np.exp(carrier_premiums["log_premium"]) - 1) * 100
)

print("\nCarrier price premiums vs. baseline carrier:")
print(carrier_premiums.sort_values("pct_premium_vs_baseline", ascending=False))

# ---------------------------------------------------------------------------
# Step 5: Residual analysis - who is overcharging, and where
# ---------------------------------------------------------------------------
reg_data["log_cost_actual"] = np.log(reg_data["delivery_cost"])
reg_data["log_cost_predicted"] = model.fittedvalues
reg_data["residual"] = model.resid

residual_std = reg_data["residual"].std()
reg_data["overcharged_flag"] = reg_data["residual"] > 1.5 * residual_std

print(f"\nShipments flagged as overcharged (residual > 1.5 SD): "
      f"{reg_data['overcharged_flag'].sum()} of {reg_data.shape[0]}")

overcharge_by_partner_corridor = (
    reg_data.groupby(["delivery_partner", "freight_corridor"])
    .agg(
        shipments=("delivery_id", "count"),
        mean_residual=("residual", "mean"),
        overcharge_rate=("overcharged_flag", "mean")
    )
    .reset_index()
)

overcharge_by_partner_corridor["overcharge_rate"] *= 100

print("\nTop carrier-corridor combinations by mean residual (most overcharged):")
print(
    overcharge_by_partner_corridor
    .sort_values("mean_residual", ascending=False)
    .head(15)
)

# ---------------------------------------------------------------------------
# Step 6: Visualize residuals by carrier and corridor
# ---------------------------------------------------------------------------
pivot = overcharge_by_partner_corridor.pivot(
    index="delivery_partner",
    columns="freight_corridor",
    values="mean_residual"
)

plt.figure(figsize=(10, 7))
sns.heatmap(pivot, cmap="RdBu_r", center=0, annot=True, fmt=".2f")
plt.title("Mean Pricing Residual by Carrier and Freight Corridor\n(positive = overcharging relative to model)")
plt.xlabel("Freight Corridor")
plt.ylabel("Delivery Partner")
plt.tight_layout()
plt.show()
