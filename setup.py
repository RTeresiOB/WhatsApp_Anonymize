#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script

@author: RobertTeresi
"""
import setuptools
import sys
from subprocess import call

setuptools.setup(
    name="WhatsApp_Anonymize", # Replace with your own username
    version="0.0.1",
    author="Robert K Teresi",
    author_email="robert.teresi@yale.edu",
    description="Package to anonymize whatsapp messages.",
    #long_description= long_description,
    #long_description_content_type="text/markdown",
    #url="https://github.com/RTeresiOB/WhatsApp_Anonymize",
    packages=setuptools.find_packages(),
    install_requires=[
                     'pandas',
                     'pathlib',
                     'datetime',
                     'spacy',
                     'names',
                     'cryptography'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.0',
)

# Now install spacy model
call([sys.executable,'-m','spacy','download','en_core_web_sm'])
