""" setup.py of highlander """
import os
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    """ Reads the file content """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="highlander",
    version="0.3.0",
    author="Michael Trunner",
    author_email="michael@trunner.de",
    maintainer="Michael Trunner",
    maintainer_email="michael@trunner.de",
    description=("checks that the defind subprocess is only started once"),
    license="Apache Software License",
    # keywords = "example documentation tutorial",
    url="https://github.com/trunneml/highlander",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Natural Language :: German",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.7",
    ],
    include_package_data=True,
    install_requires=[
        "redis >= 2.9",
    ],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'highlander = highlander:main',
        ]
    }
)
