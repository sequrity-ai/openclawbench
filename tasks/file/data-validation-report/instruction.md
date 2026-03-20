# Data Validation Report

Validate the data quality in /workspace/inventory.csv. Create a JSON file named 'validation_report.json' in /workspace that identifies all data quality issues including: 1) missing_values (items with empty/null name, price, or category fields), 2) invalid_quantities (negative quantities), 3) duplicate_items (items with the same name appearing multiple times). For each issue type, list the item_ids affected and count the total issues.
