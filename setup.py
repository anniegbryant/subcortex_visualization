from setuptools import setup, find_packages

install_requires = [
        'numpy',
        'pandas',
        'matplotlib',
        'svgpath2mpl',
        'ipython',
]

setup(
    name='subcortex_visualization',
    version='1.2.1',
    description='Visualize subcortical brain data from SVG templates',
    author='Annie G. Bryant',
    packages=find_packages(),
    include_package_data=True,  # ← IMPORTANT
    package_data={
        'subcortex_visualization': ['data/*.svg', 'data/*.csv', 'atlases/*.nii.gz', 'atlases/*.csv'],
    },
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'svgpath2mpl',
        'ipython',
    ],
)
