# CRC Wrapper Scripts

Custom CRC wrappers for common HPC commands

## Deployment

Tagging a new GitHub release will automatically deploy the most recently tagged software version via GitHub actions.

If you need to roll back to a specific version, navigate to the directory of the deployed source code and checkout the new tag:

```bash
$ git fetch
$ git checkout tags/[RELEASETAG]
```
