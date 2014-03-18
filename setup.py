from setuptools import setup
setup(
    name='PyMImage',
    version='0.1',
    author='Ardo Illaste',
    author_email='ardo.illaste@gmail.com',
    packages=['pymimage',
              'pymimage.readers',
              'pymimage.converters'],
    url='https://github.com/ardoi/pymimage',
    license='LICENSE.txt',
    description='',
    package_data={'pymimage':[ 'bftools/*']},
    long_description=open('README.txt').read(),
    install_requires=[
        "numpy>=1.7.1",
        "inflect"
    ],
)
