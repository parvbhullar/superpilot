import os

def generate_project_structure_txt(root_directory, output_txt):
    # Open the output text file in write mode
    with open(output_txt, mode='w') as file:
        # Write the header row
        file.write('Folder\tSubfolder\tFile\n')

        # Walk through the directory tree
        for root, dirs, files in os.walk(root_directory):
            relative_path = os.path.relpath(root, root_directory)

            # Handle the root directory case
            if relative_path == '.':
                relative_path = ''  # Root directory itself

            # Write each file's details
            for filename in files:
                parts = relative_path.split(os.sep)
                folder = parts[0] if len(parts) > 0 else ''
                subfolder = os.sep.join(parts[1:]) if len(parts) > 1 else ''
                
                # Write the details to the file
                file.write(f'{folder}\t{subfolder}\t{filename}\n')

if __name__ == "__main__":
    # Ask the user for the project directory
    root_directory = input("Enter the path to your project folder: ")
    
    # Define the output TXT file name
    output_txt = 'project.txt'
    
    # Generate the project structure TXT
    generate_project_structure_txt(root_directory, output_txt)
    
    print(f"TXT file '{output_txt}' has been generated.")
    