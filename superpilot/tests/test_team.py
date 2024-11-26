import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from superpilot.examples.channels.teams.main import main

if __name__ == "__main__":
    # Call the main function to start the process
    main()