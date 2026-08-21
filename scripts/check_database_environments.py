import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import yaml

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from databases import ADAPTER_REGISTRY

def check_environments():
    config_path = project_root / "config" / "databases.yaml"
    db_configs = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            db_configs = data.get("databases", {})

    print("Database environment checks\n")
    print(f"{'Database':<16} {'Status':<16} {'Version':<24} {'Protocol':<12}")
    print("-" * 70)

    overall_configured = 0
    overall_passed = 0
    failures = 0

    for key, adapter_class in ADAPTER_REGISTRY.items():
        db_conf = db_configs.get(key, {})
        display_name = db_conf.get("name", key.capitalize())
        adapter = adapter_class(name=display_name, config=db_conf)
        protocol = db_conf.get("protocol", "unknown")

        if not adapter.is_configured():
            print(f"{display_name:<16} {'NOT CONFIGURED':<16} {'not configured':<24} {protocol:<12}")
            continue

        overall_configured += 1
        try:
            passed = adapter.verify_connection()
            if passed:
                info = adapter.get_database_info()
                version = info.get("version", "unknown")
                print(f"{display_name:<16} {'PASS':<16} {version:<24} {protocol:<12}")
                overall_passed += 1
            else:
                print(f"{display_name:<16} {'FAIL':<16} {'unreachable':<24} {protocol:<12}")
                failures += 1
        except Exception:
            print(f"{display_name:<16} {'FAIL':<16} {'error':<24} {protocol:<12}")
            failures += 1
        finally:
            adapter.disconnect()

    print("-" * 70)
    print(f"Summary: {overall_passed}/{overall_configured} configured environments verified successfully.")

    if failures > 0:
        sys.exit(1)

if __name__ == "__main__":
    check_environments()
