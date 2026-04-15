import numpy as np
from scipy.stats import truncnorm  # type: ignore


def dist_deterministic(mean, rng):
    return mean


def dist_exponential(mean, rng):
    return rng.exponential(scale=mean)


def dist_uniform(mean, rng):
    return rng.uniform(low=mean * 0.5, high=mean * 1.5)


def dist_normal(mean, rng):
    sigma = mean * 0.1
    a = (1 - mean) / sigma
    b = np.inf
    return truncnorm.rvs(a, b, loc=mean, scale=sigma, random_state=rng)


def dist_normal_wide(mean, rng):
    sigma = mean * 0.5
    a = (1 - mean) / sigma
    b = np.inf
    return truncnorm.rvs(a, b, loc=mean, scale=sigma, random_state=rng)


def dist_normal_wide_truncated(mean, rng):
    sigma = mean * 0.5
    lower_bound = mean * 0.75
    a = (lower_bound - mean) / sigma
    b = np.inf
    return truncnorm.rvs(a, b, loc=mean, scale=sigma, random_state=rng)


def dist_gamma_k2(mean, rng):
    k = 2.0
    theta = mean / k
    return rng.gamma(shape=k, scale=theta)


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
    "normal_wide": dist_normal_wide,
    "normal_wide_trunc": dist_normal_wide_truncated,
    "gamma_k2": dist_gamma_k2,
    "bimodal": dist_bimodal,
}
