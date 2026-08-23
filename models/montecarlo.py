import numpy as np

def simulate_rates(
        current_rate,
        volatility,
        simulations=5000,
        horizon=1
):

    shocks = np.random.normal(
        0,
        volatility,
        simulations
    )

    return current_rate + shocks * np.sqrt(horizon)
