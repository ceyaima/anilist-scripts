# anilist-scripts

a collection of scripts I made to streamline the process of completing [AWC challenges](https://anilist.me/AWC).

### scripts available:
**convenience/**
- `date-retrieve.py` : adds start/finish dates to each requirement
- `community-list.py` : searches AWC's community lists for an anime
- `forum-search.py` : searches a forum thread for an anime

**puzzle/**
- `chess.py` : chooses animes for the [chess challenge](https://anilist.co/forum/thread/71984)
- `minesweeper.py` : chooses animes for the [minesweeper challenge](https://anilist.co/forum/thread/78688)

_**[>> check wiki for detailed description of each script <<](https://github.com/ceyaima/anilist-scripts/wiki)**_

---

## usage
created and tested on _python 3.14.2_

**all scripts** require [requests](https://pypi.org/project/requests/) : `pip install requests`
**date-retrieve** and **chess** require [pyperclip](https://pypi.org/project/pyperclip/) : `pip install pyperclip`


most scripts run solely in the terminal. only **minesweeper** generates a txt file output
```
python path/to/script.py
```







