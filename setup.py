"""Package configuration for boxtodocx."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="boxtodocx",
    version="2.0.0",
    author="Ujjwal Kumar",
    author_email="ujjwal.kumar1@ibm.com",
    description="Convert Box documents to HTML and DOCX formats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ujjwal-ibm/boxtodocx",
    project_urls={
        "Bug Tracker": "https://github.com/ujjwal-ibm/boxtodocx/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "beautifulsoup4>=4.9.3",
        "python-docx>=0.8.11",
        "requests>=2.25.1",
        "click>=8.0.0",
        "typing-extensions>=4.0.0",
        "colorlog>=6.7.0",
        "Pillow>=10.0.0",
        "yattag>=1.16.0",
        "selenium>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "boxtodocx=boxtodocx.cli:main",
        ],
    },
)