from setuptools import (
    find_packages,
    setup,
)

setup(
    name='sudoku',
    version='1.0.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sudoku = sudoku.__main__:main'
        ]
    }
)
