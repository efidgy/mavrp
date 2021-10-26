from setuptools import setup


setup(
    name='mavrp',
    version='1.0',
    packages=[
        'mavrp',
        'mavrp.salesman',
    ],
    install_requires=[
        'ortools==9.1.9490',
    ],
    entry_points={
        'console_scripts': [
            'mavrp-salesman = mavrp.salesman.main:main',
        ],
    },
    data_files=[
        ('mavrp/salesman/data', [
            'mavrp/salesman/data/task.json',
        ])
    ],
)
