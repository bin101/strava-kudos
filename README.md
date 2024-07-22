# Strava Kudos Giver 👍👍👍

Originally from [isaac-chung](https://github.com/isaac-chung/strava-kudos) which supports an run env via github workflows. Modified to run via systemd timer locally on a server.

A Python tool to automatically give [Strava](https://www.strava.com) Kudos to recent activities on your feed. There are a few repos that uses JavaScript like [strava-kudos-lambda](https://github.com/mjad-org/strava-kudos-lambda) and [strava-kudos](https://github.com/rnvo/strava-kudos).


## 🏃 Usage
1. Fork the repo
2. Setup pyenv and/or install playwright
3. Fill strava credentials inside env file
4. Adjust paths in service file
5. Copy service/timer to /etc/systemd/system
6. `systemctl daemon-reload`
7. `systemctl enable --now give_kudos.timer`
8. Give kudos automatically!
