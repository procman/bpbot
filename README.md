# BP Bot

# Setup
## Python
- Install Python (3.10 or above) (ensure Python is added ot PATH during install)
- In the project directory run `py -m pip install -r requirements.txt`

## Configuration
- Copy *example.ini* to *config.ini*
- In *config.ini* change *channel* to your channel name

## Twitch
* Create a Twitch account for the bot
* Enable 2FA on the bot account
* Register an app on the bot account: https://dev.twitch.tv/console/apps/create
    * Name it something (BPBot)
    * Set OAuth redirect URL to: http://localhost:17563
    * Copy the *Client ID* to *config.ini*
    * Get a new *Client Secret* and copy it to *config.ini*

# Usage
In the project directory run `py bpbot.py`. Press *Enter* to terminate the bot.

On the first run the bot will try to authenticate with Twitch:
- If a firewall popup appears make sure to allow access on private networks.
- Make sure to authorize with the bot account (not your main account). This may require signing in.

On future runs the authentication should be automatic.

# Implemented Commands
```
!bp-add name
!bp-remove name
!bp-give name amount
!bp-take name amount
!bp-set name amount
!bp-reset yes
!bp-save
!bp-load
!bp-show [name]
!bp-top
```

# TODO
* Automatic redemption for subs/bits/channel points (PubSub/EventSub)
