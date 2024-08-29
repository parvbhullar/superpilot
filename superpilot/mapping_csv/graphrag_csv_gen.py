import os
import csv

def generate_project_structure_csv(root_directory, output_csv):
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Folder', 'Subfolder', 'File'])

        for root, dirs, files in os.walk(root_directory):
            relative_path = os.path.relpath(root, root_directory)

            if relative_path == '.':
                relative_path = ''  # Root directory itself

            for file in files:
                parts = relative_path.split(os.sep)
                folder = parts[0] if len(parts) > 0 else ''
                subfolder = os.sep.join(parts[1:]) if len(parts) > 1 else ''
                
                writer.writerow([folder, subfolder, file])

if __name__ == "__main__":
    # Ask the user for the project directory
    root_directory = input("Enter the path to your project folder: ")
    
    # Define the output CSV file name
    output_csv = 'project.csv'
    
    # Generate the project structure CSV
    generate_project_structure_csv(root_directory, output_csv)
    
    print(f"CSV file '{output_csv}' has been generated.")
