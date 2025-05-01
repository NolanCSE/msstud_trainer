from setuptools import setup, find_packages

setup(
    name="msstud_trainer",
    version="0.1.0",
    description="Training and simulation suite for Mississippi Stud using card_lib",
    author="ProductionStructure",
    packages=find_packages(exclude=["tests", "notebooks", "data"]),
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "scipy",
        "card_lib @ git+https://github.com/NolanCSE/card_lib.git"
    ],
    entry_points={
        "console_scripts": [
            "msstud-train-basic = training.cli_basic:main",
            "msstud-train-ap3 = training.cli_ap_3rd:main",
            "msstud-train-ap5 = training.cli_ap_5th:main",
        ]
    },
    python_requires=">=3.8",
)
