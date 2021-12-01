"""Set up Voithos """
from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="voithos",
    packages=find_packages(),
    version="1.0",
    license="",
    description="Breqwatr's private cloud helper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kyle Pericak",
    author_email="kyle@breqwatr.com",
    download_url="https://github.com/breqwatr/voithos/archive/1.00.tar.gz",
    url="https://github.com/breqwatr/voithos",
    keywords=["Breqwatr", "Openstack", "Kolla", "Ceph", "Docker"],
    python_requires='>=3.0.0',
    install_requires=[
        "click",
        "boto3",
        "docker",
        "flake8",
        "gnocchiclient",
        "jinja2",
        "keystoneauth1",
        "psutil",
        "pylint",
        "pytest",
        "mysql-connector",
        "requests",
        "tqdm",
        "pyvmomi",
        "hurry.filesize",
    ],
    entry_points="""
        [console_scripts]
        voithos=voithos.cli.main:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
    ],
    package_data={"voithos": ["lib/files/grafana/*.json", "lib/files/horizon/*"]},
    include_package_data=True,
)
