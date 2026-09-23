"""Test TigerGraph connection and prepare for schema creation"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TG_HOST = os.getenv("TG_HOST")
TG_API_TOKEN = os.getenv("TG_API_TOKEN")
TG_TGCLOUD = os.getenv("TG_TGCLOUD", "true").lower() == "true"

print("TigerGraph Connection Details:")
print(f"  Host: {TG_HOST}")
print(f"  Cloud Mode: {TG_TGCLOUD}")
print(f"  API Token: {'*' * 20}{TG_API_TOKEN[-10:] if TG_API_TOKEN else 'NOT SET'}")

# Try importing pyTigerGraph
try:
    import pyTigerGraph as tg
    print("\n✓ pyTigerGraph is available")
    
    # Try creating connection
    try:
        conn = tg.TigerGraphConnection(
            host=TG_HOST,
            apiToken=TG_API_TOKEN,
            tgCloud=TG_TGCLOUD
        )
        print("✓ Connection object created")
        
        # Test connection
        version = conn.getVer()
        print(f"✓ Connected to TigerGraph version: {version}")
        
        # List graphs
        graphs = conn.getGraphList()
        print(f"✓ Existing graphs: {graphs}")
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nNote: This might be normal if graph doesn't exist yet")
        
except ImportError:
    print("\n✗ pyTigerGraph not installed")
    print("Install with: pip install pyTigerGraph")
