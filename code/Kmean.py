import pandas as pd 
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt 

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

#load data set 
df = pd.read_csv(r"C:\Users\SAKSHI\Downloads\TERM 3\CIS\Delivery_Logistics.csv")

print("Shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum())

print("\nRegion distribution:")
print(df["region"].value_counts())

# Variables used for clustering
cluster_data = df[["distance_km", "region"]].copy()

# Remove missing observations
cluster_data = cluster_data.dropna()

# Preprocessing:
# - Standardize distance
# - One-hot encode region
preprocessor = ColumnTransformer(
    transformers=[
        ("distance", StandardScaler(), ["distance_km"]),
        ("region", OneHotEncoder(handle_unknown="ignore"), ["region"])
    ]
)

X = preprocessor.fit_transform(cluster_data)

print("Clustering matrix shape:", X.shape)

silhouette_scores = []
inertia_values = []

K_range = range(2, 11)

for k in K_range:

    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = kmeans.fit_predict(X)

    inertia_values.append(kmeans.inertia_)

    # Use sample_size because silhouette calculation
    # can become computationally expensive for 25,000 rows
    score = silhouette_score(
        X,
        labels,
        sample_size=5000,
        random_state=42
    )

    silhouette_scores.append(score)

    print(f"K={k} | Inertia={kmeans.inertia_:.2f} | Silhouette={score:.4f}")

 #plot the elbow curve
plt.figure(figsize=(10, 5))

plt.plot(
    K_range,
    inertia_values,
    marker="o"
)

plt.xlabel("Number of Clusters (K)")
plt.ylabel("Within-Cluster Sum of Squares")
plt.title("Elbow Method for Freight Corridor Clustering")
plt.grid(True)

plt.show()

#Plot Silhouette Score
plt.figure(figsize=(10, 5))

plt.plot(
    K_range,
    silhouette_scores,
    marker="o"
)

plt.xlabel("Number of Clusters (K)")
plt.ylabel("Silhouette Score")
plt.title("Silhouette Analysis for Freight Corridor Clustering")
plt.grid(True)

plt.show()

#final KMEAN Model
optimal_k = 6

kmeans = KMeans(
    n_clusters=optimal_k,
    random_state=42,
    n_init=20
)

cluster_labels = kmeans.fit_predict(X)

cluster_data["cluster"] = cluster_labels

# Add cluster labels back to original dataset
df.loc[cluster_data.index, "freight_corridor"] = cluster_labels

print(df["freight_corridor"].value_counts().sort_index())

#creating corridor profile
corridor_profile = df.groupby("freight_corridor").agg(
    shipments=("delivery_id", "count"),
    avg_distance_km=("distance_km", "mean"),
    median_distance_km=("distance_km", "median"),
    avg_delivery_cost=("delivery_cost", "mean"),
    avg_rating=("delivery_rating", "mean")
).reset_index()

print(corridor_profile)

#Dominant region in each corridor
region_distribution = pd.crosstab(
    df["freight_corridor"],
    df["region"],
    normalize="index"
) * 100

print(region_distribution.round(2))

#label dominant region
dominant_region = (
    df.groupby("freight_corridor")["region"]
    .agg(lambda x: x.value_counts().idxmax())
)

print(dominant_region);

#naming corridors
corridor_summary = df.groupby("freight_corridor").agg(
    avg_distance=("distance_km", "mean"),
    shipments=("delivery_id", "count")
).reset_index()

corridor_summary["dominant_region"] = (
    df.groupby("freight_corridor")["region"]
    .agg(lambda x: x.value_counts().idxmax())
    .values
)

def distance_category(distance):

    if distance < 100:
        return "Short Haul"

    elif distance < 300:
        return "Medium Haul"

    else:
        return "Long Haul"


corridor_summary["distance_category"] = (
    corridor_summary["avg_distance"]
    .apply(distance_category)
)

corridor_summary["corridor_name"] = (
    corridor_summary["dominant_region"].str.title()
    + " - "
    + corridor_summary["distance_category"]
)

print(corridor_summary)

#Visualize the freight corridors -creating scaater plot
plt.figure(figsize=(12, 7))

sns.scatterplot(
    data=df,
    x="distance_km",
    y="region",
    hue="freight_corridor",
    palette="tab10",
    alpha=0.6,
    s=40
)

plt.title("Freight Corridors Identified Using K-Means")
plt.xlabel("Distance (km)")
plt.ylabel("Region")

plt.legend(
    title="Corridor",
    bbox_to_anchor=(1.05, 1),
    loc="upper left"
)

plt.tight_layout()
plt.show()

#structural inefficiencies -normalize cost by distance.
df["cost_per_km"] = (
    df["delivery_cost"] / df["distance_km"]
)

# Avoid infinite values
df["cost_per_km"] = df["cost_per_km"].replace(
    [np.inf, -np.inf],
    np.nan
)

#Analyze delay performance by corridor
df["delay_binary"] = (
    df["delayed"]
    .str.lower()
    .map({"yes": 1, "no": 0})
)

corridor_efficiency = df.groupby("freight_corridor").agg(
    shipments=("delivery_id", "count"),

    avg_distance_km=("distance_km", "mean"),

    avg_delivery_cost=("delivery_cost", "mean"),

    avg_cost_per_km=("cost_per_km", "mean"),

    delay_rate=("delay_binary", "mean"),

    avg_rating=("delivery_rating", "mean")
).reset_index()

corridor_efficiency["delay_rate"] *= 100

print(
    corridor_efficiency.sort_values(
        "delay_rate",
        ascending=False
    )
)

#Identify inefficient corridors

# Standardize performance indicators
metrics = [
    "avg_cost_per_km",
    "delay_rate"
]

for metric in metrics:

    corridor_efficiency[metric + "_z"] = (
        corridor_efficiency[metric]
        - corridor_efficiency[metric].mean()
    ) / corridor_efficiency[metric].std()


# Composite inefficiency score
corridor_efficiency["inefficiency_score"] = (
    corridor_efficiency["avg_cost_per_km_z"]
    + corridor_efficiency["delay_rate_z"]
)

print(
    corridor_efficiency[
        [
            "freight_corridor",
            "avg_cost_per_km",
            "delay_rate",
            "inefficiency_score"
        ]
    ]
    .sort_values(
        "inefficiency_score",
        ascending=False
    )
)

#Compare delivery partners inside each corridor

partner_corridor = df.groupby(
    ["freight_corridor", "delivery_partner"]
).agg(
    shipments=("delivery_id", "count"),
    avg_cost=("delivery_cost", "mean"),
    avg_cost_per_km=("cost_per_km", "mean"),
    delay_rate=("delay_binary", "mean"),
    avg_rating=("delivery_rating", "mean")
).reset_index()

partner_corridor["delay_rate"] *= 100

print(partner_corridor.sort_values(
    ["freight_corridor", "avg_cost_per_km"]
))

#Use a Chi-square test: H₀: Delay is independent of freight corridor. 
# H₁: Delay is associated with freight corridor.
from scipy.stats import chi2_contingency

contingency_table = pd.crosstab(
    df["freight_corridor"],
    df["delayed"]
)

print(contingency_table)

chi2, p_value, degrees_of_freedom, expected = chi2_contingency(
    contingency_table
)

print("\nChi-square statistic:", chi2)
print("Degrees of freedom:", degrees_of_freedom)
print("p-value:", p_value)

if p_value < 0.05:
    print(
        "Conclusion: Delay rates differ significantly "
        "across freight corridors."
    )
else:
    print(
        "Conclusion: No statistically significant "
        "association between corridor and delay."
    )

# to check whether delivery cost differs between corridors

from scipy.stats import f_oneway

groups = [
    group["delivery_cost"].dropna().values
    for _, group in df.groupby("freight_corridor")
]

anova_stat, anova_p = f_oneway(*groups)

print("ANOVA F-statistic:", anova_stat)
print("ANOVA p-value:", anova_p)

if anova_p < 0.05:
    print(
        "Delivery costs differ significantly "
        "across freight corridors."
    )
else:
    print(
        "No statistically significant difference "
        "in delivery costs across corridors."
    )

#final management dashboard table

final_corridor_analysis = df.groupby(
    "freight_corridor"
).agg(
    shipment_volume=("delivery_id", "count"),

    avg_distance_km=("distance_km", "mean"),

    avg_delivery_cost=("delivery_cost", "mean"),

    avg_cost_per_km=("cost_per_km", "mean"),

    delay_rate=("delay_binary", "mean"),

    avg_customer_rating=("delivery_rating", "mean")
).reset_index()

final_corridor_analysis["delay_rate"] *= 100

# Add dominant region
dominant_regions = (
    df.groupby("freight_corridor")["region"]
    .agg(lambda x: x.value_counts().idxmax())
    .reset_index()
)

dominant_regions.columns = [
    "freight_corridor",
    "dominant_region"
]

final_corridor_analysis = final_corridor_analysis.merge(
    dominant_regions,
    on="freight_corridor"
)

# Sort by inefficiency indicators
final_corridor_analysis = final_corridor_analysis.sort_values(
    "avg_cost_per_km",
    ascending=False
)

print(final_corridor_analysis.round(2))