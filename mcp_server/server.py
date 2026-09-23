"""
MCP Server for TigerGraph fraud investigation tools
Connects to real TigerGraph when available, falls back to mock data otherwise.
"""

import json
import os
from typing import Any, Dict
from mcp_server.tool_definitions import (
    TOOL_DEFINITIONS,
    TxnNeighborhoodInput,
    SharedDevicesInput,
    SharedCardsInput,
    VelocityCheckInput,
    SimilarCasesInput
)
from mcp_server.mock_graph_data import (
    generate_transaction_neighborhood,
    generate_shared_devices,
    generate_velocity_check,
    generate_similar_past_cases,
    generate_linked_cards
)

try:
    from pyTigerGraph import TigerGraphConnection
    TIGERGRAPH_AVAILABLE = True
except ImportError:
    TIGERGRAPH_AVAILABLE = False
    TigerGraphConnection = None


class TigerGraphMCPServer:
    def __init__(self):
        self.tools = TOOL_DEFINITIONS
        self.call_count = 0
        self.use_tigergraph = False
        self.tigergraph_conn = None

        if TIGERGRAPH_AVAILABLE:
            self._try_connect_tigergraph()
        else:
            print("Warning: pyTigerGraph not installed, using mock data only")

    def _try_connect_tigergraph(self):
        try:
            host = os.getenv("TG_HOST", "http://localhost:14240")
            graphname = os.getenv("TG_GRAPH_NAME", "FraudInvestigation")
            api_token = os.getenv("TG_API_TOKEN", "")
            is_cloud = os.getenv("TG_TGCLOUD", "").lower() == "true"

            self.tigergraph_conn = TigerGraphConnection(
                host=host,
                graphname=graphname,
                apiToken=api_token,
                tgCloud=is_cloud,
            )

            echo = self.tigergraph_conn.echo()
            print(f"Connected to TigerGraph: {echo}")
            self.use_tigergraph = True

        except Exception as e:
            print(f"Warning: Failed to connect to TigerGraph: {e}")
            print("Falling back to mock graph data")
            self.use_tigergraph = False
            self.tigergraph_conn = None

    def list_tools(self) -> list:
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"].schema(),
            }
            for tool in self.tools.values()
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        self.call_count += 1

        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        tool_def = self.tools[tool_name]

        try:
            input_schema = tool_def["input_schema"]
            validated_input = input_schema(**arguments)
        except Exception as e:
            return {"error": f"Invalid input: {str(e)}"}

        try:
            if tool_name == "get_txn_neighborhood":
                result = self._handle_txn_neighborhood_tigergraph(validated_input) if self.use_tigergraph else self._handle_txn_neighborhood_mock(validated_input)
            elif tool_name == "find_shared_devices":
                result = self._handle_shared_devices_tigergraph(validated_input) if self.use_tigergraph else self._handle_shared_devices_mock(validated_input)
            elif tool_name == "find_shared_cards":
                result = self._handle_shared_cards_tigergraph(validated_input) if self.use_tigergraph else self._handle_shared_cards_mock(validated_input)
            elif tool_name == "velocity_check":
                result = self._handle_velocity_check_tigergraph(validated_input) if self.use_tigergraph else self._handle_velocity_check_mock(validated_input)
            elif tool_name == "get_similar_past_cases":
                result = self._handle_similar_cases_tigergraph(validated_input) if self.use_tigergraph else self._handle_similar_cards_mock(validated_input)
            else:
                return {"error": f"Tool not implemented: {tool_name}"}

            return {"success": True, "result": result}

        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    # ── TigerGraph handlers ────────────────────────────────────────────────────

    def _handle_txn_neighborhood_tigergraph(self, input_data: TxnNeighborhoodInput) -> Dict[str, Any]:
        results = self.tigergraph_conn.runInstalledQuery(
            "get_txn_neighborhood",
            params={
                "transaction_id": input_data.transaction_id,
                "card_id":        input_data.card_id,
                "customer_id":    input_data.customer_id,
                "hops":           input_data.hops,
            }
        )
        if not results:
            return self._get_empty_txn_neighborhood()

        merged = {}
        for block in results:
            merged.update(block)

        txn  = (merged.get("transaction") or [{}])[0]
        card = (merged.get("card") or [{}])[0]
        cust = (merged.get("customer") or [{}])[0]
        dev_list = merged.get("device") or []
        dev = dev_list[0] if dev_list else None

        recent_raw = merged.get("recent_transactions") or []
        recent = [
            {
                "transaction_id": r.get("txn_id", ""),
                "amount":         float(r.get("amount", 0)),
                "timestamp":      r.get("ts", ""),
                "channel":        r.get("channel", ""),
                "product_cd":     r.get("product_cd", ""),
                "risk_score":     float(r.get("risk_score", 0)),
            }
            for r in recent_raw
        ]

        return {
            "transaction": {
                "transaction_id": txn.get("transaction_id", input_data.transaction_id),
                "amount":         float(txn.get("amount", 0)),
                "timestamp":      str(txn.get("ts", "")),
                "channel":        txn.get("channel", ""),
                "product_cd":     txn.get("product_cd", ""),
                "risk_score":     float(txn.get("risk_score", 0)),
                "addr1":          float(txn.get("addr1", 0)),
                "addr2":          float(txn.get("addr2", 0)),
                "p_email_domain": txn.get("p_email_domain", ""),
            },
            "card": {
                "card_id":     card.get("card_id", input_data.card_id),
                "customer_id": card.get("customer_id", input_data.customer_id),
                "network":     card.get("card_network", ""),
                "type":        card.get("card_type", ""),
                "issued_date": str(card.get("created_at", "")),
            },
            "customer": {
                "customer_id":            cust.get("customer_id", input_data.customer_id),
                "account_age_days":       0,
                "total_transactions":     len(recent),
                "avg_transaction_amount": (sum(r["amount"] for r in recent) / len(recent)) if recent else 0.0,
                "fraud_history_count":    0,
            },
            "device": {
                "device_id":   dev.get("device_id", ""),
                "device_type": dev.get("device_type", ""),
                "device_info": dev.get("device_info", ""),
                "os":          dev.get("os", ""),
                "browser":     dev.get("browser", ""),
            } if dev else None,
            "recent_transactions": recent,
            "risk_signals":        merged.get("risk_signals") or [],
            "query_metadata": {
                "hops":              input_data.hops,
                "execution_time_ms": 0,
                "vertices_examined": len(recent) + 3,
            },
        }

    def _handle_shared_devices_tigergraph(self, input_data: SharedDevicesInput) -> Dict[str, Any]:
        results = self.tigergraph_conn.runInstalledQuery(
            "find_shared_devices",
            params={"card_id": input_data.card_id, "time_window_hours": input_data.time_window_hours}
        )
        if not results:
            return self._get_empty_shared_devices()

        merged = {}
        for block in results:
            merged.update(block)

        dev_list   = merged.get("device") or []
        dev        = dev_list[0] if dev_list else {}
        shared_ids = merged.get("shared_card_ids") or []
        case_ids   = list(merged.get("linked_case_ids") or [])
        n          = len(shared_ids)
        pattern    = "fraud_ring" if n >= 5 else ("shared_device" if n >= 2 else "normal_usage")

        return {
            "device": {
                "device_id":   dev.get("device_id", ""),
                "device_type": dev.get("device_type", ""),
                "device_info": dev.get("device_info", ""),
                "os":          dev.get("os", ""),
                "browser":     dev.get("browser", ""),
            } if dev else None,
            "shared_cards":        [{"card_id": cid, "link_type": "shared_device"} for cid in shared_ids],
            "time_window_hours":   input_data.time_window_hours,
            "pattern":             pattern,
            "linked_closed_cases": case_ids,
            "risk_level":          "high" if n >= 5 else ("medium" if n >= 2 else "low"),
        }

    def _handle_shared_cards_tigergraph(self, input_data: SharedCardsInput) -> Dict[str, Any]:
        results = self.tigergraph_conn.runInstalledQuery(
            "find_shared_cards",
            params={"card_id": input_data.card_id}
        )
        if not results:
            return self._get_empty_shared_cards()

        merged = {}
        for block in results:
            merged.update(block)

        links_raw    = merged.get("linked_cards") or []
        cluster_size = int(merged.get("cluster_size") or 1)
        linked_cards = [
            {
                "card_id":   lnk.get("linked_card_id", ""),
                "link_type": lnk.get("link_type", ""),
                "strength":  float(lnk.get("strength", 0)),
            }
            for lnk in links_raw
        ]
        n = len(linked_cards)

        return {
            "card_id":      input_data.card_id,
            "linked_cards": linked_cards,
            "cluster_id":   None,
            "cluster_size": cluster_size,
            "risk_level":   "high" if n >= 5 else ("medium" if n >= 2 else "low"),
        }

    def _handle_velocity_check_tigergraph(self, input_data: VelocityCheckInput) -> Dict[str, Any]:
        results = self.tigergraph_conn.runInstalledQuery(
            "velocity_check",
            params={"card_id": input_data.card_id, "time_window_minutes": input_data.time_window_minutes}
        )
        if not results:
            return self._get_empty_velocity_check()

        merged = {}
        for block in results:
            merged.update(block)

        txns_raw = merged.get("transactions") or []
        count    = int(merged.get("transaction_count") or 0)
        typical  = float(merged.get("typical_velocity") or 0)

        txns = [
            {
                "transaction_id": t.get("txn_id", ""),
                "amount":         float(t.get("amount", 0)),
                "timestamp":      t.get("ts", ""),
                "channel":        t.get("channel", ""),
            }
            for t in txns_raw
        ]

        hours            = input_data.time_window_minutes / 60.0
        current_velocity = count / hours if hours else count
        velocity_ratio   = (current_velocity / typical) if typical else 1.0

        if velocity_ratio > 5 or count > 10:
            pattern = "card_testing"
        elif velocity_ratio > 2:
            pattern = "high_velocity"
        else:
            pattern = "normal"

        return {
            "card_id":                   input_data.card_id,
            "time_window_minutes":       input_data.time_window_minutes,
            "transaction_count":         count,
            "transactions":              txns,
            "pattern_detected":          pattern,
            "typical_velocity_for_card": typical,
            "current_velocity":          current_velocity,
            "velocity_ratio":            velocity_ratio,
            "risk_level":                "high" if pattern == "card_testing" else ("medium" if pattern == "high_velocity" else "low"),
        }

    def _handle_similar_cases_tigergraph(self, input_data: SimilarCasesInput) -> Dict[str, Any]:
        results = self.tigergraph_conn.runInstalledQuery(
            "get_similar_past_cases",
            params={
                "pattern":   input_data.pattern,
                "device_id": input_data.device_id,
                "card_id":   input_data.card_id,
            }
        )
        if not results:
            return {"cases": [], "query_metadata": {"total_cases_examined": 0, "cases_returned": 0, "execution_time_ms": 0}}

        merged = {}
        for block in results:
            merged.update(block)

        cases_raw = merged.get("cases") or []
        cases = [
            {
                "case_id":          c.get("case_id", ""),
                "outcome":          c.get("status", ""),
                "pattern":          c.get("pattern_name", ""),
                "opened_at":        "",
                "closed_at":        "",
                "exposure_usd":     float(c.get("exposure", 0)),
                "n_txns":           int(c.get("n_txns", 0)),
                "actions_taken":    c.get("actions_taken", ""),
                "report_filed":     bool(c.get("report_filed", False)),
                "analyst_notes":    c.get("analyst_notes", ""),
                "match_reason":     "pattern_and_graph_proximity",
                "similarity_score": float(c.get("similarity_score", 0)),
            }
            for c in cases_raw
        ]

        return {
            "cases": cases,
            "query_metadata": {
                "total_cases_examined": int(merged.get("total_returned") or len(cases)),
                "cases_returned":       len(cases),
                "execution_time_ms":    0,
            },
        }

    # ── Mock handlers ──────────────────────────────────────────────────────────

    def _handle_txn_neighborhood_mock(self, input_data: TxnNeighborhoodInput) -> Dict[str, Any]:
        scenario = self._infer_scenario(input_data.card_id)
        return generate_transaction_neighborhood(
            txn_id=input_data.transaction_id,
            card_id=input_data.card_id,
            customer_id=input_data.customer_id,
            scenario=scenario
        )

    def _handle_shared_devices_mock(self, input_data: SharedDevicesInput) -> Dict[str, Any]:
        scenario = self._infer_scenario(input_data.card_id)
        return generate_shared_devices(
            card_id=input_data.card_id,
            scenario="fraud_ring" if scenario == "suspicious" else "normal"
        )

    def _handle_shared_cards_mock(self, input_data: SharedCardsInput) -> Dict[str, Any]:
        scenario = self._infer_scenario(input_data.card_id)
        return generate_linked_cards(
            card_id=input_data.card_id,
            scenario="fraud_ring" if scenario == "suspicious" else "normal"
        )

    def _handle_velocity_check_mock(self, input_data: VelocityCheckInput) -> Dict[str, Any]:
        scenario = self._infer_scenario(input_data.card_id)
        return generate_velocity_check(
            card_id=input_data.card_id,
            scenario="testing" if scenario == "suspicious" else "normal"
        )

    def _handle_similar_cards_mock(self, input_data: SimilarCasesInput) -> Dict[str, Any]:
        result = generate_similar_past_cases(
            pattern=input_data.pattern,
            device_id=input_data.device_id,
            card_id=input_data.card_id
        )
        return {
            "cases": result,
            "query_metadata": {
                "total_cases_examined": 5565,
                "cases_returned": len(result),
                "execution_time_ms": 85
            }
        }

    # ── Empty result helpers ───────────────────────────────────────────────────

    def _get_empty_txn_neighborhood(self) -> Dict[str, Any]:
        return {
            "transaction": {
                "transaction_id": "", "amount": 0.0, "timestamp": "",
                "channel": "", "product_cd": "", "risk_score": 0.0,
                "addr1": 0.0, "addr2": 0.0, "p_email_domain": ""
            },
            "card": {"card_id": "", "customer_id": "", "network": "", "type": "", "issued_date": ""},
            "customer": {
                "customer_id": "", "account_age_days": 0,
                "total_transactions": 0, "avg_transaction_amount": 0.0, "fraud_history_count": 0
            },
            "device": None,
            "recent_transactions": [],
            "risk_signals": [],
            "query_metadata": {"hops": 2, "execution_time_ms": 0, "vertices_examined": 0}
        }

    def _get_empty_shared_devices(self) -> Dict[str, Any]:
        return {
            "device": None, "shared_cards": [], "time_window_hours": 0,
            "pattern": "normal_usage", "linked_closed_cases": [], "risk_level": "low"
        }

    def _get_empty_shared_cards(self) -> Dict[str, Any]:
        return {"card_id": "", "linked_cards": [], "cluster_id": None, "cluster_size": 1, "risk_level": "low"}

    def _get_empty_velocity_check(self) -> Dict[str, Any]:
        return {
            "card_id": "", "time_window_minutes": 0, "transaction_count": 0,
            "transactions": [], "pattern_detected": "normal",
            "typical_velocity_for_card": 0.0, "current_velocity": 0.0,
            "velocity_ratio": 0.0, "risk_level": "low"
        }

    def _infer_scenario(self, identifier: str) -> str:
        digits = ''.join(c for c in identifier if c.isdigit())
        seed = int(digits) % 97 if digits else hash(identifier) & 0xFF
        if seed % 5 == 0:
            return "legitimate"
        elif seed % 5 <= 1:
            return "uncertain"
        else:
            return "suspicious"


_server_instance = None


def get_server() -> TigerGraphMCPServer:
    global _server_instance
    if _server_instance is None:
        _server_instance = TigerGraphMCPServer()
    return _server_instance


if __name__ == "__main__":
    print("MCP Server for TigerGraph Fraud Investigation")
    print("=" * 60)

    server = get_server()

    print("\nAvailable Tools:")
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description'][:80]}...")

    print("\n" + "=" * 60)
    print("Testing get_txn_neighborhood tool...")
    print("=" * 60)

    result = server.call_tool("get_txn_neighborhood", {
        "transaction_id": "3478782",
        "card_id": "C11891-K1",
        "customer_id": "C11891",
        "hops": 2
    })

    if result.get("success"):
        print("\nTool executed successfully")
        print(json.dumps(result["result"]["transaction"], indent=2))
        print(f"Risk signals: {result['result']['risk_signals']}")
        print(f"Recent transactions: {len(result['result']['recent_transactions'])}")
    else:
        print(f"\nTool failed: {result.get('error')}")
