from codecs import open
from os import path

from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line]

setup(
    name="superpilot",
    version="0.4.2",
    description="The Multi-Role Superpilot Programming Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/parvbhullar/superpilot",
    author="ParvBhullar",
    author_email="parvinder@recalll.co",
    license="MIT",
    keywords="superpilot multi-role multi-agent programming gpt llm",
    packages=find_packages(exclude=["contrib", "docs"]),
    python_requires=">=3.10",
    install_requires=[
        *requirements,
        "setfit @ git+https://github.com/huggingface/setfit.git",
    ],
)
