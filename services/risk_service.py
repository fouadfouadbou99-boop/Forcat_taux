import numpy as np

def calculate_dv01(duration, market_value):

    return duration * market_value * 0.0001

def calculate_var(returns):

    return np.percentile(returns, 5)
