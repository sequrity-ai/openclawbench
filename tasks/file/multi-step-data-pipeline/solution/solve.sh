#!/bin/bash
# Reference solution for: Multi-Step Data Pipeline
cd /workspace

python3 << 'PYEOF'
import csv
import json
import xml.etree.ElementTree as ET

with open("reports/employees.csv") as f:
    employees = list(csv.DictReader(f))

with open("reports/departments.json") as f:
    departments = json.load(f)["departments"]

tree = ET.parse("reports/projects.xml")
projects = []
for p in tree.findall(".//project"):
    projects.append({
        "id": int(p.find("id").text),
        "name": p.find("name").text,
        "dept_id": int(p.find("dept_id").text),
        "budget": int(p.find("budget").text),
    })

result = []
for dept in departments:
    did = dept["id"]
    dept_employees = [e for e in employees if int(e["dept_id"]) == did]
    dept_projects = [p for p in projects if p["dept_id"] == did]
    result.append({
        "department": dept["name"],
        "employee_count": len(dept_employees),
        "total_salary": sum(int(e["salary"]) for e in dept_employees),
        "total_project_budget": sum(p["budget"] for p in dept_projects),
    })

with open("department_report.json", "w") as f:
    json.dump(result, f, indent=2)
PYEOF
