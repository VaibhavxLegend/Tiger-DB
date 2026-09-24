
from dotenv import load_dotenv
load_dotenv()
import os, pyTigerGraph as tg
host = os.getenv("TG_HOST")
graph = os.getenv("TG_GRAPH_NAME","FraudInvestigation")
conn = tg.TigerGraphConnection(host=host, graphname=graph, username="tigergraph", password="tigergraph", apiToken=os.getenv("TG_API_TOKEN"))
# Pull 20 cases via GSQL reference
res = conn.gsql("SELECT case_id FROM case_pack LIMIT 20")
print("Live cases:", res)
# Export transactions / identity via loading job patterns
print("Graph connect OK")
