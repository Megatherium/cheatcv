"""Setup configuration for CheatCV."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

setup(
    name='cheatcv',
    version='0.1.0',
    author='CheatCV Team',
    author_email='',
    description='A CLI tool for quick computer vision operations',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/cheatcv',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Image Processing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    install_requires=[
        'click>=8.0.0',
        'opencv-python>=4.5.0',
        'numpy>=1.20.0',
    ],
    entry_points={
        'console_scripts': [
            'cheatcv=cheatcv.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
