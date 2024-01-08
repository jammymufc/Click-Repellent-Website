import csv
import json

json_data = []

# Define the headers for each column
headers = ["id", "label", "statement", "subject", "speaker", "speaker_job_title", "state_info", "party_affiliation", "barely_true_counts", "false_counts", "half_true_counts", "mostly_true_counts", "pants_on_fire_counts", "context"]

with open('valid.tsv', 'r', encoding='utf-8', newline='') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')

    # Skip the header line
    next(reader, None)

    for row in reader:
        # Create a dictionary mapping headers to values
        row_dict = dict(zip(headers, row))
        
        # Append the dictionary to the list
        json_data.append(row_dict)

# Write the list of dictionaries to a JSON file
with open('valid.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(json_data, jsonfile, indent=2)
