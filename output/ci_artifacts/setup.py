from setuptools import find_packages, setup

setup(
    name="nodupe",
    version="1.0.0",
    description="Advanced duplicate file detection and management system",
    author="NoDupeLabs",
    packages=find_packages(where="."),
    package_dir={"": "."},
    include_package_data=True,
    install_requires=[
        "toml>=0.10.0",
        "psutil>=5.0.0",
        "PyYAML>=6.0",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "nodupe=nodupe.core.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
