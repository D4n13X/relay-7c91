# Project distributions

Each new project publishes within its own directory:

```text
projects/<project-id>/
```

Choose a stable project ID. Keep that project's release files, package feeds,
public verification keys and metadata inside its directory. Use immutable paths
for versioned downloads. Development source and build credentials belong in the
project's own development repository or private secret storage.

Publishers must update only their project's paths and preserve other projects.
Use separate signing keys and trust information for each project. GitHub deploy
keys grant repository-wide access, so directory ownership is a publishing rule,
not a GitHub permission boundary.

The existing root-level Game Cache feed predates this layout and remains available
at its current URLs for installed clients. Those legacy paths are reserved; new
projects use this directory instead of replacing root-level feed files.
