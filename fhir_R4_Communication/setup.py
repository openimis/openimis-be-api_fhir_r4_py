from setuptools import setup, find_packages

setup(
    name="openimis-be-fhir-r4-communication",
    version="1.0.0",
    author="OpenIMIS Initiative",
    author_email="admin@openimis.org",
    description="OpenIMIS FHIR R4 Communication module",
    long_description="FHIR R4 Communication resource implementation for OpenIMIS",
    long_description_content_type="text/markdown",
    url="https://github.com/openimis/openimis-be-api_fhir_r4_py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "django>=3.2,<4.0",
        "djangorestframework>=3.12.0",
        "fhir.resources>=6.0.0",
    ],
)
