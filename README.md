# JATT MUSIC BOT

A powerful, feature-rich Telegram Voice Chat music bot built with Pyrogram and PyTgCalls.

## Features

- **High Quality Audio** — Ultra quality streaming via yt-dlp
- **YouTube Integration** — Play by name, URL, search (5 results), or full playlist
- **Audio Effects** — Bass boost, reverb, nightcore, speed/pitch/volume control
- **Smart Queue** — Pagination, shuffle, move, remove, skip-to, duplicate prevention
- **Now Playing Card** — 1280×400px card with blurred thumbnail, progress ring, and real-time updates
- **On-Demand Autoplay** — `/autoplay` finds and queues a similar song (you stay in control)
- **24/7 Mode** — Keep the bot in VC even when idle
- **Permission System** — Owner → Sudo → Group Admin → DJ → Everyone
- **Global Moderation** — gban, gmute, gkick across all groups
- **Stats & Leaderboards** — Top plays, top DJs, weekly charts, group stats
- **Anti-Flood** — 3s cooldown per user on play commands
- **Auto Pin/Unpin** — NP card pinned automatically, unpinned on skip/stop
- **MongoDB** — 9 collections with TTL indexes for play stats (30-day retention)

## Requirements

- Python 3.11+
- FFmpeg installed on the system
- MongoDB instance (Atlas free tier works)
- Telegram API credentials

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/jatt-music-bot.git
cd jatt-music-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get an Assistant Session String

You need a Pyrogram session string for the assistant (userbot) account that will join voice chats.

```bash
python genstring.py
```

Follow the prompts — it will print your `ASSISTANT_SESSION` string. Keep it secret.

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

| Variable | Required | Description |
|---|---|---|
| `API_ID` | Yes | Telegram API ID from my.telegram.org |
| `API_HASH` | Yes | Telegram API Hash |
| `BOT_TOKEN` | Yes | Bot token from @BotFather |
| `OWNER_ID` | Yes | Your Telegram user ID |
| `ASSISTANT_SESSION` | Yes | Pyrogram session string for userbot |
| `MONGO_URI` | Yes | MongoDB connection string |
| `START_IMAGE_URL` | Yes | Image URL for /start command |
| `LOG_GROUP_ID` | No | Group/channel ID for logs |
| `SUDO_USERS` | No | Comma-separated sudo user IDs |
| `OWNER_CHANNEL` | No | Your channel link |
| `SUPPORT_GROUP` | No | Support group link |
| `UPDATE_CHANNEL` | No | Updates channel link |

### 5. Run the bot

```bash
python main.py
```

### Docker

```bash
docker build -t jatt-music-bot .
docker run --env-file .env jatt-music-bot
```

### Deploy on Render

