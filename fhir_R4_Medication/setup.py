import os
from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='openimis-be-fhir_r4_medication',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    license='GNU AGPL v3',
    description='The openIMIS Backend FHIR R4 Medication module.',
    long_description='The openIMIS Backend FHIR R4 Medication module.',
    long_description_content_type='text/markdown',
    url='https://openimis.org/',
    author='openIMIS',
    author_email='info@openimis.org',
    install_requires=[
        'django',
        'djangorestframework',
        'openimis-be-core',
        'openimis-be-api_fhir_r4',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
