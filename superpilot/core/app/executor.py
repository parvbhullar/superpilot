import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
# from superpilot.core.app.thread_manager import ThreadManager
from superpilot.core.app.plugin_loader import PluginContainer
from superpilot.tests.test_env_simple import get_env
from superpilot.core.pilot import SuperPilot
from superpilot.core.configuration import get_config


def main(query, files: list = None, **kwargs):
    print(query)
    thread_id = kwargs.get("thread_id", None)
    pilot_handle = kwargs.get("pilot_handle", None)
    user = kwargs.get("user", None)
    data = kwargs.get("data", None)

    if files:
        for file in files:
            print(file)
            print(file.filename)
            print(file.filepath)
            print(file.filetype)

    # superpilot model definition - gpt3.5, gpt4
    app_plugins = PluginContainer.factory()
    env = get_env({})
    # context = Context()
    config = get_config()
    # superpilot = SuperPilot(app_plugins, environment=env, config)

    # list of pilots - loaded pilots(BrowseInternet, SearchDB, SearchJira, Dalle3)
    # it will try to pick right for the query based on the query type
    # if query type is not defined, it will pick the default pilot
    # Core Layer - store the data in the database + vector_store
    # vector_store - store the vector representation of the query


if __name__ == "__main__":
    q = "Hello World"
    main(q)