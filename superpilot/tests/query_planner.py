import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from dotenv import load_dotenv
load_dotenv()

import openai
import enum
import asyncio

from pydantic import Field
from typing import List
from superpilot.core.configuration import get_config
from superpilot.core.context.schema import Context

from superpilot.core.resource.model_providers import SchemaModel


class QueryType(str, enum.Enum):
    """
    Enumeration representing the types of queries that can be asked to a question answer system.
    """

    # When i call it anything beyond 'merge multiple responses' the accuracy drops significantly.
    SINGLE_QUESTION = "SINGLE"
    MERGE_MULTIPLE_RESPONSES = "MERGE_MULTIPLE_RESPONSES"


class QueryCategory(str, enum.Enum):
    """
    Enumeration representing the types of queries that can be asked to a question answer system.
    """
    # When i call it anything beyond 'merge multiple responses' the accuracy drops significantly.
    CREATIVE_WRITING = "CREATIVE_WRITING"  # Write a question or instruction that requires a creative, open-ended written response. The instruction should be reasonable to ask of a person with general world knowledge and should not require searching. In this task, your prompt should give very specific instructions to follow. Constraints, instructions, guidelines, or requirements all work, and the more of them the better.
    CLOSED_QA = "CLOSED_QA"  # Write a question or instruction that requires factually correct response based on a passage of text from Wikipedia. The question can be complex and can involve human-level reasoning capabilities, but should not require special knowledge. To create a question for this task include both the text of the question as well as the reference text in the form.
    OPEN_QA = "OPEN_QA"  # Write a question that can be answered using general world knowledge or at most a single search. This task asks for opinions and facts about the world at large and does not provide any reference text for consultation.
    INFORMATION_EXTRACTION = "INFORMATION_EXTRACTION"  # These questions involve reading a paragraph from Wikipedia and extracting information from the passage. Everything required to produce an answer (e.g. a list, keywords etc) should be included in the passages. To create a question for this task include both the text of the question as well as the reference text in the form.
    PARAPHRASE = "PARAPHRASE"  # Write a paraphrase of the following text. A paraphrase is a restatement of the meaning of a text or passage using other words. To create a paraphrase for this task include both the text of the paraphrase as well as the reference text in the form.
    BRAINSTORMING = "BRAINSTORMING"  # Think up lots of examples in response to a question asking to brainstorm ideas.
    SUMMARIZATION = "SUMMARIZATION"  # Give a summary of a paragraph from Wikipedia. Please don't ask questions that will require more than 3-5 minutes to answer. To create a question for this task include both the text of the question as well as the reference text in the form.
    CLASSIFICATION = "CLASSIFICATION"  # Write a sentence that classifies the following text into the following categories. To create a sentence for this task include both the text of the sentence as well as the reference text in the form.
    TASK_EXECUTION = "TASK_EXECUTION"  # Write a sentence that describes how to complete the following task. To create a sentence for this task include both the text of the sentence as well as the reference text in the form.
    TEXT_TRANSLATION = "SENTENCE_TRANSLATION"  # Translate the following sentence into French. To create a sentence for this task include both the text of the sentence as well as the reference text in the form.


