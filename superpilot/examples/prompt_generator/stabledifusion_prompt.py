import json

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
    SchemaModel,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from pydantic import Field
from typing import List, Optional, Union, Dict


class StableDiffusionPromptModel(SchemaModel):
    """
    This class serves as a data model for Stable Diffusion Prompts used in AI art generation.
    It includes various fields that describe the properties and attributes of the art piece to be generated.
    Each field is self-explanatory and maps directly to a specific aspect of the art piece.
    """
    subject: str = Field(..., description="The main subject of the art piece.")
    action: str = Field(..., description="What the subject is doing.")
    context: str = Field(..., description="Background and surroundings.")
    environment: str = Field(..., description="General setting.")
    lighting: str = Field(..., description="Type of lighting in the scene.")
    artist: str = Field(..., description="Artist whose style is to be mimicked.")
    art_style: str = Field(..., alias="style", description="Artistic style.")
    medium: str = Field(..., description="Medium used for the art.")
    type: str = Field(..., description="Type of art e.g., illustration, painting.")
    color_scheme: str = Field(..., description="Color scheme to be followed.")
    computer_graphics: str = Field(..., description="Computer graphics tech used.")
    quality: str = Field(..., description="Resolution quality.")
    etc: List[str] = Field(..., description="Additional specifications.")
    positive_prompt: str = Field(..., description="Positive prompt.")
    negative_prompt: str = Field(..., description="Negative prompt.")


class StableDiffusionPrompt(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = (
        """
        As a prompt generator for a generative AI called "StableDiffusion", you will create image prompts for the AI to visualize. I will give you a concept, and you will provide a detailed prompt for StableDiffusion AI to generate an image.
        Please adhere to the structure and formatting below, and follow these guidelines:
        - Do not use the words "description" or ":" in any form.
        - Write each prompt in one line without using return.
        """
    )

    DEFAULT_USER_PROMPT_TEMPLATE = (
        """
        {task_objective}
        use above information to learn about Stable diffusion Prompting, and use it to create prompts.
        Stable Diffusion is an AI art generation model similar to DALLE-2. 
        It can be used to create impressive artwork by using positive and negative prompts. Positive prompts describe what should be included in the image. 
        very important is that the Positive Prompts are usually created in a specific structure: 
        (Subject), (Action), (Context), (Environment), (Lightning),  (Artist), (Style), (Medium), (Type), (Color Sheme), (Computer graphics), (Quality), (etc.)
        Subject: Person, animal, landscape
        Action: dancing, sitting, surveil
        Verb: What the subject is doing, such as standing, sitting, eating, dancing, surveil
        Adjectives: Beautiful, realistic, big, colourful
        Context: Alien planet's pond, lots of details
        Environment/Context: Outdoor, underwater, in the sky, at night
        Lighting: Soft, ambient, neon, foggy, Misty
        Emotions: Cosy, energetic, romantic, grim, loneliness, fear
        Artist: Pablo Picasso, Van Gogh, Da Vinci, Hokusai 
        Art medium: Oil on canvas, watercolour, sketch, photography
        style: Polaroid, long exposure, monochrome, GoPro, fisheye, bokeh, Photo, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT3
        Art style: Manga, fantasy, minimalism, abstract, graffiti
        Material: Fabric, wood, clay, Realistic, illustration, drawing, digital painting, photoshop, 3D
        Colour scheme: Pastel, vibrant, dynamic lighting, Green, orange, red
        Computer graphics: 3D, octane, cycles
        Illustrations: Isometric, pixar, scientific, comic
        Quality: High definition, 4K, 8K, 64K
        use this Negative Prompts and add some words what you think that match to Prompt: 2 heads, 2 faces, cropped image, out of frame, draft, deformed hands, signatures, twisted fingers, double image, long neck, malformed hands, nwltiple heads, extra limb, ugty, poorty drawn hands, missing limb, disfigured, cut-off, ugty, grain, Iow-res, Deforrned, blurry, bad anaWny, disfigured, poorty drawn face, mutation, mutated, floating limbs, disconnected limbs, long body, disgusting, poorty drawn, mutilated, mangled, surreal, extra fingers, duplicate artifacts, morbid, gross proportions, missing arms, mutated hands, mutilated hands, cloned face, malformed,ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, bad anatomy, watermark, signature, cut off, low contrast, underexposed, overexposed, bad art, beginner, amateur, distorted face, blurry, draft, grainy, etc 
        very important: use an artist matching to the art style , or dont write any artist if it is realistic style or some of that.
        Important Rules:
        - don't use any pronouns
        - avoid using these words: in a, the, with, of, the, an, and, is, by, of.
        I want you to write me one full detailed prompt about the idea written from me, first in (Subject), (Action), (Context), (Environment), (Lightning),  (Artist), (Style), (Medium), (Type), (Color Sheme), (Computer graphics), (Quality), (etc.). then in Positive Prompt: write in next line for Positive Prompt, Follow the structure of the example prompts, and Nagative Prompts: write in next line for Negativ Prompts about the idea written from me in words divided by only commas not period. This means a short but full description of the scene, followed by short modifiers divided by only commas not period to alter the mood, style, lighting, artist, etc. write all prompts in english.
        """
    )

    DEFAULT_PARSER_SCHEMA = StableDiffusionPromptModel.function_schema()

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
        super().__init__(
            model_classification=model_classification,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            parser_schema=parser_schema,
        )

    @classmethod
    def factory(cls, system_prompt=None, user_prompt_template=None, parser=None, model_classification=None)\
            -> "StableDiffusionPrompt":
        config = cls.default_configuration.dict()
        if model_classification:
            config['model_classification'] = model_classification
        if system_prompt:
            config['system_prompt'] = system_prompt
        if user_prompt_template:
            config['user_prompt_template'] = user_prompt_template
        if parser:
            config['parser_schema'] = parser
        return cls(**config)
