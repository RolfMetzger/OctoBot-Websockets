#  Drakkar-Software OctoBot
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import os
from setuptools import find_packages, setup
# from Cython.Build import cythonize

from octobot_websockets import PROJECT_NAME, VERSION


def find_package_data(path):
    return (path, [os.path.join(dirpath, filename)
                   for dirpath, dirnames, filenames in os.walk(path)
                   for filename in
                   [file for file in filenames if not file.endswith(".py") and not file.endswith(".pyc")]])


PACKAGES = find_packages()

# long description from README file
with open('README.md', encoding='utf-8') as f:
    DESCRIPTION = f.read()

REQUIRED = open('requirements.txt').read()
REQUIRES_PYTHON = '>=3.7'

setup(
    name=PROJECT_NAME,
    version=VERSION,
    url='https://github.com/Drakkar-Software/OctoBot-Websockets',
    license='LGPL-3.0',
    author='Drakkar-Software',
    author_email='drakkar.software@protonmail.com',
    description='OctoBot project exchange websockets',
    packages=PACKAGES,
    long_description=DESCRIPTION,
    install_requires=REQUIRED,
    tests_require=["pytest"],
    test_suite="tests",
    zip_safe=False,
    data_files=[],
    python_requires=REQUIRES_PYTHON,
    # ext_modules=cythonize(["**/*.pyx"]),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
    ],
)
