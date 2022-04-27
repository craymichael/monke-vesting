# monke-vesting bot

Enables the Slack commands for an app:

- `/monke-quote ticker [duration=30d]` (example usage: `/monke-quote SOXL 1y`). Provides a quote for
the given duration (default period of 30 days) and a candlestick image using Yahoo finance data.

```shell
pip install -r requirements.txt
python run.py
```

To run this project, you will need to create the following files with appropriate contents:

- `slack_bot_user_oauth_token.txt` OAuth token for the Slack bot
- `slack_app_token.txt` App token for the Slack app
