"""
Adapted from
https://slack.dev/python-slack-sdk/socket-mode/index.html
"""
import traceback
from functools import wraps

import io

from threading import Event

import yfinance as yf

from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

import matplotlib.pyplot as plt
import mplfinance as mpf


def log_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f'Exception in `{func.__name__}`')
            print(traceback.format_exc())
            raise e

    return wrapper


@log_exceptions
def process(client: SocketModeClient, req: SocketModeRequest):
    print(req.type, req.payload, req.to_dict())

    if req.type == 'slash_commands':
        command = req.payload['command']

        print(f'Received slash command {command}')

        # Acknowledge the request
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

        if command == '/monke-quote':
            # Parse command arguments
            cmd_args_str = req.payload['text']
            cmd_args = cmd_args_str.split()

            ticker = None
            duration = '30d'
            msg = ''

            usage_msg = 'Usage: /monke-quote ticker [duration=30d]'
            blame_msg = (f'Requested by {req.payload["user_name"]} with the '
                         f'command `/monke-quote {cmd_args_str}`')

            if len(cmd_args) == 0:
                msg = usage_msg
            elif len(cmd_args) == 1:
                ticker = cmd_args[0]
            elif len(cmd_args) == 2:
                ticker, duration = cmd_args
            else:
                msg = (f'Error: {len(cmd_args)}>2 arguments received. '
                       f'{usage_msg}')

            if ticker is not None:
                ticker = ticker.upper()
                duration = duration.lower()

                yf_ticker = yf.Ticker(ticker)
                hist = yf_ticker.history(period=duration)
                if len(hist):
                    print(f'Got history {ticker} with duration {duration}')
                    last = hist.iloc[-1]
                    if len(hist) > 1:
                        first = hist.iloc[0]
                        prev_day = hist.iloc[-2]
                        pct_change_time_frame = (
                                (last["Close"] - first["Close"]) /
                                first["Close"] * 100
                        )
                        pct_change_prev_day = (
                                (last["Close"] - prev_day["Close"]) /
                                prev_day["Close"] * 100
                        )
                        pct_change_str = (
                            f'\n%Chg Prev. Day={pct_change_prev_day:.2f}% | '
                            f'%Chg Time Frame={pct_change_time_frame:.2f}%\n'
                        )
                    else:
                        pct_change_str = ''
                    msg = (f'[{ticker} Quote {last.name}] '
                           f'Open={last["Open"]:.2f} High={last["High"]:.2f} '
                           f'Low={last["Low"]:.2f} Close={last["Close"]:.2f}'
                           f'{pct_change_str}\n'
                           f'{blame_msg}')

                    fig, *_ = mpf.plot(hist, type='candle', style='yahoo',
                                       volume=True, returnfig=True)

                    stringio = io.BytesIO()
                    fig.tight_layout()
                    fig.savefig(stringio, format='png')
                    stringio.seek(0)
                    plt.close(fig)

                    response = client.web_client.files_upload(
                        file=stringio,
                        filetype='png',
                        filename=f'monke_quote_{ticker}_{duration}.png',
                        initial_comment=msg,
                        channels=req.payload['channel_id'],
                    )
                    # print(response)
                    return
                else:
                    msg = f'Invalid ticker "{ticker}"'

            # Respond
            client.web_client.chat_postMessage(
                channel=req.payload['channel_id'],
                text=msg + f'\n{blame_msg}',
            )
            print(f'monke-quote respond {msg}')
        else:
            client.web_client.chat_postMessage(
                channel=req.payload['channel_id'],
                text=f'Invalid command {command}',
            )
            print(f'Invalid command {command}')


def read_key(path):
    with open(path, 'r') as f:
        return f.read().strip()


def main():
    SLACK_APP_TOKEN = read_key('slack_app_token.txt')
    SLACK_BOT_TOKEN = read_key('slack_bot_user_oauth_token.txt')

    # Initialize SocketModeClient with an app-level token + WebClient
    client = SocketModeClient(
        # This app-level token will be used only for establishing a connection
        app_token=SLACK_APP_TOKEN,
        # You will be using this WebClient for performing Web API calls in
        #  listeners
        web_client=WebClient(token=SLACK_BOT_TOKEN)
    )

    # Add a new listener to receive messages from Slack
    # You can add more listeners like this
    client.socket_mode_request_listeners.append(process)
    # Establish a WebSocket connection to the Socket Mode servers
    client.connect()
    # Just not to stop this process
    Event().wait()


if __name__ == '__main__':
    # /monke-quote SOXL
    main()
