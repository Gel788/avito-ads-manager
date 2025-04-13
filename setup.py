from setuptools import setup, find_packages

setup(
    name="avito_ads",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-sqlalchemy",
        "python-dotenv",
    ],
) 