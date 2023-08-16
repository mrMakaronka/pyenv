import setuptools
from Cython.Build import cythonize

import Cython.Compiler.Options
Cython.Compiler.Options.annotate = True

import sys

version = sys.version_info
assert version.major == 3
assert version.minor >= 7

pyarrow_version = '>=0.17.1,<=5.0.0' if version.minor < 10 else '>=6.0.1'

setuptools.setup(
    name='ipystate',
    version='0.0.1',
    package_dir={'': 'src/main/python'},
    packages=['ipystate', 'ipystate/impl', 'ipystate/impl/dispatch'],
    install_requires=[
        'ipython>=7.13.0,<=7.19.0',
        'cloudpickle@git+https://github.com/AlvinMax/cloudpickle.git@feature/persistent-function-globals#egg=cloudpickle',
        f'pyarrow{pyarrow_version}',
        'pybase64>=1.0.2',
        'cython>=0.29.26',
        'pympler>=0.9',
        'packaging>=20.9',
    ],
    tests_require=[
        'numpy',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Framework :: IPython',
        'Framework :: Jupyter',
    ],
    include_package_data=True,
    ext_modules=cythonize(["src/main/python/ipystate/impl/walker.pyx"], annotate=True),
    zip_safe=False,
)
