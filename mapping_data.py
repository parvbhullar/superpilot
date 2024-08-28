import os
import csv
import ast

def count_functions(filepath):
    with open(filepath, "r") as file:
        tree = ast.parse(file.read(), filename=filepath)
        return sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))

def traverse_directory(root_dir):
    data = []
    for root, dirs, files in os.walk(root_dir):
        folder_name = os.path.basename(root)
        num_folders = len(dirs)
        num_files = len(files)
        num_functions = sum(count_functions(os.path.join(root, file)) for file in files if file.endswith(".py"))

        data.append({
            "Folder": root,
            "Number of Folders": num_folders,
            "Number of Files": num_files,
            "Number of Functions": num_functions
        })

    return data

def write_csv(data, output_file):
    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Folder", "Number of Folders", "Number of Files", "Number of Functions"])
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    root_directory = "superpilot"  # Replace with your project path
    output_csv = "project_structure.csv"
    data = traverse_directory(root_directory)
    write_csv(data, output_csv)
    print(f"CSV file created: {output_csv}")
