import os

def write_directory_structure(root_dir, file):
    for root, dirs, files in os.walk(root_dir):
        # Write the current directory path
        file.write(f"{root}\n")
        
        # Write all subdirectories
        for dir_name in dirs:
            file.write(f"  {dir_name}/\n")
        
        # Write all files
        for file_name in files:
            file.write(f"  {file_name}\n")

def main():
    # Ask user for the root directory of the project
    root_directory = input("Enter the path of the project directory: ").strip()
    
    # Validate the directory path
    if not os.path.isdir(root_directory):
        print("The specified path does not exist or is not a directory.")
        return
    
    # Specify the path for the output text file
    output_file_path = 'project_structure.txt'
    
    # Write the directory structure to the text file
    with open(output_file_path, 'w') as file:
        write_directory_structure(root_directory, file)
    
    print(f"Project structure has been written to {output_file_path}")

if __name__ == "__main__":
    main()
