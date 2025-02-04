# -*- coding: utf-8 -*-
"""
setup.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

<Description>
"""

from setuptools import setup, find_packages

_ = setup(
    name="vcard_tracker",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "customtkinter>=5.2.0",  # Modern looking Tkinter widgets
        "pillow>=10.0.0",        # Image handling
        "sqlalchemy>=2.0.0",     # Database ORM
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pylint>=2.17.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    author="Jaynathias",
    # author_email="nope@example.com",
    description="A card collection tracking application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ncagle/VCard-Tracker",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
