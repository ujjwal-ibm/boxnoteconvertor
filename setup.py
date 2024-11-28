from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="boxtodocx",
    version="1.0.0",
    author="Ujjwal Kumar",
    author_email="ujjwal.kumar1@ibm.com",
    description="Convert Box Notes to Microsoft Word (docx) documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ujjwal-ibm/boxtodocx",
    project_urls={
        "Bug Tracker": "https://github.com/ujjwal-ibm/boxtodocx/issues",
        "Documentation": "https://github.com/ujjwal-ibm/boxtodocx",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Text Processing",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "boxtodocx=boxtodocx.cli:main",
        ],
    },
    include_package_data=True,
)