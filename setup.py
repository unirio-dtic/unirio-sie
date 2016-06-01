# coding=utf-8
from setuptools import setup, find_packages
from os import path

VERSION = '0.0.2'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst')) as f:
    README = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='unirio-sie',
    version=VERSION,
    packages=find_packages(exclude=['*test*']),
    description='Python DAO module for SIE(Sistema de Informações para o Ensino) academic administration solution.',
    long_description=README,
    url='https://github.com/unirio-dtic/unirio-sie',
    author='Diogo Magalhães Martins',
    author_email='magalhaesmartins@icloud.com',
    license='GPLv2',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='unirio api sie development',
    install_requires=required
)

# todo: pre-publish -> pandoc --from=markdown --to=rst --output=README.rst README.md
