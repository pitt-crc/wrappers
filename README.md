# CRC Wrapper Scripts

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/230da08d818542d4a4bb556880943dd5)](https://www.codacy.com/gh/pitt-crc/wrappers/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=pitt-crc/wrappers&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/230da08d818542d4a4bb556880943dd5)](https://www.codacy.com/gh/pitt-crc/wrappers/dashboard?utm_source=github.com&utm_medium=referral&utm_content=pitt-crc/wrappers&utm_campaign=Badge_Coverage)
[![Test Suite](https://github.com/pitt-crc/wrappers/actions/workflows/Unittests.yml/badge.svg)](https://github.com/pitt-crc/wrappers/actions/workflows/Unittests.yml)

Custom CRC wrappers for common HPC commands

## Deployment

To deploy a new version of the wrapper scripts, start by tagging a new GitHub release.
Once the release is live, navigate to the directory of the deployed source code and checkout the new tag:

```bash
git fetch
git checkout tags/[RELEASETAG]
```

If you need to roll back to an earlier version, use the same `git` commands listed above but with the appropriate tag. 
