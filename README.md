# Strava Kudos Giver 👍👍👍

Originally from [isaac-chung](https://github.com/isaac-chung/strava-kudos) which supports an run env via github workflows. Modified to run via systemd timer locally on a server.

A Python tool to automatically give [Strava](https://www.strava.com) Kudos to recent activities on your feed. There are a few repos that uses JavaScript like [strava-kudos-lambda](https://github.com/mjad-org/strava-kudos-lambda) and [strava-kudos](https://github.com/rnvo/strava-kudos).


## 🏃 Usage
1. Fork the repo
2. Setup pyenv
3. `pip install -r requirements.txt`
4. `playwright install`
5. Fill strava credentials inside env file
6. Adjust paths in service file
7. Copy service/timer to /etc/systemd/system
8. `systemctl daemon-reload`
9. `systemctl enable --now give_kudos.timer`
10. Give kudos automatically!
