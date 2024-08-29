from graphviz import Digraph
import os

def generate_codebase_graph(codebase_path, output_file):
    dot = Digraph(comment='Codebase Structure', format='png')
    
    # Set graph size (width, height) and DPI
    dot.attr(size='90,90')  # Adjust width and height
    dot.attr(dpi='300')     # Set DPI for higher resolution
    
    # Traverse the codebase directory
    for root, dirs, files in os.walk(codebase_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                # Add file as a node
                dot.node(file_path, file)
                
                # Example: add edges (dummy example, adjust according to actual relationships)
                # This part needs real function and class relationships
                dot.node(f'{file_path}::example_function', 'example_function')
                dot.edge(file_path, f'{file_path}::example_function')
                dot.attr(size='90,90', dpi='300', rankdir='LR', nodesep='1', ranksep='1.5')
                dot.render(output_file, format='pdf')  # Render as PDF, which can be resized without losing quality


    
    # Render and save the graph
    dot.render(output_file, format='png')

if __name__ == "__main__":
    # Path to your codebase
    codebase_path = "/Users/zestgeek31/Desktop/super-pilot/superpilot/superpilot"
    
    # Output file for the graph
    output_file = "codebase_graph"
    
    # Generate and save the graph
    generate_codebase_graph(codebase_path, output_file)
    
    print(f"Graph structure of the codebase saved to {output_file}.png")
