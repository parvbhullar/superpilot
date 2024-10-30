import json


class EnvConfigBuilder:
    def __init__(self):
        self.config = {}

    def build_environment(self,
                          name='simple_environment',
                          description='A simple environment',
                          creation_time=None,
                          request_id=None,
                          systems=None):
        self.config['environment'] = {
            'name': name,
            'description': description,
            'configuration': {
                'creation_time': creation_time,
                'request_id': request_id,
                'systems': systems
            }
        }

    def build_ability_registry(self,
                               name='super_ability_registry',
                               description='A super ability registry',
                               abilities=None, config=None):
        self.config['ability_registry'] = {
            'name': name,
            'description': description,
            'configuration': {
                'abilities': abilities,
                'config': config
            }
        }

    def build_memory(self,
                     name='simple_memory',
                     description='A simple memory'):
        self.config['memory'] = {
            'name': name,
            'description': description,
            'configuration': {}
        }

    def build_openai_provider(self,
                              name='openai_provider',
                              description="Provides access to OpenAI's API",
                              retries_per_request=10,
                              resource_type='model',
                              credentials=None,
                              budget=None):
        self.config['openai_provider'] = {
            'name': name,
            'description': description,
            'resource_type': resource_type,
            'credentials': credentials,
            'budget': budget,
            'configuration': {
                'retries_per_request': retries_per_request
            }
        }

    def build_planning(self,
                       name='planner',
                       description="Manages the pilot's planning and goal-setting",
                       models=None, prompt_strategies=None):
        self.config['planning'] = {
            'name': name,
            'description': description,
            'configuration': {
                'models': models,
                'prompt_strategies': prompt_strategies
            }
        }

    def build_workspace(self,
                        name='workspace',
                        description='The workspace is the root directory for all pilot activity',
                        root='',
                        parent='',
                        restrict_to_workspace=True):
        self.config['workspace'] = {
            'name': name,
            'description': description,
            'configuration': {
                'root': root,
                'parent': parent,
                'restrict_to_workspace': restrict_to_workspace
            }
        }

    def export_json(self):
        return json.dumps(self.config, indent=2)


# Usage example
if __name__ == "__main__":
    builder = EnvConfigBuilder()
    builder.build_environment(name='env_1', description='Environment 1', creation_time='20230826_154959', request_id='some_id', systems='some_systems')
    builder.build_ability_registry(name='ability_1', description='Ability Registry 1', abilities='some_abilities', config=None)
    builder.build_memory(name='memory_1', description='Memory 1')
    builder.build_openai_provider(name='provider_1', description='OpenAI Provider 1', retries_per_request=10, resource_type='model', credentials={'api_key': None}, budget={'total_budget': float('inf')})
    builder.build_planning(name='planner_1', description='Planner 1', models='some_models', prompt_strategies='some_strategies')
    builder.build_workspace(name='workspace_1', description='Workspace 1', root='', parent='some_parent', restrict_to_workspace=True)

    config_json = builder.export_json()
    print(config_json)
