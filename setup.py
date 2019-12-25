import os
from setuptools import setup, find_packages

PACKAGE_NAME = 'pydevccu'
HERE = os.path.abspath(os.path.dirname(__file__))
VERSION = '0.0.3'

PACKAGES = find_packages(exclude=['tests', 'tests.*', 'dist', 'build'])

REQUIRES = []

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    license='MIT License',
    url='https://github.com/danielperna84/pydevccu',
    download_url='https://github.com/danielperna84/pydevccu/tarball/'+VERSION,
    author='Daniel Perna',
    author_email='danielperna84@gmail.com',
    description='Virtual HomeMatic CCU XML-RPC backend',
    packages=PACKAGES,
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=REQUIRES,
    keywords=['homematic', 'ccu', 'xml-rpc'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Topic :: Home Automation'
    ],
)
