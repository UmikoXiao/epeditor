import os
from setuptools import setup, find_packages, Extension


setup(
    name='epeditor',
    version='0.2.1',
    description='package for multi energyplus files generation, simulation and result analysis',
    license='GPL Licence',
    author='Umiko',
    author_email='junx026@gmail.com',
    packages=find_packages(exclude=('test*',)),
    package_data={'epeditor': ['idd/*.idd'],},
    include_package_data=True,
    python_requires='>=3.7',
    url= 'www.tsinghua.edu.cn',
    install_requires=['numpy>=1.20', 'eppy>=0.5'],
    data_files=[],
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Development Status :: 4 - Beta"
    ],
    scripts=[],
)
