import pandas as pd
import sys
import logging
from scipy.optimize import linprog
import numpy as np
import time
import os

working_Directory = os.getcwd()
fullPathCSV = os.path.join(working_Directory, "Delivery_Logistics.csv")
df=pd.read_csv(fullPathCSV, index_col=0)
weight_bins = [0, 10, 25, 40, 50]
weight_labels = ['0-10kg', '10-25kg', '25-40kg', '40-50kg']

def weightingUp():
    """Add delay indicators and package-weight brackets to the delivery data."""
    global df
    df['is_delayed'] = (df['delayed'] == 'yes').astype(int)
    df['weight_bracket'] = pd.cut(df['package_weight_kg'], bins=weight_bins, labels=weight_labels)

def calculations():
    """Build and solve the delivery allocation optimization model.

    Returns:
        tuple: The optimization result and the aggregated delivery metrics.
    """
    global df
    demand_df = df.groupby(['region', 'weight_bracket'], observed=False).size().reset_index(name='demand')
    demand_df = demand_df[demand_df['demand'] > 0].reset_index(drop=True)
    print(demand_df.head())
    total_demand = demand_df['demand'].sum()  # calculating the total demand

    partner_counts = df['delivery_partner'].value_counts()
    capacities = {partner: int(count * 1.2) for partner, count in partner_counts.items()}  # calculating the carrier capacities with a 20% buffer
    partners = list(capacities.keys())

    agg_df = df.groupby(['region', 'weight_bracket', 'delivery_partner', 'delivery_mode'], observed=False).agg(
        cost=('delivery_cost', 'mean'),
        delay_rate=('is_delayed', 'mean')
    ).dropna().reset_index()  # Getting historical cost and delay rate for each partner in each region and weight bracket
    print("Aggregated DataFrame:\n",agg_df.head())
    c = agg_df['cost'].values

    # EQUALITY CONSTRAINTS (A_eq * x = b_eq) -> Fulfill Demand
    # 1 row per unique region/weight combo, N columns
    A_eq = np.zeros((len(demand_df), len(agg_df)))
    b_eq = np.zeros(len(demand_df))

    for i, row in demand_df.iterrows():
        reg, wt = row['region'], row['weight_bracket']
        # Find which variables (columns) belong to this region/weight demand
        mask = (agg_df['region'] == reg) & (agg_df['weight_bracket'] == wt)
        A_eq[i, mask] = 1 
        b_eq[i] = row['demand']

    # INEQUALITY CONSTRAINTS (A_ub * x <= b_ub) -> Capacity & Delay
    # rows: Number of partners + 1 (for global delay limit)
    num_ub_constraints = len(partners) + 1
    A_ub = np.zeros((num_ub_constraints, len(agg_df)))
    b_ub = np.zeros(num_ub_constraints)

    # A) Capacity limits per partner
    for i, partner in enumerate(partners):
        mask = (agg_df['delivery_partner'] == partner)
        A_ub[i, mask] = 1
        b_ub[i] = capacities[partner]

    # B) Strict Service Level - Max 5% global network delay rate
    MAX_DELAY_TOLERANCE = 0.05
    A_ub[-1, :] = agg_df['delay_rate'].values
    b_ub[-1] = MAX_DELAY_TOLERANCE * total_demand

    # Variable bounds (x >= 0)
    bounds = [(0, None) for _ in range(len(agg_df))]
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')  # solving the model
    return res, agg_df

def routing_guide(res, agg_df):
    """Create a sorted routing guide from the optimization allocation result.

    Args:
        res: The optimization result containing allocated volumes.
        agg_df (pandas.DataFrame): Aggregated delivery metrics by route.

    Returns:
        pandas.DataFrame: Routes with positive allocated volume, sorted for use
            as a routing guide.
    """
    agg_df['Allocated_Volume'] = res.x
    routing_guide = agg_df[agg_df['Allocated_Volume'] > 1e-5].copy()
    routing_guide = routing_guide.sort_values(
        by=['region', 'weight_bracket', 'Allocated_Volume'],
    ).reset_index(drop=True)
    return routing_guide

def main():
    """Main execution function."""
    try:
        print(working_Directory)
        print(fullPathCSV)
        print(df.head())
        print("Starting the model training and evaluation process...")
        print("Step 1: Data Preprocessing and Weighting")
        time.sleep(5.0)
        weightingUp()
        print("Step 2: Calculations and Optimization")
        time.sleep(5.0)
        res, agg_df = calculations()
        print("Optimization Result:\n", res)
        print(agg_df.head())
        print("Step 3: Generating Routing Guide")
        time.sleep(5.0)
        routing_guide_df = routing_guide(res, agg_df)
        print(routing_guide_df.head())
        print("Model training and evaluation completed successfully.")
    except Exception as e:
        print("Exception occurred due to {0}".format(str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
