import pandas as pd

def load_portfolio(file):

    return pd.read_excel(file)

def calculate_portfolio_return(df):

    return (df["Poids"] *
            df["Total Return"]).sum()
