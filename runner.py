#!/usr/bin/env python3
"""Discover all environment and air quality sensor device_classes and units in the user's HA."""

import json
import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
sys.path.insert(0, os.path.abspath("addons/antigravity-cli"))
from core.ha_client import get_ha_states

states = get_ha_states()
env_sensors = []
env_classes = {
    "temperature", "humidity", "carbon_dioxide", "co2", "volatile_organic_compounds", 
    "voc", "aqi", "pm25", "pm10", "pm1", "illuminance", "pressure", "atmospheric_pressure",
    "carbon_monoxide", "ozone", "nitrogen_dioxide", "nitrogen_monoxide", "radon", "sulphur_dioxide"
}

print(f"[*] Total states fetched: {len(states)}")
found_metrics = {}

for s in states:
    eid = s.get("entity_id", "")
    if eid.startswith("sensor.") or eid.startswith("air_quality."):
        attrs = s.get("attributes", {})
        dclass = attrs.get("device_class", "")
        uom = attrs.get("unit_of_measurement", "")
        fn = attrs.get("friendly_name", "")
        state = s.get("state", "")
        
        # Check matching keywords or device_class
        for ec in env_classes:
            if ec in dclass or ec in eid.lower() or ec in fn.lower() or any(k in fn.lower() for k in ["co2", "이산화탄소", "tvoc", "voc", "미세먼지", "초미세먼지", "공기질", "조도", "기압"]):
                found_metrics[eid] = {
                    "friendly_name": fn,
                    "state": state,
                    "unit": uom,
                    "device_class": dclass
                }
                break

print("\n[*] Discovered Environment & Air Quality Sensors:")
for eid, data in found_metrics.items():
    print(f"  • {eid} | {data['friendly_name']}: {data['state']} {data['unit']} (class: {data['device_class']})")
