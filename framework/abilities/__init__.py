from superpilot.framework.abilities.search_summarise import SearchAndSummarizeAbility
from superpilot.framework.abilities.text_summarise import TextSummarizeAbility

ABILITIES = {
    SearchAndSummarizeAbility.name(): SearchAndSummarizeAbility,
    TextSummarizeAbility.name(): TextSummarizeAbility,
}
