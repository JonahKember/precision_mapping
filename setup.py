from setuptools import setup, find_packages

setup(
    name='precision_mapping',
    version='0.4',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'precision_mapping = precision_mapping.main:main',
            'feature_extraction = feature_extraction.main:main'
        ],
    },
    install_requires=[
        'numpy',
        'scipy',
        'pandas',
        'nibabel',
    ],
    python_requires='>=3.6',
    package_data={
        'precision_mapping': ['data/*'],
    },
)
