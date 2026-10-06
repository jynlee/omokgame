import asyncio

import pygame  # noqa: F401  pygbag(웹)은 main.py의 import를 보고 웹용 pygame을 불러온다

from omok.game import main

asyncio.run(main())
