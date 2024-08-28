import ast
import os
import ollama 
def extract_functions_from_code(code):
    """Parse the given code and return a list of function names."""
    try:
        tree = ast.parse(code)
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    except SyntaxError as e:
        print(f"Error parsing code: {e}")
        return []

def generate_test_case_file(functions, output_file):
    """Generate a test case file for the given functions."""
    with open(output_file, 'w') as test_file:
        test_file.write("import unittest\n\n")
        
        test_class_name = "Test" + os.path.splitext(os.path.basename(output_file))[0].capitalize()
        test_file.write(f"class {test_class_name}(unittest.TestCase):\n\n")

        for func in functions:
            test_file.write(f"    def test_{func}(self):\n")
            test_file.write(f"        # TODO: Write test case for {func}\n")
            test_file.write(f"        pass\n\n")

        test_file.write("\nif __name__ == '__main__':\n")
        test_file.write("    unittest.main()\n")

    print(f"Test case file '{output_file}' created successfully.")

def main():
   
    code_file = input("Enter the path to the Python code file: ").strip()
    
    if not os.path.exists(code_file):
        print("File does not exist.")
        return

    # Read the code from the file
    with open(code_file, 'r') as file:
        code = file.read()

    # Extract function names
    functions = extract_functions_from_code(code)
    
    if not functions:
        print("No functions found in the code.")
        return
    
    # Generate the test case file name
    output_file = os.path.splitext(code_file)[0] + "_test.py"
    
    # Generate the test case file
    generate_test_case_file(functions, output_file)

if __name__ == "__main__":
    main()
