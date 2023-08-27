from superpilot.core.ability.builtins.create_new_ability import CreateNewAbility
from superpilot.core.ability.builtins.query_language_model import QueryLanguageModel
from superpilot.core.ability.builtins.google_search import GoogleSearch

BUILTIN_ABILITIES = {
    QueryLanguageModel.name(): QueryLanguageModel,
}

RESEARCH_ABILITIES = {
    GoogleSearch.name(): GoogleSearch,
    QueryLanguageModel.name(): QueryLanguageModel,
}
