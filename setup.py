from setuptools import (
    find_packages,
    setup,
)


with open('test_requirements.txt') as f:
    test_requirements = f.readlines()


setup(
    name='sudoku',
    version='1.0.0',
    packages=find_packages(),
    test_requires=test_requirements,
    entry_points={
        'console_scripts': [
            'ku = sudoku.__main__:ku',
            'sudoku = sudoku.__main__:main',
        ]
    }
)
