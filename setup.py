"""Setup script for the catholic_calendar project."""

from setuptools import setup

with open('README.md', encoding='utf-8') as fp:
    long_description = fp.read()

setup(
    name='catholic_calendar',
    version='1.0.0',
    description='Generate modern Roman Catholic liturgical calendars using romcal.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/your-username/catholicCalendar',
    author='Catholic Calendar contributors',
    license='MIT',
    packages=['catholic_calendar'],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'catholic_calendar=catholic_calendar.cli:main',
        ],
    },
    include_package_data=True,
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    python_requires='>=3.9',
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Religion',
        'Natural Language :: English',
        'Topic :: Religion',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
