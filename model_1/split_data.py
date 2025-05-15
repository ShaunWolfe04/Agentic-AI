import json
import os

# Load the JSON file
with open('medical_o1_sft.json', 'r') as file:
    data = json.load(file)

# Check how many rows there are
num_rows = len(data)
print(f"There are {num_rows} rows in the JSON file.")

# Extract only the 'Question' parts
questions = [{'Question': entry['Question'], "Response": entry["Response"]} for entry in data if "Question" in entry and "Response" in entry]

# Split the data into 10 equal-ish parts
num_parts = 10
part_size = len(questions) // num_parts
remainder = len(questions) % num_parts
file_name = f"Hospital_full_data.json"
with open(file_name, 'w') as output_file:
    json.dump(questions, output_file, indent=4)
start_index = 0
exit()
for i in range(num_parts):
    # Determine the end index for each part
    end_index = start_index + part_size + (1 if i < remainder else 0)

    # Slice the data to create the current part
    part_data = questions[start_index:end_index]

    # Save the part to a new file
    file_name = f"Hospital_{i+1}_qa.json"
    with open(file_name, 'w') as output_file:
        json.dump(part_data, output_file, indent=4)

    # Update the start index for the next part
    start_index = end_index

    print(f"Saved {file_name} with {len(part_data)} rows.")
