#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script

@author: RobertTeresi
"""
import setuptools

setuptools.setup(
    name="RTeresiOB", # Replace with your own username
    version="0.0.1",
    author="Robert K Teresi",
    author_email="robert.teresi@yale.edu",
    description="Package to anonymize whatsapp messages.",
    #long_description= long_description,
    #long_description_content_type="text/markdown",
    #url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.0',
)