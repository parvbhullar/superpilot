import os
import ast
import networkx as nx
import matplotlib.pyplot as plt

def extract_code_info(directory):
    graph = nx.DiGraph()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    try:
                        tree = ast.parse(f.read(), filename=file)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                graph.add_node(node.name, type='function', file=file_path)
                                if node.args.args:
                                    for arg in node.args.args:
                                        graph.add_node(arg.arg, type='argument', file=file_path)
                                        graph.add_edge(node.name, arg.arg)
                            elif isinstance(node, ast.ClassDef):
                                graph.add_node(node.name, type='class', file=file_path)
                                for item in node.body:
                                    if isinstance(item, ast.FunctionDef):
                                        graph.add_node(item.name, type='method', file=file_path)
                                        graph.add_edge(node.name, item.name)
                    except SyntaxError:
                        print(f"Syntax error in file: {file_path}")
    return graph

def visualize_graph(graph):
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=10, font_weight='bold')
    plt.show()

def main():
    directory = input("Enter the directory path to extract source code: ")
    graph = extract_code_info(directory)
    visualize_graph(graph)

if __name__ == "__main__":
    main()
