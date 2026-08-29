#!/usr/bin/env python3
"""Inspect exact entity names and states for humidity and battery in each room."""

import json
import urllib.request

url = "http://192.168.0.14:8000/api/status"


def inspect_entities():
    # Let's inspect via Home Assistant API through runner
    from core.ha_engine import get_ha_states
    states = get_ha_states()
    print(f"Total entities fetched: {len(states)}")
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다"]
    
    print("\n--- [Entities with % or 습도] ---")
    for s in states:
        eid = s.get("entity_id", "")
        fn = s.get("attributes", {}).get("friendly_name", "")
        st = s.get("state", "")
        uom = s.get("attributes", {}).get("unit_of_measurement", "")
        device_class = s.get("attributes", {}).get("device_class", "")
        
        if any(r in fn for r in rooms) and (uom == "%" or "습도" in fn or "humidity" in eid):
            print(f"EID: {eid:40} | FN: {fn:30} | State: {st:6} | UOM: {uom:3} | Class: {device_class}")


if __name__ == "__main__":
    inspect_entities()
