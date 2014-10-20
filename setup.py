from distutils.core import setup

setup(
    name = 'preservationist',
    py_modules = ['preservationist'],
    version = '1.0',
    description = 'Rsync-based backup system',
    author = 'Gregory Crosswhite',
    author_email = 'gcrosswhite@gmail.com',
    # url =
    classifiers = [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: Utilities',
    ],
     
)