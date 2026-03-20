#!/bin/bash
# Reference solution for: File Comparison
cd /workspace

python3 << 'PYEOF'
import configparser

v1 = configparser.ConfigParser()
v1.read("config_v1.ini")
v2 = configparser.ConfigParser()
v2.read("config_v2.ini")

lines = ["Configuration Differences: config_v1.ini vs config_v2.ini", "=" * 50, ""]

all_sections = set(v1.sections()) | set(v2.sections())
for section in sorted(all_sections):
    lines.append(f"[{section}]")
    keys1 = dict(v1.items(section)) if v1.has_section(section) else {}
    keys2 = dict(v2.items(section)) if v2.has_section(section) else {}
    all_keys = set(keys1) | set(keys2)
    for key in sorted(all_keys):
        if key in keys1 and key in keys2:
            if keys1[key] != keys2[key]:
                lines.append(f"  CHANGED: {key} = {keys1[key]} -> {keys2[key]}")
        elif key in keys2:
            lines.append(f"  ADDED: {key} = {keys2[key]}")
        else:
            lines.append(f"  REMOVED: {key} = {keys1[key]}")
    lines.append("")

with open("config_diff.txt", "w") as f:
    f.write("\n".join(lines) + "\n")
PYEOF
