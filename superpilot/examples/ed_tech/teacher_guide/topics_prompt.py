from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict

from superpilot.examples.ed_tech.question_solver import QuestionSolverPrompt


class TopicsPrompt(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = """
        You are teacher guide creator. You need to create teacher guide for the given content to be taught by the teacher.
        Your language should be simple and easy to understand.
        Content language is Hindi.
        
        Format Instructions:
        1. Topics to be covered in given chapter(table format)
        2. What we will learn from the topic or chapter (bullets or table format)
        3. Learning outcomes after completing the chapter (bullets or table format)
        4. Instructions to teacher:
            Explain the topic with real - world example (approx 250 words)
            Introduction → Example → Explain topics related with example → Conclusion
        5. Class Settings
            Topic (25 words with brief explanation)
            Class aids (requirements of material in the class in bullets)
            Student arrangement in the class (Size of group/circle etc.)
        6. Explanation of all the topics from the book (300 words)
            Copy the content from the given context which is necessary or you can rewrite the given content.
            Use examples from a book or real-world to ensure that teachers make use of the best
            way to explain the topic.
            Add images from the web if needed with reference.
        7. Questions to be asked from students
            (3 questions from each topic)

        Example:
        We will cover the following topics in this chapter:
        Table of topics
        
        What we will learn from the chapter:
        Table of learning
        
        Learning outcomes after completing the chapter:
        At the end of the chapter, students should be able to learn about following topics
        
        Instructions to teacher:
            Introduction:
            Begin the session by engaging the students in a relatable scenario.
            "Imagine you're in a village, surrounded by the simplicity of life. Now, let's explore how the
            world of networking and cybersecurity can make this village life even more secure,
            connected, and fascinating."
                Networking in Village Life:
                    ● Communication and Connectivity:
                        ○  Explain how networking connects people and devices. In the village context, it
                        helps in communicating with neighboring villages, sharing information, and
                        collaborating for community activities.
                    ● Resource Sharing:
                        ○ Describe how a network can be like a virtual marketplace for villagers,
                        facilitating the exchange of resources, agricultural tools, and knowledge.
                Cybersecurity in Village Life:
                    ● Securing Information:
                        ○ Emphasize the importance of keeping personal and community information
                        safe from potential threats. Discuss how cybersecurity measures protect
                        against unauthorized access.
        Class Settings:
            Begin the class by discussing how networking connects computers and enhances
            communication. Highlight the importance of cybersecurity in keeping information
            safe online.
            Class aids
                Student handbook
                Computer
            Student arrangement in the class
                Students sit in class on benches and chairs. Give opportunities to all students to be part of
                the discussion related to the topics.
            Explanation of the Topics:
            
        Questions to ask from Students (on each topic)
            Projects/tasks to encourage students to develop an understanding of the topic (for
            each topic)
            Networking and Its Types:
                1. What is networking, and why is it important for devices to communicate?
                2. Can you explain the difference between a local area network (LAN) and a wide area
                    network (WAN)?
            Cloud Computing:
                1. What is cloud computing, and how does it differ from using only your computer?
                2. How might cloud computing be helpful for students in a village school?

        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Chapter:
        {context}
    
        task:{task_objective}
        """

    DEFAULT_PARSER_SCHEMA = None  # Question.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification = default_configuration.model_classification,
        system_prompt: str = default_configuration.system_prompt,
        user_prompt_template: str = default_configuration.user_prompt_template,
        parser_schema: Dict = None,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser_schema = parser_schema

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def parse_response_content(
        self,
        response_content: dict,
    ) -> dict:
        """Parse the actual text response from the objective model.

        Args:
            response_content: The raw response content from the objective model.

        Returns:
            The parsed response.

        """
        if "function_call" in response_content:
            parsed_response = json_loads(response_content["function_call"]["arguments"])
        else:
            parsed_response = response_content
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

    def get_config(self) -> PromptStrategyConfiguration:
        return PromptStrategyConfiguration(
            model_classification=self._model_classification,
            system_prompt=self._system_prompt_message,
            user_prompt_template=self._user_prompt_template,
            parser_schema=self._parser_schema,
            location=PluginLocation(
                storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                storage_route=f"{__name__}.{self.__class__.__name__}",
            ),
        )

