# relay-7c91

Shared public distribution hub for D4n13X projects: release downloads, package
feeds, public verification keys and distribution metadata.

Development repositories are managed separately. Publish only files intended for
public download here; private keys, credentials and development checkout history
must stay outside this repository.

## Project layout

New projects use `projects/<project-id>/`, with their own artifacts, metadata and
signing trust. See [publishing conventions](projects/README.md). A publisher must
preserve every other project's files.

The existing Game Cache feed remains at its original root-level URLs for
compatibility with installed clients. Those paths are reserved for that feed;
they do not limit this repository to Game Cache or OPNsense.

Base HTTPS URL: `https://d4n13x.github.io/relay-7c91/`.
