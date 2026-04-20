import subprocess
import sys

from adapters.cavia.utils.path import BASE_PATH


def run_script(script_path):
    print(f"\nStart: {script_path.name}")
    result = subprocess.run([sys.executable, str(script_path)])
    if result.returncode != 0:
        raise RuntimeError(f"Error during execution of {script_path}")


def main():

    simulation_script = BASE_PATH / "scripts" / "run_all_jobs.py"
    verify_script = BASE_PATH / "analysis" / "verify_cavia_mean.py"
    aggregate_script = BASE_PATH / "analysis" / "build_worst_case_dataset.py"

    run_script(simulation_script)
    run_script(verify_script)
    run_script(aggregate_script)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
