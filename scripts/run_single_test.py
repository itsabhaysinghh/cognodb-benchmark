import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from benchmark.ingest import IngestBenchmarkEngine

def main():
    engine = IngestBenchmarkEngine(project_root=project_root)
    result = engine.run_single_ingest("cognodb", batch_size=1000)
    print(json.dumps(result, indent=2))
    if result.get("status") != "passed":
        sys.exit(1)

if __name__ == "__main__":
    main()
