import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import yaml

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from databases import ADAPTER_REGISTRY

def test_connections():
    config_path = project_root / "config" / "databases.yaml"
    db_configs = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            db_configs = data.get("databases", {})

    print("Database connection checks\n")

    overall_configured = 0
    overall_passed = 0
    failures = 0

    for key, adapter_class in ADAPTER_REGISTRY.items():
        db_conf = db_configs.get(key, {})
        display_name = db_conf.get("name", key.capitalize())
        adapter = adapter_class(name=display_name, config=db_conf)

        if not adapter.is_configured():
            print(f"{display_name}: NOT CONFIGURED")
            continue

        overall_configured += 1
        try:
            passed = adapter.verify_connection()
            if passed:
                print(f"{display_name}: PASS")
                overall_passed += 1
            else:
                print(f"{display_name}: FAIL (verification query returned invalid result)")
                failures += 1
        except Exception as e:
            print(f"{display_name}: FAIL ({type(e).__name__})")
            failures += 1
        finally:
            adapter.disconnect()

    print()
    print(f"Summary: {overall_passed}/{overall_configured} configured databases connected successfully.")

    if failures > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_connections()
