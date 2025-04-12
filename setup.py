from setuptools import setup, find_packages
import os

setup(
    name="jit",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'jit=jit.main:main',
        ],
    },
    author="Aryan Raskar",
    description="Jit - Another version control system to ruin everyones day",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/aryanraskar/jit.git",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