class QueryDomain(str, enum.Enum):
    """
    Enumeration representing the domains for different types of queries in a question answer system.
    """
    TRAVEL = "TRAVEL"  # Queries related to travel, such as destinations, accommodations, transportation, etc.
    SHOPPING = "SHOPPING"  # Queries related to shopping, such as products, brands, online or offline shopping, etc.
    CODING = "CODING"  # Queries related to coding, programming languages, software development, etc.
    COOKING = "COOKING"  # Queries related to cooking, recipes, ingredients, cooking techniques, etc.
    FITNESS = "FITNESS"  # Queries related to fitness, exercise routines, workout plans, nutrition, etc.
    TECHNOLOGY = "TECHNOLOGY"  # Queries related to technology, gadgets, devices, software, etc.
    AI = "AI"  # Queries related to artificial intelligence, machine learning, deep learning, neural networks, etc.
    PROMPT_ENGINEERING = "PROMPT_ENGINEERING"  # Queries related to prompt writing, prompt engineering, prompt design, prompt tuning, etc.
    SCIENCE = "SCIENCE"  # Queries related to science, scientific concepts, discoveries, research, etc.
    HISTORY = "HISTORY"  # Queries related to history, historical events, periods, civilizations, etc.
    ART = "ART"  # Queries related to art, artistic techniques, artists, art history, etc.
    MUSIC = "MUSIC"  # Queries related to music, genres, artists, albums, musical instruments, etc.
    MOVIES = "MOVIES"  # Queries related to movies, films, actors, directors, genres, etc.
    BOOKS = "BOOKS"  # Queries related to books, literature, authors, genres, book recommendations, etc.
    SPORTS = "SPORTS"  # Queries related to sports, athletes, teams, rules, sports events, etc.
    HEALTH = "HEALTH"  # Queries related to health, medical conditions, treatments, wellness, etc.
    FINANCE = "FINANCE"  # Queries related to finance, investments, personal finance, banking, etc.
    EDUCATION = "EDUCATION"  # Queries related to education, schools, learning methods, educational resources, etc.
    BUSINESS = "BUSINESS"  # Queries related to business, entrepreneurship, startups, management, etc.
    POLITICS = "POLITICS"  # Queries related to politics, political systems, government policies, elections, etc.
    ENVIRONMENT = "ENVIRONMENT"  # Queries related to the environment, sustainability, climate change, conservation, etc.
    PHILOSOPHY = "PHILOSOPHY"  # Queries related to philosophy, philosophical concepts, thinkers, ethics, etc.
    RELIGION = "RELIGION"  # Queries related to religion, religious beliefs, practices, spirituality, etc.
    PSYCHOLOGY = "PSYCHOLOGY"  # Queries related to psychology, human behavior, mental processes, therapy, etc.
    PARENTING = "PARENTING"  # Queries related to parenting, child-rearing, parenting techniques, family dynamics, etc.
    RELATIONSHIPS = "RELATIONSHIPS"  # Queries related to relationships, dating, love, marriage, friendships, etc.
    FASHION = "FASHION"  # Queries related to fashion, clothing styles, fashion trends, fashion designers, etc.
    BEAUTY = "BEAUTY"  # Queries related to beauty, skincare, makeup, beauty products, grooming, etc.
    GAMING = "GAMING"  # Queries related to gaming, video games, game reviews, gaming consoles, esports, etc.
    PHOTOGRAPHY = "PHOTOGRAPHY"  # Queries related to photography, camera equipment, techniques, photo editing, etc.
    CARS = "CARS"  # Queries related to cars, automobiles, car brands, car models, car maintenance, etc.
    BIKES = "BIKES"  # Queries related to bikes, bicycles, bike brands, bike models, bike maintenance, etc.
    TOYS = "TOYS"  # Queries related to toys, toy brands, toy models, toy reviews, etc.
    PETS = "PETS"  # Queries related to pets, pet care, pet breeds, pet training, pet health, etc.
    GARDENING = "GARDENING"  # Queries related to gardening, plants, gardening techniques, garden design, etc.
    FOOD = "FOOD"  # Queries related to food, recipes, cooking tips, culinary traditions, food culture, etc.
    ENTERTAINMENT = "ENTERTAINMENT"  # Queries related to entertainment, celebrities, gossip, events, etc.
    NEWS = "NEWS"  # Queries related to news, current events, world affairs, etc.
    SOCIAL_MEDIA = "SOCIAL_MEDIA"  # Queries related to social media platforms, social media marketing, influencers, etc.
    CULTURE = "CULTURE"  # Queries related to culture, cultural practices, traditions, cultural heritage, etc.
    LANGUAGES = "LANGUAGES"  # Queries related to languages, language learning, translation, linguistic concepts, etc.
    DIY = "DIY"  # Queries related to do-it-yourself (DIY) projects, crafts, home improvement, etc.
    HOME_DECOR = "HOME_DECOR"  # Queries related to home decor, interior design, home styling, etc.
    CAREER = "CAREER"  # Queries related to career development, job search, professional growth, workplace advice, etc.
    DESIGN = "DESIGN"  # Queries related to design, graphic design, web design, product design, etc.
    SUSTAINABILITY = "SUSTAINABILITY"  # Queries related to sustainability, eco-friendly practices, renewable energy, etc.
    YOGA = "YOGA"  # Queries related to yoga, yoga poses, yoga styles, yoga benefits, etc.
    MEDITATION = "MEDITATION"  # Queries related to meditation, meditation techniques, mindfulness, etc.
    ENTREPRENEURSHIP = "ENTREPRENEURSHIP"  # Queries related to entrepreneurship, starting a business, business ideas, etc.
    STARTUPS = "STARTUPS"  # Queries related to startups, startup culture, funding, incubators, etc.
    MARKETING = "MARKETING"  # Queries related to marketing, marketing strategies, digital marketing, advertising, etc.
    ADVERTISING = "ADVERTISING"  # Queries related to advertising, advertising campaigns, ad design, advertising platforms, etc.
    SPORTS_COACHING = "SPORTS_COACHING"  # Queries related to sports coaching, coaching techniques, team management, etc.
    PERSONAL_DEVELOPMENT = "PERSONAL_DEVELOPMENT"  # Queries related to personal development, self-improvement, goal setting, etc.
    MENTAL_HEALTH = "MENTAL_HEALTH"  # Queries related to mental health, emotional well-being, stress management, etc.
    SELF_IMPROVEMENT = "SELF_IMPROVEMENT"  # Queries related to self-improvement, personal growth, motivation, etc.
    TECHNOLOGY_PROGRAMMING = "TECHNOLOGY_PROGRAMMING"  # Queries related to technology and programming, coding languages, software development, etc.
    GENERAL = "GENERAL"  # Queries that are not specific to any domain.


