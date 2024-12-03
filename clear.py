# Read the original requirements.txt file
with open('new_requirements.txt', 'r') as file:
    lines = file.readlines()

# Process each line to remove the version numbers and "=="
libraries = [line.split('==')[0] for line in lines]

# Write the library names to the new_requirements.txt file
with open('requirements.txt', 'w') as file:
    for library in libraries:
        file.write(library + '\n')


print("Hello World")
