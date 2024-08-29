import csv
import os
import subprocess
import sys

def read_csv(csv_path):
    """Reads the CSV file and returns the content."""
    data = []
    try:
        with open(csv_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Error: The file {csv_path} does not exist.")
        sys.exit(1)
    return data

def generate_graph_from_csv(csv_path):
    """Generates a graph from CSV data."""
    # Check if the CSV file exists
    if not os.path.isfile(csv_path):
        print(f"CSV file '{csv_path}' does not exist.")
        return

    # Prepare the command to generate the graph
    command = [
        'python', '-m', 'graphrag.index',
        '--root', csv_path  # Adjust according to valid options
    ]

    try:
        # Run the command
        subprocess.run(command, check=True)
        print("Graph has been generated.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while generating the graph: {e}")

if __name__ == "__main__":
    # Prompt user for CSV file path
    csv_file_path = input("Enter the path to the CSV file: ")

    # Read data from CSV (for validation or processing, if needed)
    data = read_csv(csv_file_path)

    # Generate the graph from the CSV file
    generate_graph_from_csv(csv_file_path)
