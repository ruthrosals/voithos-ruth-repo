"""Set up Voithos """
import os
import pathlib
from setuptools import setup, find_packages

def data_files():
  """  package_data doesn't look for files recursively.
  This method returns list of all the data paths.
  """
  paths = []
  current_file_parent_dir = pathlib.Path(__file__).parent.absolute()
  files_dir = f"{current_file_parent_dir}/voithos/lib/files/"
  for (path, directories, filenames) in os.walk(files_dir):
      # Removes the path's substring before lib/files. Absolute path won't work in package_data.
      path = path[path.find('lib/files/'):]
      for filename in filenames:
          paths.append(os.path.join(path, filename))
  return paths
data_paths = data_files()

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
    package_data={'voithos': data_paths },
    include_package_data=True,
)
