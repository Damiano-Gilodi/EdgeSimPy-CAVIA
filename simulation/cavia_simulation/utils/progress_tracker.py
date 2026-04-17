import json


def make_progress_key(distribution, scenario, app):
    return f"{distribution}|{scenario}|{app}"


def load_completed_apps(progress_file):
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_completed_apps(progress_file, completed_apps):
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(sorted(completed_apps), f, indent=4)


def is_app_marked_completed(completed_apps, distribution, scenario, app):
    return make_progress_key(distribution, scenario, app) in completed_apps


def mark_app_completed(completed_apps, distribution, scenario, app):
    completed_apps.add(make_progress_key(distribution, scenario, app))
