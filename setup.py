from setuptools import  setup

setup(
    name="flasktest",
    packages = ['flasktest'],
    include_package_data = True,
    install_requires = [
        'flask',
    ],
)