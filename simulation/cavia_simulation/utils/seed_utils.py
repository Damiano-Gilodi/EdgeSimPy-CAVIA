import hashlib


def generate_base_seed(scenario, app):
    combined = f"{scenario}|{app}"
    return int(hashlib.md5(combined.encode()).hexdigest(), 16)


def derive_run_seed(base_seed, run_index):
    return int(hashlib.md5(f"{base_seed}_{run_index}".encode()).hexdigest(), 16) % (2**32)
