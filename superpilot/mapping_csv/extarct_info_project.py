import os
import ast
import csv

# Function to extract function and class names from a Python file
def extract_info_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        # Parse the contents into an Abstract Syntax Tree (AST)
        tree = ast.parse(file.read(), filename=file_path)
    
    # Extract all function names in the file
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    # Extract all class names in the file
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    return functions, classes

# Function to go through the project directory and collect information
def extract_info_from_directory(directory_path):
    data = []  # List to store all extracted information
    ignore_dirs = {"__pycache__", "myenv", ".git"}  # Directories to ignore
    
    # Walk through the directory, including all subdirectories
    for root, dirs, files in os.walk(directory_path):
        # Skip directories we want to ignore
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        folder_name = os.path.relpath(root, directory_path)  # Get the relative path of the folder
        
        # Process each file in the current directory
        for file in files:
            # Only consider Python files (ending with .py)
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                # Extract function and class names from the file
                functions, classes = extract_info_from_file(file_path)
                
                # Add each function as a separate row in the data list
                for func in functions:
                    data.append({
                        "Folder": folder_name,  # Folder name or path relative to the base directory
                        "File": file,  # Name of the Python file
                        "Function": func,  # Function name
                        "Class": ""  # Leave class blank as we're focusing on functions
                    })
                
                for cls in classes:
                    data.append({
                        "Folder": folder_name,  # Folder name or path relative to the base directory
                        "File": file,  # Name of the Python file
                        "Function": "",  # Leave function blank as we're focusing on classes
                        "Class": cls  # Class name
                    })
    
    return data

# Function to save the collected information into a CSV file
def save_to_csv(data, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        # Define the column headers for the CSV
        fieldnames = ["Folder", "File", "Function", "Class"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()  # Write the header row
        for row in data:
            writer.writerow(row)  # Write each row of data

# Main function to run the script
if __name__ == "__main__":
    # Ask the user to input the path to the project directory
    project_directory = input("Enter the path to the project directory: ")
    
    # Define the output CSV file name
    output_csv = "project_structure.csv"
    
    # Extract the information from the directory
    extracted_data = extract_info_from_directory(project_directory)
    
    # Save the extracted information to the CSV file
    save_to_csv(extracted_data, output_csv)
    
    print(f"Data extracted and saved to {output_csv}")
