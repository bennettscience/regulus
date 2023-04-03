# Requirements

- HTTP server (Apache, nginx)
- Application server (gunicorn)
- SQL database (SQLite, MySQL, Postres)
- Google account (Calendar integration, OpenID login)
- Google Apps Script webhook

## Using a Google Apps Script Webhook

Google makes it difficult to set up service accounts because they require full delegated access, which means it can act on behalf of any user in the domain. That isn't always an option, so a webhook became the next best solution.

[This blog post](https://blog.ohheybrian.com/2021/09/using-google-apps-script-as-a-webhook/) covers what a webhook is and how to set up a simple endpoint for your applicaiton. This repo contains a functional webhook ready to use with Regulus. Before you start the deployment process, you'll need a Google account which will act as the authorized calendar user.

To set up your webhook:

- Sign into the [Google Apps Script Dashboard][https://script.google.com] with your account.
- Click on **New Project** in the top left.
- Paste `webhook.js` into the file editor and save.

## Deployment

Clone this repo to your computer or host

`git clone https://github.com/bennettscience/regulus regulus`

### Config Variables

Regulus relies on several environment variables to function properly. Make a copy of `.env.sample` and populate it with your own values.

```text
SECRET_KEY='your_flask_secret_key'
GOOGLE_CLIENT_ID='your_client_id'
GOOGLE_CLIENT_SECRET='your_client_secret'
GOOGLE_CALENDAR_ID='your_calendar_id'
CALENDAR_HOOK_TOKEN='your_webhook_token'
CALENDAR_HOOK_URL='your_webhook_url'
CONTACT_EMAIL='email@example.com'
# Optional, allow only users from this domain to sign in
# ALLOWED_DOMAINS='example.com'
```
