from pathlib import Path
import subprocess
import sys


def run_script(script_path):
    print(f"\nStart: {script_path.name}")
    result = subprocess.run([sys.executable, str(script_path)])
    if result.returncode != 0:
        raise RuntimeError(f"Error during execution of {script_path}")


def main():
    base_dir = Path(__file__).resolve().parent.parent

    simulation_script = base_dir / "simulation" / "cavia_simulation" / "cavia_simulation.py"
    verify_script = base_dir / "analysis" / "verify_cavia_mean.py"
    aggregate_script = base_dir / "analysis" / "aggregate_datapacket_user.py"

    run_script(simulation_script)
    run_script(verify_script)
    run_script(aggregate_script)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
