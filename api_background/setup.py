#!/usr/bin/env python3
import uuid
import os
from setuptools import setup, find_packages
import pathlib
import pkg_resources
pwd = pathlib.Path(__file__).parent.absolute()
with pathlib.Path(os.path.join(pwd, '../requirements.txt')).open() as requirements_txt:
    reqs = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(
    name='Meerkat API Background tasks',
    version='0.0.1',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=reqs,
    test_suite='api_background.test'
)