class ComputeQuery(SchemaModel):
    """
    Models a computation of a query, assume this can be some RAG system like llamaindex
    """

    query: str
    response: str = "..."


class MergedResponses(SchemaModel):
    """
    Models a merged response of multiple queries.
    Currently we just concatinate them but we can do much more complex things.
    """

    responses: List[ComputeQuery]


class Query(SchemaModel):
    """
    Class representing a single question in a question answer subquery.
    Can be either a single question or a multi question merge.
    """

    id: int = Field(..., description="Unique id of the query")
    question: str = Field(
        ...,
        description="Question we are asking using a question answer system, if we are asking multiple questions, this question is asked by also providing the answers to the sub questions",
    )
    dependancies: List[int] = Field(
        default_factory=list,
        description="List of sub questions that need to be answered before we can ask the question. Use a subquery when anything may be unknown, and we need to ask multiple questions to get the answer. Dependences must only be other queries.",
    )
    node_type: QueryType = Field(
        default=QueryType.SINGLE_QUESTION,
        description="Type of question we are asking, either a single question or a multi question merge when there are multiple questions",
    )
    category: QueryCategory = Field(
        default=QueryCategory.OPEN_QA,
        description="Type of category user asked this will helps us to choose the best prompt and workflow for the query",
    )
    domain: QueryDomain = Field(
        default=QueryDomain.GENERAL,
        description="Domain of query we are asking, it can be anything like shopping, travel, food, coding, question answering, science, history, medical, health etc.",
    )
    # clarifying_questions: List[str] = Field(
    #     default_factory=list,
    #     description="List of clarifying questions that can be asked to the user to get more information about the query and create a better prompt",
    # )

    async def execute(self, dependency_func):
        print("Executing", f"`self.question`")
        print("Executing with", len(self.dependancies), "dependancies")

        if self.node_type == QueryType.SINGLE_QUESTION:
            resp = ComputeQuery(
                query=self.question,
            )
            await asyncio.sleep(1)
            pprint(resp.dict())
            return resp

        sub_queries = dependency_func(self.dependancies)
        computed_queries = await asyncio.gather(
            *[q.execute(dependency_func=dependency_func) for q in sub_queries]
        )
        sub_answers = MergedResponses(responses=computed_queries)
        merged_query = f"{self.question}\nContext: {sub_answers.json()}"
        resp = ComputeQuery(
            query=merged_query,
        )
        await asyncio.sleep(2)
        pprint(resp.dict())
        return resp


