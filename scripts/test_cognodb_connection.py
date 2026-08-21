import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

uri = os.getenv("COGNODB_URI")
username = os.getenv("COGNODB_USERNAME")
password = os.getenv("COGNODB_PASSWORD")

if not uri or not username or not password:
    print("Error: Missing required environment variables.", file=sys.stderr)
    print("Ensure COGNODB_URI, COGNODB_USERNAME, and COGNODB_PASSWORD are set in your .env file.", file=sys.stderr)
    sys.exit(1)

try:
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()
            if record and record["test"] == 1:
                print("Connection to CognoDB verified successfully.")
                print(f"Query response: {record['test']}")
            else:
                print("Query did not return expected output.", file=sys.stderr)
                sys.exit(1)
except exceptions.AuthError:
    print("Authentication failed: invalid username or password.", file=sys.stderr)
    sys.exit(1)
except exceptions.ServiceUnavailable as e:
    print(f"Service unavailable or unreachable: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Unexpected connection error: {e}", file=sys.stderr)
    sys.exit(1)
