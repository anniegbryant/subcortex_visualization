from setuptools import setup, find_packages

setup(
    name='subcortex_visualization',
    version='0.1',
    description='Visualize subcortical brain data from SVG templates',
    author='Your Name',
    packages=find_packages(),
    package_data={
        'subcortex_visualization': ['data/*.svg', 'data/*.csv'],
    },
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'svgpath2mpl',
        'ipython',
    ],
)
