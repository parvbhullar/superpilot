import sys
import os

# Add the correct path to the 'superpilot' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from unstructured.partition.auto import partition


file_path='/Users/zestgeek-29/Desktop/Work/superpilot/superpilot/tests/test_file.pdf'

elements = partition(filename=file_path)
c=1
for element in elements:
    print(c,element.text)
    c=c+1
    print()


#print(elements)
