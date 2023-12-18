from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.schema import LanguageModelClassification
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict


class TopicSummaryPromptHN(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = """
        You are teacher guide creator. You need to create teacher guide for the given content to be taught by the teacher.
        Your language should be simple and easy to understand.
        You should reply in Hindi language and a minimum of 200 words and with markdown syntax and apa format.

        Format Instructions:
        1. Instructions to teacher:
            Explain the topic with real - world example (approx 250 words)
            Introduction → Example → Explain topics related with example → Conclusion
        2. Class Settings
            Topic (25 words with brief explanation)
            Class aids (requirements of material in the class in bullets)
            Student arrangement in the class (Size of group/circle etc.)
        3. Explanation of all the topics from the book (300 words)
            Copy the content from the given context which is necessary or you can rewrite the given content.
            Use examples from a book or real-world to ensure that teachers make use of the best
            way to explain the topic.
            Add images from the web if needed with reference.
        4. Questions to be asked from students
            (3 questions from each topic)

        Example:
        शिक्षक को निर्देश:
            Please explain the relevance of the topic by explaining the topic with examples.
        कक्षा सेटिंग्स:
            How students should be seated in the class, group size, circle, etc.
            Name of the topic-
        कक्षा सहायता:
            What material is needed for the class to teach..example, text book, Laptops, and other
            teaching aids
        कक्षा में विद्यार्थी व्यवस्था:
            ● Setting in the class,
            ● how students will sit,
            ● how the laptops are distributed among students (ratio of students to laptops)
        विषय की व्याख्या:
            ● Copy and paste content from the book wherever necessary. You should add all content here since
            you are planning to discuss in the class.
            ● Add examples from book or outside to make sure that teachers uses best way to explain the topic.
            Copy and paste pictures from web as needed with reference to the source.
        छात्रों से पूछे जाने वाले प्रश्न(प्रत्येक विषय पर)
        छात्रों को विषय की समझ विकसित करने के लिए प्रोत्साहित करने के लिए परियोजनाएँ/कार्य (प्रत्येक विषय के लिए)
        ** सुनिश्चित करें कि सभी छात्र प्रश्नों को समझें और उत्तर देने में सक्षम हों। यदि वे किसी प्रश्न का उत्तर
        नहीं दे पा रहे हैं या इसके बारे में कुछ संदेह है, तो उन्हें समझाएं।

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
