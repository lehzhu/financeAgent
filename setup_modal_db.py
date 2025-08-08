"""
Setup script to upload the SQLite database to Modal volume
"""

import modal
import os
import shutil

app = modal.App("setup-finance-db",
    image=(modal.Image.debian_slim()
           .pip_install("sqlite-utils")
           .add_local_dir(os.path.dirname(__file__), remote_path="/root/app")  # repo root
          )
)

# Create or get the volume
volume = modal.Volume.from_name("finance-agent-storage", create_if_missing=True)

@app.function(
    volumes={"/data": volume},
    timeout=600
)
def setup_database():
    """Upload the database and related files to Modal volume."""
    import sqlite3
    
    print("Setting up database in Modal volume...")
    
    # Build DB from ingestion script using repo files under /root/app/data
    import subprocess
    py = "/usr/local/bin/python" if os.path.exists("/usr/local/bin/python") else "python3"
    ingester = "/root/app/data/ingest_costco_10k.py"
    assert os.path.exists(ingester), "ingest script missing in image"
    print("Running ingestion...")
    subprocess.check_call([py, ingester])

    # Copy built DB into Modal volume
    built_db = "/root/app/data/costco_financial_data.db"
    if os.path.exists(built_db):
        shutil.copy(built_db, "/data/costco_financial_data.db")
        print("✓ Database copied to /data/costco_financial_data.db")

        # Verify database
        conn = sqlite3.connect("/data/costco_financial_data.db")
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✓ Found tables: {[t[0] for t in tables]}")
        
        # Check row count
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} rows")
        
        conn.close()
    else:
        print("✗ Database file not found!")
    
    # Copy FAISS index for narrative search
    narrative_files = [
        "narrative_kb_index/index.faiss",
        "narrative_kb_index/index.pkl"
    ]
    
    for file in narrative_files:
        src = f"/tmp/data/{file}"
        dst = f"/data/{file}"
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
            print(f"✓ Copied {file}")
    
    # List all files in volume
    print("\nFiles in Modal volume:")
    for root, dirs, files in os.walk("/data"):
        for file in files:
            path = os.path.join(root, file)
            size = os.path.getsize(path) / 1024 / 1024  # MB
            print(f"  {path} ({size:.2f} MB)")
    
    return "Database setup complete!"

@app.local_entrypoint()
def main():
    """Run the setup."""
    result = setup_database.remote()
    print(f"\n{result}")

if __name__ == "__main__":
    main()
