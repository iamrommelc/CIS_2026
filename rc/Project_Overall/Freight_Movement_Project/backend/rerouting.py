import pandas as pd
from scipy.optimize import linprog
import numpy as np
import os

def get_master_routing_guide():
    working_Directory = os.getcwd()
    fullPathCSV = os.path.join(working_Directory, "Delivery_Logistics.csv")
    df = pd.read_csv(fullPathCSV)

    weight_bins = [0, 10, 25, 40, 50]
    weight_labels = ['0-10kg', '10-25kg', '25-40kg', '40-50kg']

    df['is_delayed'] = (df['delayed'].astype(str).str.strip().str.lower() == 'yes').astype(int)
    df['weight_bracket'] = pd.cut(df['package_weight_kg'], bins=weight_bins, labels=weight_labels)

    demand_df = df.groupby(['region', 'weight_bracket'], observed=False).size().reset_index(name='demand')
    demand_df = demand_df[demand_df['demand'] > 0].reset_index(drop=True)
    total_demand = demand_df['demand'].sum()

    partner_counts = df['delivery_partner'].value_counts()
    capacities = {partner: int(count * 1.2) for partner, count in partner_counts.items()}
    partners = list(capacities.keys())

    agg_df = df.groupby(['region', 'weight_bracket', 'delivery_partner', 'delivery_mode'], observed=False).agg(
        cost=('delivery_cost', 'mean'),
        delay_rate=('is_delayed', 'mean')
    ).dropna().reset_index()
    c = agg_df['cost'].values

    A_eq = np.zeros((len(demand_df), len(agg_df)))
    b_eq = np.zeros(len(demand_df))
    for i, row in demand_df.iterrows():
        reg, wt = row['region'], row['weight_bracket']
        mask = (agg_df['region'] == reg) & (agg_df['weight_bracket'] == wt)
        A_eq[i, mask] = 1
        b_eq[i] = row['demand']

    num_ub_constraints = len(partners) + 1
    A_ub = np.zeros((num_ub_constraints, len(agg_df)))
    b_ub = np.zeros(num_ub_constraints)

    for i, partner in enumerate(partners):
        mask = (agg_df['delivery_partner'] == partner)
        A_ub[i, mask] = 1
        b_ub[i] = capacities[partner]

    MAX_DELAY_TOLERANCE = 0.05
    A_ub[-1, :] = agg_df['delay_rate'].values
    b_ub[-1] = MAX_DELAY_TOLERANCE * total_demand

    bounds = [(0, None) for _ in range(len(agg_df))]
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    agg_df['Allocated_Volume'] = np.round(res.x, 0)
    routing_guide = agg_df[agg_df['Allocated_Volume'] > 0].copy()
    routing_guide = routing_guide.sort_values(by=['region', 'weight_bracket', 'Allocated_Volume'], ascending=[True, True, False]).reset_index(drop=True)

    return routing_guide.to_dict(orient='records')