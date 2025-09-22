#!/usr/bin/env python3
"""
Script to verify that a simulation JSON file follows the schema defined in simulation_models.py
"""

import json
import sys
from pathlib import Path
from pydantic import ValidationError

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from thinkrl.simulation_models import FilteredSimulationRuns


def verify_simulation_schema(json_file_path: str) -> bool:
    """
    Verify that a simulation JSON file follows the FilteredSimulationRuns schema.

    Args:
        json_file_path: Path to the JSON file to verify

    Returns:
        True if the file follows the schema, False otherwise
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        print(f"Loading JSON file: {json_file_path}")
        print(f"Found {len(data.get('simulations', []))} simulations")

        # Attempt to parse with Pydantic model
        simulation_runs = FilteredSimulationRuns(**data)

        print("✅ Schema validation PASSED")
        print(f"Validated {len(simulation_runs.simulations)} simulation runs")

        # Print some basic info about the data
        print(f"\nData summary:")
        print(f"- Timestamp: {simulation_runs.timestamp}")
        print(f"- Domain: {simulation_runs.info.environment_info.domain_name}")
        print(f"- Git commit: {simulation_runs.info.git_commit}")
        print(f"- Number of simulations: {len(simulation_runs.simulations)}")

        # Check if any simulations have judgments
        with_judgments = sum(1 for sim in simulation_runs.simulations if sim.judgment is not None)
        print(f"- Simulations with judgments: {with_judgments}")

        if with_judgments > 0:
            # Show judgment summary
            verdicts = [sim.judgment.verdict for sim in simulation_runs.simulations if sim.judgment is not None]
            pass_count = sum(1 for v in verdicts if v == "PASS")
            fail_count = sum(1 for v in verdicts if v == "FAIL")
            print(f"  - PASS: {pass_count}")
            print(f"  - FAIL: {fail_count}")

        return True

    except FileNotFoundError:
        print(f"❌ Error: File not found: {json_file_path}")
        return False

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        return False

    except ValidationError as e:
        print(f"❌ Schema validation FAILED:")
        print(f"Pydantic validation error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function to run the verification"""
    if len(sys.argv) != 2:
        print("Usage: python verify_simulation_schema.py <path_to_json_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]

    success = verify_simulation_schema(json_file_path)

    if not success:
        sys.exit(1)

    print("\n🎉 Verification completed successfully!")


if __name__ == "__main__":
    main()