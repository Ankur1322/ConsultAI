# CI installation

The Python CI job installs third-party runtime and test dependencies directly
and runs tests from the checked-out source tree. It does not install the local
`consultai` project package, so dependency auditing only evaluates packages
that are published and resolvable by the audit service.

The Docker image still installs the project package because that is required
for the deployed Uvicorn application.
