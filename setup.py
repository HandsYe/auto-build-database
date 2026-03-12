#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生信数据库自动化部署系统"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="biodeploy",
    version="1.0.0",
    author="BioDeploy Team",
    author_email="biodeploy@example.com",
    description="生信数据库自动化部署系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/biodeploy/biodeploy",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "biodeploy=biodeploy.cli.main:cli",
        ],
    },
)
