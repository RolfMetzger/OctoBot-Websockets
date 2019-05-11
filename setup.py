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
# from distutils.extension import Extension
from Cython.Distutils import build_ext
from setuptools import find_packages
from setuptools import setup, Extension

from octobot_websockets.constants import PROJECT_NAME, VERSION

ext_modules = [
    Extension("octobot_websockets.bitmex", ["octobot_websockets/bitmex.pyx"]),
    Extension("octobot_websockets.book", ["octobot_websockets/book.pyx"]),
    Extension("octobot_websockets.callback", ["octobot_websockets/callback.pyx"]),
    Extension("octobot_websockets.candle", ["octobot_websockets/candle.pyx"]),
    Extension("octobot_websockets.candle_constructor", ["octobot_websockets/candle_constructor.pyx"]),
    Extension("octobot_websockets.feed", ["octobot_websockets/feed.pyx"]),
    Extension("octobot_websockets.ticker", ["octobot_websockets/ticker.pyx"]),
    Extension("octobot_websockets.ticker_constructor", ["octobot_websockets/ticker_constructor.pyx"]),
]

PACKAGES = find_packages(exclude=["tests"])

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
    cmdclass={'build_ext': build_ext},
    tests_require=["pytest"],
    test_suite="tests",
    zip_safe=False,
    data_files=[],
    setup_requires=['Cython'],
    python_requires=REQUIRES_PYTHON,
    ext_modules=ext_modules,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
    ],
)
