# Setup
* Create a bot account on twitch
* Enable 2FA

* Register app on the bot account: https://dev.twitch.tv/console/apps/create
* Set OAuth redirect URL to: http://localhost:17563

* Copy example.ini to config.ini and modify.

* Install python and requirements
`py -m pip install -U twitchAPI`

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
