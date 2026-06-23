from setuptools import setup, find_packages

setup(
    name="agent-os",
    version="0.1.0",
    description="A decoupled, standalone Agent OS containing Memory System 3.0 and Growth System 2.0",
    author="Wenchen Ma",
    packages=find_packages(),
    install_requires=[
        "lancedb>=0.6.0",
        "networkx>=3.0",
        "pydantic>=2.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "agent-os=agent_os.cli:main",
        ],
    },
    python_requires=">=3.9",
)
