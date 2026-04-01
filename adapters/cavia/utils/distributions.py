def dist_deterministic(mean, rng):
    return mean


def dist_exponential(mean, rng):
    return rng.exponential(scale=mean)


def dist_uniform(mean, rng):
    return rng.uniform(low=mean * 0.5, high=mean * 1.5)


def dist_normal(mean, rng):
    sigma = mean * 0.1
    return max(0, rng.normal(loc=mean, scale=sigma))


def dist_bimodal(mean, rng):
    if rng.random() < 0.8:
        return mean * 0.5
    else:
        return mean * 3.0


STRATEGY_REGISTRY = {
    "deterministic": dist_deterministic,
    "exponential": dist_exponential,
    "uniform": dist_uniform,
    "normal": dist_normal,
    "bimodal": dist_bimodal,
}
