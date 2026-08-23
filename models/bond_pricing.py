def total_return(
        yield_rate,
        duration,
        convexity,
        horizon,
        delta_rate,
        roll_down
):

    carry = yield_rate * horizon

    price_effect = -duration * delta_rate

    convexity_effect = 0.5 * convexity * delta_rate**2

    total = (
        carry
        + roll_down
        + price_effect
        + convexity_effect
    )

    return total
