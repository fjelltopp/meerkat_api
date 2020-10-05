#!/usr/bin/env python3
import uuid
from setuptools import setup, find_packages

setup(
    name='Meerkat API Background tasks',
    version='0.0.1',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    # you need to manually install meerkat_api/requirements.txt
    install_requires=[],
    test_suite='api_background.test'
)
