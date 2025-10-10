"""
Setup script for s-CGCNN package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README_v0.1.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="s-cgcnn",
    version="0.1.0",
    author="Abdullah Hasan Dafa",
    author_email="dafa.abdullahhasan@gmail.com",
    description="Simplified Graph Neural Networks for CPU-Efficient Screening of AlₓGa₁₋ₓAs Alloys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hasandafa/s-cgcnn",
    project_urls={
        "Bug Tracker": "https://github.com/hasandafa/s-cgcnn/issues",
        "Documentation": "https://github.com/hasandafa/s-cgcnn/blob/main/README_v0.1.md",
        "Source Code": "https://github.com/hasandafa/s-cgcnn",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "viz": [
            "jupyter>=1.0.0",
            "jupyterlab>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "s-cgcnn-fetch=src.data_acquisition.mp_fetcher:main",
            "s-cgcnn-interpolate=src.data_acquisition.structure_interpolator:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "materials-science",
        "graph-neural-networks",
        "semiconductor",
        "AlGaAs",
        "computational-materials",
        "machine-learning",
        "cpu-optimization",
        "materials-informatics",
    ],
)