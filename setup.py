#!/usr/bin/env python3
from setuptools import setup, find_namespace_packages

setup(
        name='pyecsca-codegen',
        author='Jan Jancar',
        author_email='johny@neuromancer.sk',
        version='0.2.0',
        packages=find_namespace_packages(include=["pyecsca.*"]),
        license="MIT",
        description="Python Elliptic Curve cryptography Side Channel Analysis toolkit (codegen package).",
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: MIT License",
            "Topic :: Security",
            "Topic :: Security :: Cryptography",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research"
        ],
        package_data={
            "pyecsca.codegen" : ["*.h", "*.inc", "asn1/", "bn/", "hal/", "hash/", "prng/", "simpleserial/",
                                 "templates/", "tommath/"]
        },
        #install_package_data=True,
        python_requires='>=3.8',
        install_requires=[
            "pyecsca",
            "chipwhisperer",
            "numpy",
            "scipy",
            "atpublic",
            "matplotlib",
            "fastdtw",
            "asn1crypto",
            "jinja2",
            "Click"
        ],
        extras_require={
            "dev": ["mypy", "flake8"],
            "test": ["nose2", "parameterized", "green", "coverage"]
        },
        entry_points="""
            [console_scripts]
            builder=pyecsca.codegen.builder:main
            client=pyecsca.codegen.client:main
        """
)
