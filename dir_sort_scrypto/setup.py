from setuptools import setup, find_namespace_packages

setup(name='sort_dir',
      version='3',
      description='Sorting directory from given path by file extensions ',
      url='https://github.com/dJg-jpeg/GoIT-Python/tree/main/dir_sort_scrypto',
      author='dJg.jpeg',
      author_email='vvl5656@gmail.com',
      license='MIT',
      packages=find_namespace_packages(),
      entry_points={'console_scripts': ['sort_dir = dir_sort_scrypto.dir_sort:main']})