1. Create a new **Background Worker** on [Render](https://render.com)
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python main.py`
5. Add all environment variables from `.env.example`

## Commands

### Everyone
| Command | Description |
|---|---|
| `/play <name or URL>` | Play a song |
| `/song <name or URL>` | Alias for /play |
| `/vplay <name or URL>` | Play video in VC |
| `/search <query>` | Search YouTube (5 results) |
| `/playlist <URL>` | Load a YouTube playlist |
| `/np` | Now playing card |
| `/queue` | View queue with pagination |
| `/history` | Last 10 played songs |
| `/replay` | Replay current song |
| `/skipto <number>` | Jump to track number |
| `/songinfo` | Full song info |
| `/mysongs` | Songs you requested |

### DJ / Admin
| Command | Description |
|---|---|
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/mute` | Mute bot audio in VC |
| `/unmute` | Unmute bot audio in VC |
| `/skip` | Skip to next track |
| `/stop` | Stop and leave VC |
| `/shuffle` | Shuffle the queue |
| `/loop` | Toggle loop mode |
| `/seek <time>` | Seek (1:30 / 90 / +30s / -15s) |
| `/speed <0.5–2.0>` | Change playback speed |
| `/bass <1–10>` | Bass boost |
| `/pitch <0.5–2.0>` | Change pitch |
| `/reverb` | Toggle reverb |
| `/nightcore` | Toggle nightcore |
| `/normalise` | Reset all effects |
| `/volume <0–200>` | Set volume |
| `/remove <pos>` | Remove a track |
| `/move <from> <to>` | Move a track |
| `/clearqueue` | Clear queue |
| `/fix` | Force reconnect to VC |
| `/autoplay` | Queue a similar song (on demand) |
| `/247` | Toggle 24/7 mode |
| `/invite` | Invite members to VC |
| `/playforce <name>` | Force play (skips current) |

### Group Admin
| Command | Description |
|---|---|
| `/auth` | Reply to grant DJ role |
| `/unauth` | Reply to remove DJ role |
| `/adminonly` | Toggle admin-only controls |
| `/setlog <channel_id>` | Set log channel |
| `/setwelcome <text>` | Set welcome message |
| `/setprefix <symbol>` | Change command prefix |
| `/quality <high/medium/low>` | Set audio quality |
| `/topplays` | Top 5 most played songs |
| `/topdjs` | Top 5 requesters |
| `/groupstats` | Group music stats |
| `/weekly` | Top 5 songs this week |
| `/leaderboard` | Full requester leaderboard |
| `/ban` | Ban user from bot |
| `/unban` | Unban user |

### Owner / Sudo (DM only)
| Command | Description |
|---|---|
| `/broadcast -all/-users/-groups/-pin <text>` | Broadcast message |
| `/stats` | Global statistics |
| `/maintenance` | Toggle maintenance mode |
| `/ping` | Response time |
| `/uptime` | Bot uptime |
| `/botinfo` | Bot version and info |
| `/gban <user_id>` | Ban from all groups |
| `/ungban <user_id>` | Remove global ban |
| `/gmute <user_id>` | Mute in all groups |
| `/ungmute <user_id>` | Remove global mute |
| `/gkick <user_id>` | Kick from all groups |
| `/gbanlist` | List gbanned users |
| `/gmutelist` | List gmuted users |

## Architecture

```
jatt_music_bot/
├── main.py              Entry point — starts bot, assistant, pytgcalls
├── config.py            All settings from env
├── database.py          All MongoDB operations (9 collections)
├── Dockerfile           Docker deployment
├── requirements.txt     Python dependencies
├── .env.example         Environment variable template
│
├── core/
│   └── stream.py        Stream manager (play/pause/skip/seek/effects/timers)
│
├── helpers/
│   ├── downloader.py    yt-dlp YouTube fetcher + search
│   ├── thumbnails.py    Now Playing card generator (Pillow)
│   ├── antiflood.py     Per-user cooldown
│   ├── pinmanager.py    Auto pin/unpin NP messages
│   ├── autoplay.py      On-demand similar song finder
│   └── logger.py        Startup + error logging
│
├── plugins/
│   ├── start.py         /start /help
│   ├── play.py          /play /song /vplay /playforce
│   ├── controls.py      Playback controls + NP inline buttons
│   ├── effects.py       Audio effects
│   ├── queue.py         Queue management + /autoplay
│   ├── search.py        /search with 5 inline results
│   ├── playlist.py      /playlist YouTube URL
│   ├── admin.py         Group admin commands + welcome handler
│   ├── stats.py         Statistics and leaderboards
│   ├── moderation.py    Global ban/mute/kick + auto-delete
│   ├── owner.py         Owner/sudo commands + broadcast
│   ├── invite.py        /invite members to VC
│   ├── vc247.py         /247 toggle
│   └── utils.py         Keyboards, decorators, permission checks
│
└── assets/
    └── fonts/           Roboto/Liberation fonts for NP card
```

## Architecture Notes

- **`on_stream_end` handler**: When a track finishes, the stream manager auto-advances the queue with full loop mode support (off / track / queue). This is the most critical piece — without it the bot plays one song and stops.
- **Loop mode**: Stored in MongoDB per-chat. `/loop` opens an inline keyboard to switch between `off`, `track`, and `queue`.
- **Auto-reconnect**: If the assistant is kicked from VC, it attempts to reconnect once after 3 seconds.
- **Mute/unmute VC**: `/mute` and `/unmute` mute/unmute the bot's audio stream in the voice chat (separate from Telegram's own mute).
- **Autoplay is on-demand**: `/autoplay` queues a similar song manually — it does NOT auto-queue when the queue ends. This gives you full control.
- **Assistant account**: The bot account handles commands; the assistant (userbot) joins voice chats to stream audio. Run `genstring.py` once to generate the session string.
- **FFmpeg required**: Audio effects (bass, reverb, nightcore, speed, pitch) all run through FFmpeg filter chains via pytgcalls `MediaStream`.
- **Smart queue**: Duplicate songs (same YouTube video ID) are blocked from being added twice.
- **Non-blocking thumbnail generation**: The Now Playing card fetches the thumbnail via async httpx and runs all Pillow (image) work in a thread executor — the event loop stays free.
- **In-memory queue cache**: Active queues are mirrored to an in-memory dict for hot-path speed; MongoDB is the persistent store.

## License

MIT License — free to use, modify, and distribute.
