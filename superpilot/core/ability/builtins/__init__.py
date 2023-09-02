from superpilot.core.ability.builtins.create_new_ability import CreateNewAbility
from superpilot.core.ability.builtins.query_language_model import QueryLanguageModel

BUILTIN_ABILITIES = {
    QueryLanguageModel.name(): QueryLanguageModel,
}

RESEARCH_ABILITIES = {
    QueryLanguageModel.name(): QueryLanguageModel,
}