class QueryPlan(SchemaModel):
    """
    Container class representing a tree of questions to ask a question answer system.
    and its dependencies. Make sure every question is in the tree, and every question is asked only once.
    """

    query_graph: List[Query] = Field(
        ..., description="The original question we are asking"
    )

    def __init__(self, query_graph: List[Query] = []):
        if not isinstance(query_graph, List):
            query_graph = [query_graph]
        print("Creating query plan with", query_graph, "queries")
        super().__init__(query_graph=query_graph)

    async def execute(self):
        # this should be done with a topological sort, but this is easier to understand
        original_question = self.query_graph[-1]
        print(f"Executing query plan from `{original_question.question}`")
        return await original_question.execute(dependency_func=self.dependencies)

    def dependencies(self, idz: List[int]) -> List[Query]:
        """
        Returns the dependencies of the query with the given id.
        """
        return [q for q in self.query_graph if q.id in idz]


Query.update_forward_refs()
QueryPlan.update_forward_refs()


def query_planner(question: str, ai_persona=None, plan=False) -> QueryPlan:
    context = Context()
    PLANNING_MODEL = "gpt-4"
    ANSWERING_MODEL = "gpt-3.5-turbo-0613"
    full_prompt = question
    # for i, goal in enumerate(ai_persona.ai_plan):
    #     full_prompt += f" and {goal}"
    # print(full_prompt)
    from superpilot.tests.default_prompts import DEFAULT_SYSTEM_PROMPT_QUERY_PLANNER, DEFAULT_TASK_PROMPT_QUERY_PLANNER
    from jinja2 import Template
    prompt_user_template = Template(
        DEFAULT_TASK_PROMPT_QUERY_PLANNER
    ).render(user_prompt=full_prompt)
    messages = [
        {
            "role": "system",
            "content": DEFAULT_SYSTEM_PROMPT_QUERY_PLANNER,
        },
        {
            "role": "user",
            "content": prompt_user_template,
        },
    ]

    if plan:
        messages.append(
            {
                "role": "assistant",
                "content": "Lets think step by step to find correct set of queries and its dependencies and not make any assuptions on what is known.",
            },
        )
        completion = openai.ChatCompletion.create(
            model=PLANNING_MODEL,
            temperature=0,
            messages=messages,
            max_tokens=1000,
        )

        messages.append(completion.choices[0].message)

        messages.append(
            {
                "role": "user",
                "content": "Using that information produce the complete and correct query plan.",
            }
        )

    completion = openai.ChatCompletion.create(
        model=ANSWERING_MODEL,
        temperature=0,
        functions=[QueryPlan.function_schema()],
        function_call={"name": QueryPlan.function_schema()["name"]},
        messages=messages,
        max_tokens=1000,
    )
    root = QueryPlan.from_response(completion)
    return root


if __name__ == "__main__":
    from pprint import pprint

    plan = query_planner(
        # "What is the difference in populations of Canada and the Jason's home country?",
        "multiply 2 and 3 and then sum with 6 and then subtract 2 and then divide by 2",
        plan=False,
    )
    pprint(plan.dict())
    """
    {'query_graph': [{'dependancies': [],
                    'id': 1,
                    'node_type': <QueryType.SINGLE_QUESTION: 'SINGLE'>,
                    'question': "Identify Jason's home country"},
                    {'dependancies': [],
                    'id': 2,
                    'node_type': <QueryType.SINGLE_QUESTION: 'SINGLE'>,
                    'question': 'Find the population of Canada'},
                    {'dependancies': [1],
                    'id': 3,
                    'node_type': <QueryType.SINGLE_QUESTION: 'SINGLE'>,
                    'question': "Find the population of Jason's home country"},
                    {'dependancies': [2, 3],
                    'id': 4,
                    'node_type': <QueryType.SINGLE_QUESTION: 'SINGLE'>,
                    'question': 'Calculate the difference in populations between '
                                "Canada and Jason's home country"}]}    
    """

    asyncio.run(plan.execute())
    """
    Executing query plan from `What is the difference in populations of Canada and Jason's home country?`
    Executing `What is the difference in populations of Canada and Jason's home country?`
    Executing with 2 dependancies
    Executing `What is the population of Canada?`
    Executing `What is the population of Jason's home country?`
    {'query': 'What is the population of Canada?', 'response': '...'}
    {'query': "What is the population of Jason's home country?", 'response': '...'}
    {'query': "What is the difference in populations of Canada and Jason's home "
            'country?'
            'Context: {"responses": [{"query": "What is the population of '
            'Canada?", "response": "..."}, {"query": "What is the population of '
            'Jason's home country?", "response": "..."}]}',
    'response': '...'}
    """
