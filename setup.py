from setuptools import find_packages
from setuptools import setup

with open("requirements.txt") as f:
    content = f.readlines()
requirements = [x.strip() for x in content]

setup(
    name="flatfindr",
    version="0.1",
    description="Project Description",
    packages=find_packages(),
    install_requires=requirements,
    test_suite="tests",
    # include_package_data: to install data from MANIFEST.in
    include_package_data=True,
    scripts=["scripts/flatfindr-run", "scripts/flatfindr-bot"],
    zip_safe=False,
)
