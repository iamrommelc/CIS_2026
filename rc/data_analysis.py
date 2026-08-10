import pandas as pd
df =pd.DataFrame()


def data_read():
    df=pd.read_csv("Delivery_Logistics.csv",index_col=0)
    return df
    

def clean_data(df):
    df=df[["distance_km","package_weight_kg","vehicle_type","delivery_cost"]]
    df = df.reset_index(drop=True)
    df1 = df[["distance_km","package_weight_kg","vehicle_type"]]
    df2 = df[["delivery_cost"]]
    print(df)

    

if __name__ == "__main__":
    print("Running Data Analysis.....\n")
    df=data_read()
    clean_data(df)
 