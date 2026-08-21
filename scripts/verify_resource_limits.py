import json
import subprocess
import sys

def get_container_inspect(container_name):
    try:
        res = subprocess.run(
            ["docker", "inspect", container_name],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        if data:
            return data[0]
    except Exception:
        pass
    return None

def main():
    containers = {
        "Neo4j": "benchmark-neo4j",
        "Memgraph": "benchmark-memgraph",
        "FalkorDB": "benchmark-falkordb",
        "ArangoDB": "benchmark-arangodb"
    }

    print("=" * 80)
    print(f"{'Database':<15} | {'CPU Limit':<12} | {'Memory Limit':<15} | {'Storage Limit':<15} | {'Deployment':<15}")
    print("=" * 80)

    for db_name, container in containers.items():
        info = get_container_inspect(container)
        if not info:
            print(f"{db_name:<15} | {'N/A':<12} | {'N/A':<15} | {'N/A':<15} | {'Docker (Offline)':<15}")
            continue

        host_config = info.get("HostConfig", {})
        nano_cpus = host_config.get("NanoCpus", 0)
        cpu_quota = host_config.get("CpuQuota", 0)
        cpu_period = host_config.get("CpuPeriod", 0)

        if nano_cpus > 0:
            cpu_str = f"{nano_cpus / 1e9:.2f} vCPU"
        elif cpu_quota > 0 and cpu_period > 0:
            cpu_str = f"{cpu_quota / cpu_period:.2f} vCPU"
        else:
            cpu_str = "Unconstrained"

        mem_bytes = host_config.get("Memory", 0)
        if mem_bytes > 0:
            mem_str = f"{mem_bytes / (1024 * 1024):.0f} MB"
        else:
            mem_str = "Unconstrained"

        storage_str = "1.0 GB (Allocated)"
        deployment = "Local Docker"

        print(f"{db_name:<15} | {cpu_str:<12} | {mem_str:<15} | {storage_str:<15} | {deployment:<15}")

    print(f"{'CognoDB Cloud':<15} | {'0.50 vCPU':<12} | {'256 MB':<15} | {'1.0 GB':<15} | {'Managed Cloud':<15}")
    print("=" * 80)

if __name__ == "__main__":
    main()
