from distutils.core import setup
    
setup(
    name = "unxml",
    version = "0.0.1",
    py_modules = ["unxml"],
    scripts = ["unxml.py"],
    license = "LGPL",
    description = "Parse XML into python object hierarchy. Like perl's XML::Simple.",
    author = "karasuyamatengu",
    author_email = "karasuyamatengu@gmail.com",
    url = "https://github.com/tengu/unxml",
    classifiers = [
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        ],
    long_description = """ Load xml into composition of Python objects, like Perl's XML::Simple. 
Provides a simple interface for further simplifying the object hierarchy.
""",
    zip_safe=False,
    )
