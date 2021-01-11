from setuptools import find_packages, setup
from devioc.version import get_version

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='devioc',
    version=get_version(),
    url="https://github.com/michel4j/devioc",
    license='MIT',
    author='Michel Fodje',
    author_email='michel4j@gmail.com',
    description='Simple Python based EPICS Device IOC Support',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='epics device ioc development',
    packages=find_packages(),
    scripts=[
        'bin/devioc-startproject'
    ],
    install_requires=requirements + [
        'importlib-metadata ~= 1.0 ; python_version < "3.8"',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)