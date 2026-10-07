# Security policy

## Supported versions

Refute is pre-1.0. Only the latest release on the `main` branch receives fixes.

## Reporting a vulnerability

Please do **not** open a public issue for security problems.

Use GitHub's private vulnerability reporting: open the repository's **Security**
tab and choose **Report a vulnerability**. Include:

- what is affected (file, command, version or commit),
- how to reproduce it,
- the impact you expect.

You should get an acknowledgement within 7 days. Fixes are released as soon as
practical, and reporters are credited unless they ask not to be.

## Scope notes

Refute downloads public scientific data and runs analysis code locally. Reports
about the following are especially welcome:

- ways to make `refute verify` accept a modified claim, attachment or code tree
  (lock bypass),
- ways for data or claim files to execute code or write outside the project,
- leaks of hidden holdout data into the training side of a blind test.

Refute never submits anything to scientific bodies and contains no credentials.
The pre-commit configuration runs `gitleaks` to keep secrets out of the history.
