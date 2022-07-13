"""Installation instructions for the tell-me-about application"""

import re
from pathlib import Path

from setuptools import setup, find_packages


def get_long_description():
    """Return a long description of tha parent package"""

    readme_file = Path(__file__).parent / 'README.md'
    return readme_file.read_text()


def get_requirements():
    """Return a list of package dependencies"""

    requirements_path = Path(__file__).parent / 'requirements.txt'
    with requirements_path.open() as req_file:
        return req_file.read().splitlines()


def get_meta():
    """Return package metadata including the:
        - author
        - version
        - license
    """

    init_path = Path(__file__).resolve().parent / 'apps/__init__.py'
    init_text = init_path.read_text()

    version_regex = re.compile("__version__ = '(.*?)'")
    version = version_regex.findall(init_text)[0]

    author_regex = re.compile("__author__ = '(.*?)'")
    author = author_regex.findall(init_text)[0]

    # license_regex = re.compile("__license__ = '(.*?)'")
    # license_type = license_regex.findall(init_text)[0]

    return author, version


_author, _version = get_meta()
setup(
    name='crc-wrappers',
    description='Command-line applications for interacting with HPC clusters at the Pitt CRC.',
    version=_version,
    packages=find_packages(),
    python_requires='>=3.7',
    entry_points="""
        [console_scripts]
        crc-idle=apps.crc_idle:CrcIdle.execute
        crc-interactive=apps.crc_interactive:CrcInteractive.execute
        crc-job-stats=apps.crc_job_stats:CrcJobStats.execute
        crc-proposal-end=apps.crc_proposal_end:CrcProposalEnd.execute
        crc-quota=apps.crc_quota:CrcQuota.execute
        crc-scancel=apps.crc_scancel:CrcScancel.execute
        crc-show-config=apps.crc_show_config:CrcShowConfig.execute
        crc-sinfo=apps.crc_sinfo:CrcSinfo.execute
        crc-squeue=apps.crc_squeue:CrcSqueue.execute
        crc-sus=apps.crc_sus:CrcSus.execute
        crc-usage=apps.crc_usage:CrcUsage.execute
        crc-scontrol=apps.crc_scontrol:CrcScontrol.execute
    """,
    install_requires=get_requirements(),
    author=_author,
    keyword='Pitt, CRC, HPC, wrappers',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    # license=_license_type,
    classifiers=[
        'Programming Language :: Python :: 3',
    ]
)
