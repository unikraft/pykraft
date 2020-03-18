from setuptools import setup, find_packages
import glob
import os

with open('requirements.txt') as f:
    required = [x for x in f.read().splitlines() if not x.startswith("#")]

from kraft import __version__, __description__

setup(
    name = 'unikraft-tools',
    version = __version__,
    packages = find_packages(exclude=['tests.*', 'tests']),
    description = __description__,
    license = '',
    url = 'https://github.com/unikraft/kraft.git',
    author = 'Alexander Jung',
    author_email = 'a.jung@lancs.ac.uk',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.5, <4',
    entry_points = """
        [console_scripts]
        kraft = kraft.kraft:kraft
        """,
    scripts = [
        'scripts/qemu-guest',
        'scripts/xen-guest',
        'scripts/kraft-net'
    ],
    keywords = [],
    tests_require = ['pytest', 'coveralls'],
    zip_safe = False,
    install_requires = required,
    include_package_data=True
)
