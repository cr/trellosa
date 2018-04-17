# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages

PACKAGE_NAME = 'trellosa'
PACKAGE_VERSION = '0.3.0a5'

INSTALL_REQUIRES = [
    'coloredlogs',
    'ipython',
    'jsondiff',
    'pygments',
    'requests'
]

TESTS_REQUIRE = [
    'coverage',
    'nose',
    'mock'
]

DEV_REQUIRES = [
    'coverage',
    'nose',
    'mock',
    'pycodestyle'
]

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description='TLS/SSL Test Suite for Mozilla Firefox',
    classifiers=[
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Operating System :: Microsoft :: Windows :: Windows 8',
        'Operating System :: Microsoft :: Windows :: Windows 8.1',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing'
    ],
    keywords=['mozilla', 'firefox', 'trello', 'product management', 'security', 'security assurance'],
    author='Christiane Ruetten',
    author_email='cr@mozilla.com',
    url='https://github.com/cr/trellosa',
    download_url='https://github.com/cr/trellosa/archive/latest.tar.gz',
    license='MPL2',
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,  # See MANIFEST.in
    zip_safe=True,
    use_2to3=True,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    extras_require={'dev': DEV_REQUIRES},  # For `pip install -e .[dev]`
    test_suite='nose.collector',
    entry_points={
        'console_scripts': [
            'trellosa = trellosa.main:main'
        ]
    }
)
