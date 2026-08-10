# Stage-0 ALE geometry inputs

The Stage-0 parameter files use paths relative to this directory. Run them
through `run_case.sh`, whose default working directory is the parameter-file
directory. Output remains at the repository root through `../../output_*`.

The three HDF5 initial-condition files are local test data and are not stored in
Git. Their immutable identities are recorded in `ALE_STAGE0_ICS.sha256`. After
copying or regenerating them, verify them from this directory with:

```sh
sha256sum --quiet -c ALE_STAGE0_ICS.sha256
```

A different checksum defines a different numerical experiment and must not be
silently substituted into the recorded Stage-0 tables.
