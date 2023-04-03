# Regulus

Regulus is a self-hosted event registration and management system. Organizations can create events, manage attendance limits, and track participation all through a lightweight web application.

## Features

-  Google OpenID login
-  Google Calendar integrated
-  Semantic markup using [HTMX](https://htmx.org) and [_hyperscript](https://hyperscript.org)
-  Role-based access controls

## Contributing

To contribute bug fixes or enhancements, fork the repo and then clone to your machine. Install dependencies either with `pip install -f requirements.txt` or `poetry install`.

Any new feature should include new tests. Write your test in the appropriate file and add any fixtures necessary for the test in `tests/fixtures/[].json`. You can look at the existing tests to see how to structure tests.

If you're adding a new route, be sure to run your test within the `captured_templates()` context manager to make sure the correct template is returned.

I'm also happy to have contributions related to usability, documentation, or just ideas for how to improve the application. This was built mostly in my spare time and any added eyes are appreciated.

## Installation

If you want to install Regulus for yourself, detailed instructions are over [here](./INSTALL.md).
