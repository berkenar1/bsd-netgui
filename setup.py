#!/usr/bin/env python3
"""Setup script for bsd-netgui package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='bsd-netgui',
    version='0.1.0',
    description='GUI Network Management Tool for FreeBSD and other BSD Systems',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='berkenar1',
    author_email='',
    url='https://github.com/berkenar1/bsd-netgui',
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'bsd-netgui=bsd_netgui.main:main',
            'bsd-netgui-daemon=bsd_netgui.daemon:main',
            'bsd-netgui-cli=bsd_netgui.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Environment :: X11 Applications',
        'Environment :: MacOS X',
    ],
    keywords='bsd freebsd network manager gui networking',
    project_urls={
        'Source': 'https://github.com/berkenar1/bsd-netgui',
        'Bug Reports': 'https://github.com/berkenar1/bsd-netgui/issues',
    },
)
