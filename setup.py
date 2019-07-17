from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='devioc',
    version='2019.7.1',
    url="https://github.com/michel4j/devioc",
    license='MIT',
    author='Michel Fodje',
    author_email='michel4j@gmail.com',
    description='Simple Python based EPICS Device IOC Support',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='epics device ioc development',
    packages=['devioc'],
    scripts=['bin/devioc-startproject'],
    install_requires=['gepics', 'Twisted', 'numpy', 'PyGObject'],
    classifiers=[
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)