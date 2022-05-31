# CRC Wrapper Scripts

Custom CRC wrappers for common HPC commands

## Deployment

To deploy a new version of the wrapper scripts, start by tagging a new GitHub release.
Once the release is live, navigate to the directory of the deployed source code and checkout the new tag:

```bash
$ git fetch
$ git checkout tags/[RELEASETAG]
```

If you need to rollback to an earlier version, use the same `git` commands lsited above but with the appropraite tag. 
