import os
import subprocess
import shutil
import winreg
from pathlib import Path
from urllib.parse import quote_plus
import threading
import time
import webbrowser

import httpx
import uvicorn

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# ============================================================
# НАСТРОЙКИ
# ============================================================


BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "static"
CHARACTERS_DIR = STATIC_DIR / "characters"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)

BACKGROUND_FILE = STATIC_DIR / "forza.jpg"

print("Папка проекта:", BASE_DIR)
print("Папка static:", STATIC_DIR)
print("Файл фона:", BACKGROUND_FILE)
print("Фон найден:", BACKGROUND_FILE.is_file())

HOST = "127.0.0.1"
PORT = 9012


# ============================================================
# STEAM
# ============================================================

def find_steam_exe():
    # 1. PATH
    steam = shutil.which("steam.exe")

    if steam and Path(steam).exists():
        return Path(steam)

    # 2. Обычные папки
    paths = [

        Path(os.environ.get("PROGRAMFILES(X86)", "")) /
        "Steam" /
        "steam.exe",

        Path(os.environ.get("PROGRAMFILES", "")) /
        "Steam" /
        "steam.exe",

        Path(os.environ.get("LOCALAPPDATA", "")) /
        "Programs" /
        "Steam" /
        "steam.exe",

        Path("C:/Steam/steam.exe")
    ]

    for path in paths:

        if path.exists():
            return path

    # 3. Реестр Windows
    registry_locations = [

        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Valve\Steam"
        ),

        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Valve\Steam"
        ),

        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Valve\Steam"
        )
    ]

    for hive, key_path in registry_locations:

        try:

            with winreg.OpenKey(
                    hive,
                    key_path
            ) as key:

                install_path, _ = winreg.QueryValueEx(
                    key,
                    "InstallPath"
                )

                steam_path = (
                        Path(install_path)
                        / "steam.exe"
                )

                if steam_path.exists():
                    return steam_path

        except (FileNotFoundError, OSError):

            pass

    return None


def launch_steam_game(appid: int):
    steam = find_steam_exe()

    print(
        f"🎮 Запуск Steam AppID: {appid}"
    )

    if steam:

        print(
            f"✅ Steam найден: {steam}"
        )

        try:

            subprocess.Popen(
                [
                    str(steam),
                    "-applaunch",
                    str(appid)
                ],
                cwd=str(steam.parent)
            )

            return {
                "success": True,
                "method": "steam.exe",
                "appid": appid
            }

        except Exception as e:

            print(
                f"❌ Ошибка запуска Steam: {e}"
            )

    # Запасной вариант
    try:

        os.startfile(
            f"steam://rungameid/{appid}"
        )

        return {
            "success": True,
            "method": "steam-url",
            "appid": appid
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Game Music Dance",
    version="5.0"
)

# ============================================================
# STATIC
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# ============================================================
# ПЕРСОНАЖИ
# ============================================================

CHARACTERS = [

    {
        "id": "spiderman",
        "name": "Spider-Man",
        "image": "/static/characters/spiderman.png",

        "game": "Marvel Contest of Champions",

        "launch_url": "steam://rungameid/3127280",
        "store_url": "https://store.steampowered.com/app/3127280/",
        "type": "steam",

        "steam_appid": 3127280,

        "requires_license": True,

        "role": "Супергерой",

        "voice": (
            "Я Человек Паук! "
            "Город нуждается в моей помощи!"
        ),

        "description": (
            "Spider-Man — герой Marvel, "
            "который защищает Нью-Йорк."
        ),

        "stats": {
            "Сила": 92,
            "Скорость": 98,
            "Прыжок": 100,
            "Выносливость": 90,
            "Ловкость": 100
        }
    },

    {
        "id": "skyline",
        "name": "Nissan Skyline",
        "image": "/static/characters/skyline.png",

        "game": "Car Mechanic Simulator 2026 Demo",

        "launch_url": "steam://rungameid/4307740",
        "store_url": "https://store.steampowered.com/app/4307740/",
        "type": "steam",

        "steam_appid": 4307740,
        "requires_license": False,

        "role": "Гоночный автомобиль",
        "voice": "Nissan Skyline готов к гонке!",

        "description": (
            "Легендарный японский автомобиль "
            "для любителей скорости."
        ),

        "stats": {
            "Сила": 88,
            "Скорость": 99,
            "Прыжок": 20,
            "Выносливость": 95,
            "Ловкость": 85
        }
    },

    {
        "id": "mickey",
        "name": "Mickey Mouse",
        "image": "/static/characters/mickey.png",

        "game": "Castle of Illusion",

        "launch_url": "steam://rungameid/227600",
        "store_url": "https://store.steampowered.com/app/227600/Castle_of_Illusion/",
        "type": "steam",

        "steam_appid": 227600,

        "requires_license": True,

        "role": "Герой",

        "voice": (
            "Ох, привет! Это Микки Маус!"
        ),

        "description": (
            "Микки отправляется в необычное приключение."
        ),

        "stats": {
            "Сила": 70,
            "Скорость": 82,
            "Прыжок": 90,
            "Выносливость": 80,
            "Ловкость": 95
        }
    },

    {
        "id": "noob",
        "name": "Noob",
        "image": "/static/characters/noob.png",

        "game": "Terraria",

        "launch_url": "steam://rungameid/105600",
        "store_url": "https://store.steampowered.com/app/105600/",
        "type": "steam",

        "steam_appid": 105600,

        "requires_license": True,

        "role": "Игрок",

        "voice": (
            "Я новичок, но скоро стану профессионалом!"
        ),

        "description": (
            "Noob исследует огромный игровой мир."
        ),

        "stats": {
            "Сила": 65,
            "Скорость": 70,
            "Прыжок": 75,
            "Выносливость": 78,
            "Ловкость": 72
        }
    },

{
    "id": "steve",
    "name": "Steve",
    "image": "/static/characters/steve.png",

    "game": "Minecraft",
    "launch_url": "tlauncher://",
    "store_url": "https://tlauncher.org/",
    "type": "tlauncher",

    "requires_license": False,

    "role": "Выживший",
    "voice": "Я Стив! Пора строить!",

    "description": (
        "Стив умеет добывать ресурсы, "
        "строить и исследовать мир."
    ),

    "stats": {
        "Сила": 85,
        "Скорость": 70,
        "Прыжок": 75,
        "Выносливость": 95,
        "Ловкость": 70
    }
},

    {
        "id": "dizzy_two",
        "name": "Dizzy Two",
        "image": "/static/characters/dizzy_two.png",

        "game": "Dizzy Two",

        "launch_url": "steam://rungameid/1515990",
        "store_url": "https://store.steampowered.com/app/1515990/",
        "type": "steam",

        "requires_license": False,

        "role": "Герой приключений",

        "voice": (
            "Привет! Я Dizzy Two!"
        ),

        "description": (
            "Dizzy Two — приключенческая игра "
            "с классическим стилем."
        ),

        "stats": {
            "Сила": 75,
            "Скорость": 80,
            "Прыжок": 95,
            "Выносливость": 85,
            "Ловкость": 92
        }
    },
    {
        "id": "dota2",
        "name": "Djgertayn",
        "image": "/static/characters/dota2.png",

        "game": "Dota 2",
        "launch_url": "steam://rungameid/570",
        "store_url": "https://store.steampowered.com/app/570/",
        "type": "steam",
        "steam_appid": 570,
        "requires_license": False,
        "role": "MOBA",
        "voice": "Dota 2 готова к игре!",
        "description": "Командная игра с героями и стратегией.",
        "stats": {
            "Сила": 90,
            "Скорость": 80,
            "Прыжок": 70,
            "Выносливость": 90,
            "Ловкость": 85
        }
    },
    {
        "id": "cs2",
        "name": "Special Forces",
        "image": "/static/characters/cs2.png",

        "game": "Counter-Strike 2",
        "launch_url": "steam://rungameid/730",
        "store_url": "https://store.steampowered.com/app/730/",
        "type": "steam",
        "steam_appid": 730,
        "requires_license": False,
        "role": "Командная игра",
        "voice": "Counter-Strike 2 запускается!",
        "description": "Командная игра с тактическими раундами.",
        "stats": {
            "Сила": 85,
            "Скорость": 90,
            "Прыжок": 70,
            "Выносливость": 90,
            "Ловкость": 95
        }
    },
    {
        "id": "stalzone",
        "name": "NPC",
        "image": "/static/characters/stalzone.png",

        "game": "STALZONE",
        "launch_url": "steam://rungameid/1818450",
        "store_url": "https://store.steampowered.com/app/1818450/",
        "type": "steam",
        "steam_appid": 1818450,
        "requires_license": False,
        "role": "Приключение",
        "voice": "STALZONE запускается!",
        "description": "Исследование большого игрового мира.",
        "stats": {
            "Сила": 85,
            "Скорость": 80,
            "Прыжок": 75,
            "Выносливость": 95,
            "Ловкость": 85
        }
    },

    {

        "id": "house_1000_doors",
        "name": "Katty",
        "image": "/static/characters/house_1000_doors.png",

        "game": "House of 1000 Doors: Family Secrets",
        "launch_url": "steam://rungameid/1151630",
        "store_url": "https://store.steampowered.com/app/1151630/",
        "type": "steam",
        "steam_appid": 1151630,
        "requires_license": True,
        "role": "Приключение",
        "voice": "Добро пожаловать в Дом тысячи дверей!",
        "description": (
            "Приключение с загадками, поиском предметов "
            "и исследованием таинственных мест."
        ),
        "stats": {
            "Сила": 70,
            "Скорость": 75,
            "Прыжок": 65,
            "Выносливость": 85,
            "Ловкость": 90
        }
    }
]

# ============================================================
# STEAM IMAGE CACHE
# ============================================================

steam_image_cache = {}


async def get_steam_image(appid: int):
    if appid in steam_image_cache:
        return steam_image_cache[appid]

    url = (
        "https://store.steampowered.com/api/appdetails"
        f"?appids={appid}&l=russian"
    )

    try:

        async with httpx.AsyncClient(
                timeout=10,
                follow_redirects=True
        ) as client:

            response = await client.get(url)

            if response.status_code != 200:
                return None

            data = response.json()

            app_data = (
                data
                .get(str(appid), {})
                .get("data", {})
            )

            # Сначала header_image
            image = app_data.get("header_image")

            # Запасной вариант
            if not image:
                image = app_data.get("capsule_image")

            if image:
                steam_image_cache[appid] = image

            return image

    except Exception as e:

        print(
            f"Steam image error {appid}: {e}"
        )

        return None


# ============================================================
# STEAM IMAGE API
# ============================================================

@app.get("/api/game-image/{appid}")
async def game_image(appid: int):
    image = await get_steam_image(appid)

    if not image:
        return JSONResponse(
            {
                "success": False,
                "message": "Изображение Steam не найдено"
            },
            status_code=404
        )

    return RedirectResponse(
        url=image,
        status_code=307
    )


# ============================================================
# CHARACTERS API
# ============================================================

@app.get("/api/characters")
async def get_characters():
    return {
        "success": True,
        "characters": CHARACTERS
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "project": "Game Music Dance",
        "version": "5.0"
    }


# ============================================================
# ASSETS CHECK
# ============================================================

@app.get("/api/assets")
async def assets():
    files = [
        "forza.jpg",
        "characters/spiderman.png",
        "characters/skyline.png",
        "characters/mickey.png",
        "characters/noob.png",
        "characters/steve.png",
        "characters/dizzy_two.png",
        "characters/dota2.png",
        "characters/cs2.png",
        "characters/stalzone.png",
        "characters/house_1000_doors.png"
    ]

    return {
        file: (STATIC_DIR / file).is_file()
        for file in files
    }


# ============================================================
# MUSIC SEARCH
# ============================================================

@app.get("/api/music")
async def music(
        q: str = Query(
            ...,
            min_length=1
        )
):
    try:

        url = "https://api.deezer.com/search/track"

        async with httpx.AsyncClient(
                timeout=15
        ) as client:

            response = await client.get(
                url,
                params={
                    "q": q,
                    "limit": 20
                }
            )

            response.raise_for_status()

            data = response.json()

        tracks = []

        for item in data.get("data", []):
            tracks.append({

                "title":
                    item.get("title", "Без названия"),

                "artist":
                    item.get("artist", {})
                    .get("name", "Unknown"),

                "album":
                    item.get("album", {})
                    .get("title", ""),

                "cover":
                    item.get("album", {})
                    .get("cover_big", ""),

                "audio":
                    item.get("preview", ""),

                "link":
                    item.get("link", ""),

                "duration":
                    item.get("duration", 0)
            })

        return {
            "success": True,
            "tracks": tracks
        }

    except Exception as e:

        return JSONResponse(
            {
                "success": False,
                "error": str(e)
            },
            status_code=500
        )


# ============================================================
# OLD SEARCH
# ============================================================

@app.get("/api/search")
async def search(
        q: str = Query("")
):
    if not q.strip():
        return {
            "success": False,
            "url": ""
        }

    return {
        "success": True,
        "url":
            "https://www.google.com/search?q="
            + quote_plus(q)
    }

# ============================================================
# АВТОМАТИЧЕСКИЙ ПОИСК TLAUNCHER
# ============================================================

def find_Tlauncher_exe():
    import winreg

    candidates = []

    # 1. Проверяем переменные окружения Windows
    env_paths = [
        Path(os.environ.get("APPDATA", "")) / ".tlauncher" / "TLauncher.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "TLauncher" / "TLauncher.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "TLauncher" / "TLauncher.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "TLauncher" / "TLauncher.exe",
        Path("C:/TLauncher/TLauncher.exe"),
        Path("D:/TLauncher/TLauncher.exe"),
        Path("E:/TLauncher/TLauncher.exe"),
    ]

    candidates.extend(env_paths)

    # 2. Ищем путь установки в реестре Windows
    registry_keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\TLauncher"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\TLauncher"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\TLauncher"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\TLauncher"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TLauncher"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\TLauncher"),
    ]

    for hive, key_path in registry_keys:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                for value_name in ("InstallLocation", "InstallPath", "DisplayIcon"):
                    try:
                        value, _ = winreg.QueryValueEx(key, value_name)

                        if value:
                            # DisplayIcon иногда содержит путь с кавычками
                            value = str(value).strip().strip('"')
                            path = Path(value)

                            if path.name.lower() == "tlauncher.exe":
                                candidates.append(path)
                            else:
                                candidates.append(path / "TLauncher.exe")

                    except OSError:
                        pass

        except OSError:
            pass

    # 3. Проверяем найденные варианты
    checked = set()

    for path in candidates:
        try:
            path = path.expanduser()

            if not str(path):
                continue

            path = path.resolve()

            if str(path).lower() in checked:
                continue

            checked.add(str(path).lower())

            if path.is_file() and path.name.lower() == "tlauncher.exe":
                print(f"✅ TLauncher найден: {path}")
                return path

        except (OSError, ValueError):
            continue

    # 4. Автоматический поиск по дискам Windows
    # Ищем только в распространённых папках, чтобы не сканировать
    # весь ноутбук целиком.
    search_roots = []

    for drive_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = Path(f"{drive_letter}:/")

        if not drive.exists():
            continue

        search_roots.extend([
            drive / "TLauncher",
            drive / "Games",
            drive / "Games" / "TLauncher",
            drive / "Program Files",
            drive / "Program Files (x86)",
            drive / "Users",
        ])

    for root in search_roots:
        if not root.is_dir():
            continue

        try:
            for directory, dirs, files in os.walk(root):
                # Не заходим в служебные и системные каталоги
                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in {
                        "windows",
                        "$recycle.bin",
                        "system volume information",
                        "node_modules",
                        ".git",
                    }
                ]

                for filename in files:
                    if filename.lower() == "tlauncher.exe":
                        found = Path(directory) / filename

                        print(f"✅ TLauncher найден: {found}")
                        return found

        except (OSError, PermissionError):
            continue

    print("❌ TLauncher.exe не найден. Проверь, установлен ли лаунчер.")
    return None


# ============================================================
# ЗАПУСК TLAUNCHER
# ============================================================

def launch_tlauncher():
    launcher = find_Tlauncher_exe()

    if launcher is None:
        return {
            "success": False,
            "error": (
                "TLauncher не найден автоматически. "
                "Убедись, что он установлен на ноутбуке."
            )
        }

    try:
        subprocess.Popen(
            [str(launcher)],
            cwd=str(launcher.parent)
        )

        return {
            "success": True,
            "method": "auto-detected",
            "path": str(launcher)
        }

    except OSError as e:
        return {
            "success": False,
            "error": f"Ошибка запуска TLauncher: {e}"
        }


# ============================================================
# LAUNCH GAME
# ============================================================

@app.get("/api/launch/{character_id}")
async def launch(character_id: str):

    character = next(
        (c for c in CHARACTERS if c["id"] == character_id),
        None
    )

    # Проверяем персонажа
    if character is None:
        return JSONResponse(
            {
                "success": False,
                "error": "Персонаж не найден"
            },
            status_code=404
        )

    # --------------------------------------------------------
    # TLAUNCHER — MINECRAFT
    # --------------------------------------------------------

    if character.get("type") == "tlauncher":
        result = launch_tlauncher()

        return JSONResponse(
            {
                "success": result["success"],
                "id": character["id"],
                "name": character["name"],
                "method": result.get("method"),
                "error": result.get("error")
            },
            status_code=200 if result["success"] else 500
        )

    # --------------------------------------------------------
    # STEAM — ИГРЫ
    # --------------------------------------------------------

    if character.get("type") == "steam":

        appid = character.get("steam_appid")

        if not appid:
            return JSONResponse(
                {
                    "success": False,
                    "error": "Steam AppID не указан"
                },
                status_code=500
            )

        result = launch_steam_game(int(appid))

        return JSONResponse(
            {
                "success": result.get("success", False),
                "id": character["id"],
                "name": character["name"],
                "appid": appid,
                "method": result.get("method"),
                "error": result.get("error")
            },
            status_code=200 if result.get("success") else 500
        )

    # --------------------------------------------------------
    # НЕИЗВЕСТНЫЙ ТИП
    # --------------------------------------------------------

    return JSONResponse(
        {
            "success": False,
            "error": "Неизвестный тип запуска игры"
        },
        status_code=400
    )

# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>GAME MUSIC DANCE</title>


<style>

/* =========================================================
   RESET
========================================================= */

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}


html,
body {
    min-height: 100%;
}


body {
    font-family: Arial, Helvetica, sans-serif;
    color: white;
    background-color: #07070c;
    background-image:
        linear-gradient(
            rgba(8, 5, 20, 0.22),
            rgba(8, 5, 20, 0.35)
        ),
        url("/static/forza.jpg");
    background-position: center;
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    min-height: 100vh;
    overflow-x: hidden;
}


/* =========================================================
   FANTASY FRAME
========================================================= */

body::before {

    content: "";

    position: fixed;

    inset: 12px;

    border: 2px solid
        rgba(215, 174, 70, 0.75);

    box-shadow:

        0 0 20px
            rgba(120, 70, 255, 0.4),

        inset 0 0 20px
            rgba(120, 70, 255, 0.15);

    pointer-events: none;

    z-index: 9999;
}


/* =========================================================
   HEADER
========================================================= */

header {

    position: relative;

    text-align: center;

    padding: 55px 20px 25px;

}


header h1 {

    font-size: 42px;

    letter-spacing: 5px;

    color: #f2cf66;

    text-shadow:

        0 0 10px #8b5cff,
        0 0 25px #4a1d99;

}


header p {

    margin-top: 10px;

    color: #ddd;

    font-size: 17px;

}


/* =========================================================
   MAIN
========================================================= */

.container {

    width: min(
        1200px,
        calc(100% - 40px)
    );

    margin: auto;

}


/* =========================================================
   PANELS
========================================================= */

.panel {
    background: rgba(245, 248, 255, 0.58);
    color: #171b2b;
    border: 2px solid rgba(255, 255, 255, 0.8);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 25px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.18);
    backdrop-filter: blur(5px);
}

.panel h2 {
    color: #171b2b;
    text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
}

.character {
    background: rgba(255, 255, 255, 0.65);
    color: #171b2b;
    border: 2px solid rgba(255, 255, 255, 0.9);
    border-radius: 18px;
    overflow: hidden;
    cursor: pointer;
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.18);
    transition: 0.25s;
}

.character-info h2 {
    color: #20264a;
    margin-bottom: 7px;
}

.character-info p {
    color: #333b50;
    line-height: 1.4;
}

.badge {
    display: inline-block;
    margin-top: 10px;
    padding: 5px 9px;
    border-radius: 7px;
    background: rgba(104, 71, 167, 0.15);
    color: #38215f;
    font-size: 12px;
}


/* =========================================================
   SEARCH
========================================================= */

.search-row {

    display: flex;

    gap: 10px;

    flex-wrap: wrap;
}


input {

    flex: 1;

    min-width: 220px;

    padding: 15px 18px;

    border-radius: 12px;

    border: 1px solid #9c70df;

    background: #11101b;

    color: white;

    outline: none;

    font-size: 16px;
}


button {

    border: none;

    border-radius: 12px;

    padding: 13px 20px;

    cursor: pointer;

    color: white;

    font-weight: bold;

    background:
        linear-gradient(
            135deg,
            #7146c7,
            #a87927
        );

    box-shadow:
        0 5px 15px
        rgba(0, 0, 0, 0.3);

    transition: 0.2s;
}


button:hover {

    transform: translateY(-2px);

    filter: brightness(1.15);

}


button:active {

    transform: scale(0.97);
}


/* =========================================================
   MUSIC
========================================================= */

.music-results {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(230px, 1fr)
        );

    gap: 15px;

    margin-top: 20px;
}


.music-card {

    background: rgba(15, 15, 25, 0.9);

    border: 1px solid #6847a7;

    border-radius: 14px;

    overflow: hidden;

    padding-bottom: 15px;
}


.music-card img {

    width: 100%;

    height: 190px;

    object-fit: cover;
}


.music-card h3 {

    padding: 12px 14px 3px;

    font-size: 17px;
}


.music-card p {

    padding: 0 14px;

    color: #bbb;

}


/* =========================================================
   CHARACTERS
========================================================= */

.characters {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(240px, 1fr)
        );

    gap: 22px;
}


.character {

    position: relative;

    min-height: 360px;

    overflow: hidden;

    cursor: pointer;

    border-radius: 18px;

    border: 2px solid #a87927;

    background:
        linear-gradient(
            145deg,
            rgba(35, 19, 60, 0.95),
            rgba(8, 8, 15, 0.95)
        );

    box-shadow:

        0 0 20px
            rgba(91, 49, 160, 0.3);

    transition: 0.25s;
}


.character:hover {

    transform:
        translateY(-7px)
        scale(1.02);

    border-color: #e4bd58;

    box-shadow:

        0 0 30px
            rgba(151, 86, 255, 0.55);
}


.character-image {

    width: 100%;

    height: 245px;

    object-fit: cover;

    display: block;

    background:
        radial-gradient(
            circle,
            #3b2365,
            #0d0b13
        );
}


.character-info {

    padding: 14px;

}


.character-info h2 {

    color: #f3d269;

    margin-bottom: 7px;
}


.character-info p {

    color: #bbb;

    line-height: 1.4;
}


.badge {

    display: inline-block;

    margin-top: 10px;

    padding: 5px 9px;

    border-radius: 7px;

    background: #34205b;

    color: #d8c1ff;

    font-size: 12px;
}


/* =========================================================
   MODAL
========================================================= */

.modal {

    display: none;

    position: fixed;

    inset: 0;

    background:
        rgba(0, 0, 0, 0.82);

    z-index: 5000;

    align-items: center;

    justify-content: center;

    padding: 20px;
}


.modal.active {

    display: flex;
}


.modal-box {

    width: min(
        800px,
        100%
    );

    max-height: 90vh;

    overflow-y: auto;

    border-radius: 20px;

    border: 2px solid #b88932;

    background:
        linear-gradient(
            145deg,
            #24143d,
            #090910
        );

    box-shadow:
        0 0 50px
        rgba(119, 60, 220, 0.5);

    padding: 25px;

    position: relative;
}


.close {

    position: absolute;

    right: 18px;

    top: 15px;

    font-size: 25px;

    cursor: pointer;

    color: #f0cf6a;
}


.modal-image {

    width: 100%;

    max-height: 320px;

    object-fit: cover;

    border-radius: 14px;

    margin-bottom: 18px;
}


.modal-box h2 {

    color: #f2d064;

    font-size: 30px;

    margin-bottom: 7px;
}


.modal-box h3 {

    color: #c9a5ff;

    margin-top: 18px;

    margin-bottom: 10px;
}


.description {

    color: #ccc;

    line-height: 1.6;
}


/* =========================================================
   STATS
========================================================= */

.stats {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(150px, 1fr)
        );

    gap: 10px;
}


.stat {

    background: rgba(255,255,255,0.04);

    border: 1px solid #52377e;

    border-radius: 10px;

    padding: 12px;
}


.stat-name {

    color: #aaa;

    font-size: 13px;

    margin-bottom: 5px;
}


.stat-value {

    font-size: 22px;

    color: #f2cf66;

    font-weight: bold;
}


/* =========================================================
   ACTIONS
========================================================= */

.actions {

    display: flex;

    gap: 10px;

    flex-wrap: wrap;

    margin-top: 20px;
}


/* =========================================================
   STATUS
========================================================= */

.status {

    text-align: center;

    color: #aaa;

    padding: 20px;
}


/* =========================================================
   FOOTER
========================================================= */

footer {

    text-align: center;

    color: #888;

    padding: 30px;

}


@media (max-width: 600px) {

    header h1 {

        font-size: 27px;

    }

    .character-image {

        height: 210px;

    }

}

</style>

</head>


<body>


<header>

    <h1>🎵 GAME MUSIC DANCE 🎮</h1>

    <p>
        Музыка • Персонажи • Игры • Танцы
    </p>

</header>


<main class="container">


    <!-- MUSIC -->

    <section class="panel">

        <h2>🎵 Поиск музыки</h2>

        <br>

        <div class="search-row">

            <input
                id="musicSearch"
                placeholder="Например: Michael Jackson"
            >

            <button onclick="searchMusic()">
                🔎 Найти
            </button>

        </div>

        <div
            id="musicResults"
            class="music-results"
        ></div>

    </section>


    <!-- CHARACTERS -->

    <section class="panel">

        <h2>🎮 Персонажи</h2>

        <br>

        <div
            id="characters"
            class="characters"
        >

            <div class="status">
                Загрузка персонажей...
            </div>

        </div>

    </section>


    <!-- DANCE -->

    <section class="panel">

        <h2>💃 Танцы</h2>

        <br>

        <button onclick="startDance()">
            🕺 ЗАПУСТИТЬ ТАНЕЦ
        </button>

        <button onclick="stopDance()">
            ⛔ ОСТАНОВИТЬ
        </button>

    </section>


</main>


<!-- MODAL -->

<div
    id="modal"
    class="modal"
    onclick="closeModalOutside(event)"
>

    <div
        class="modal-box"
        onclick="event.stopPropagation()"
    >

        <div
            class="close"
            onclick="closeModal()"
        >
            ✕
        </div>


        <img
            id="modalImage"
            class="modal-image"
            alt=""
        >


        <h2 id="modalName">
            Персонаж
        </h2>


        <p
            id="modalGame"
            style="color:#aaa;"
        ></p>


        <h3>📖 Описание</h3>

        <p
            id="modalDescription"
            class="description"
        ></p>


        <h3>📊 Характеристики</h3>

        <div
            id="stats"
            class="stats"
        ></div>


        <div class="actions">

            <button onclick="launchGame()">
                🎮 ЗАПУСТИТЬ ИГРУ
            </button>

            <button onclick="openStore()">
                🛒 STEAM
            </button>

            <button onclick="speakCurrent()">
                🔊 ОЗВУЧИТЬ
            </button>

        </div>

    </div>

</div>


<footer>

    GAME MUSIC DANCE © 2026

</footer>


<script>

/* =========================================================
   GLOBAL
========================================================= */

let characters = [];

let currentCharacter = null;

let danceTimer = null;


/* =========================================================
   LOAD CHARACTERS
========================================================= */

async function loadCharacters() {

    const container =
        document.getElementById("characters");

    try {

        const response =
            await fetch("/api/characters");

        const data =
            await response.json();

        if (!data.success) {

            throw new Error(
                "Не удалось получить персонажей"
            );
        }

        characters = data.characters || [];

        renderCharacters();

        // Автоматически запускаем танцы после появления карточек
        startDance();


    } catch (error) {

        console.error(error);

        container.innerHTML = `
            <div class="status">
                ❌ Ошибка загрузки персонажей
            </div>
        `;
    }
}


/* =========================================================
   RENDER CHARACTERS
========================================================= */

function renderCharacters() {

    const container =
        document.getElementById("characters");

    container.innerHTML = "";


    if (!characters.length) {

        container.innerHTML = `
            <div class="status">
                🎮 Персонажи не найдены
            </div>
        `;

        return;
    }


    characters.forEach(character => {

        const card =
            document.createElement("div");

        card.className =
            "character";


        card.onclick = () => {

            showCharacter(
                character.id,
                true
            );

        };


        card.innerHTML = `

            <img
                class="character-image"
                src="${character.image}"
                alt="${escapeHtml(character.name)}"
                loading="lazy"
                onerror="this.onerror=null; this.src='/static/characters/noob.png';"
            >

            <div class="character-info">

                <h2>
                    ${escapeHtml(character.name)}
                </h2>

                <p>
                    ${escapeHtml(character.game)}
                </p>

                <span class="badge">
                    ${escapeHtml(character.role)}
                </span>

            </div>
        `;


        container.appendChild(card);

    });
}


/* =========================================================
   SHOW CHARACTER
========================================================= */

function showCharacter(
    id,
    autoSpeak = false
) {

    currentCharacter =
        characters.find(
            c => c.id === id
        );


    if (!currentCharacter) {
        return;
    }


    document.getElementById(
        "modalName"
    ).textContent =
        currentCharacter.name;


    document.getElementById(
        "modalGame"
    ).textContent =
        currentCharacter.game;


    document.getElementById(
        "modalDescription"
    ).textContent =
        currentCharacter.description;


    const image =
        document.getElementById(
            "modalImage"
        );


    image.src =
        currentCharacter.image;


    image.alt =
        currentCharacter.name;


    image.onerror = function() {

        this.onerror = null;

        this.src =
            "/static/characters/noob.png";

    };


    renderStats(
        currentCharacter.stats
    );


    document
        .getElementById("modal")
        .classList.add("active");


    if (autoSpeak) {

        setTimeout(
            speakCurrent,
            250
        );

    }

}


/* =========================================================
   STATS
========================================================= */

function renderStats(stats) {

    const container =
        document.getElementById("stats");

    container.innerHTML = "";


    if (!stats) {
        return;
    }


    Object.entries(stats).forEach(
        ([name, value]) => {

            const element =
                document.createElement("div");

            element.className =
                "stat";

            element.innerHTML = `

                <div class="stat-name">
                    ${escapeHtml(name)}
                </div>

                <div class="stat-value">
                    ${value}
                </div>

            `;

            container.appendChild(element);

        }
    );
}


/* =========================================================
   SPEECH
========================================================= */

function speakCurrent() {

    if (!currentCharacter) {
        return;
    }


    if (!("speechSynthesis" in window)) {

        alert(
            "Ваш браузер не поддерживает озвучку."
        );

        return;
    }


    speechSynthesis.cancel();


    const text =
        currentCharacter.voice ||
        currentCharacter.name;


    const speech =
        new SpeechSynthesisUtterance(text);


    speech.lang = "ru-RU";

    speech.rate = 0.95;

    speech.pitch = 1.0;

    speech.volume = 1.0;


    speechSynthesis.speak(
        speech
    );
}


/* =========================================================
   LAUNCH GAME
========================================================= */

async function launchGame() {

    if (!currentCharacter) {
        return;
    }


    const gameName =
        currentCharacter.game;


    const button =
        document.querySelector(
            ".actions button"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "⏳ ЗАПУСК...";
    }


    try {

        const response =
            await fetch(
                "/api/launch/" +
                encodeURIComponent(
                    currentCharacter.id
                )
            );


        const data =
            await response.json();


        if (!data.success) {

            alert(
                "❌ Не удалось запустить игру\n\n" +
                (data.error || "Неизвестная ошибка")
            );

            return;
        }


        console.log(
            "Steam запущен:",
            data
        );


        alert(
            "🎮 Запускаю:\n" +
            gameName
        );


    } catch (error) {

        console.error(error);


        alert(
            "❌ Ошибка запуска:\n" +
            error.message
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "🎮 ЗАПУСТИТЬ ИГРУ";

        }

    }
}


/* =========================================================
   OPEN STORE
========================================================= */

function openStore() {

    if (!currentCharacter) {
        return;
    }


    window.open(
        currentCharacter.store_url,
        "_blank"
    );
}


/* =========================================================
   CLOSE MODAL
========================================================= */

function closeModal() {

    document
        .getElementById("modal")
        .classList.remove("active");

    speechSynthesis.cancel();
}


function closeModalOutside(event) {

    if (
        event.target.id === "modal"
    ) {

        closeModal();

    }

}


/* =========================================================
   DANCE
========================================================= */

function startDance() {

    stopDance();


    const images =
        document.querySelectorAll(
            ".character-image"
        );


    let angle = 0;


    danceTimer =
        setInterval(() => {

            angle += 1;


            images.forEach(
                (image, index) => {

                    const direction =
                        index % 2 === 0
                            ? 1
                            : -1;


                    image.style.transform =
                        `
                        translateY(
                            ${Math.sin(angle / 4) * 12}px
                        )
                        rotate(
                            ${Math.sin(angle / 5) * 4 * direction}deg
                        )
                        scale(
                            ${1 + Math.sin(angle / 5) * 0.025}
                        )
                        `;

                }
            );

        }, 30);
}


function stopDance() {

    if (danceTimer) {

        clearInterval(
            danceTimer
        );

        danceTimer = null;

    }


    document
        .querySelectorAll(
            ".character-image"
        )
        .forEach(image => {

            image.style.transform = "";

        });
}


/* =========================================================
   MUSIC SEARCH
========================================================= */

async function searchMusic() {

    const input =
        document.getElementById(
            "musicSearch"
        );


    const query =
        input.value.trim();


    const container =
        document.getElementById(
            "musicResults"
        );


    if (!query) {

        container.innerHTML = `
            <div class="status">
                Введите название песни
            </div>
        `;

        return;
    }


    container.innerHTML = `
        <div class="status">
            🔎 Ищу музыку...
        </div>
    `;


    try {

        const response =
            await fetch(
                "/api/music?q=" +
                encodeURIComponent(query)
            );


        const data =
            await response.json();


        if (
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Ошибка поиска"
            );

        }


        renderMusic(
            data.tracks || []
        );


    } catch (error) {

        console.error(error);


        container.innerHTML = `
            <div class="status">
                ❌ ${escapeHtml(error.message)}
            </div>
        `;
    }
}


/* =========================================================
   RENDER MUSIC
========================================================= */


function renderMusic(tracks) {
    const container = document.getElementById("musicResults");
    container.innerHTML = "";

    if (!tracks.length) {
        container.innerHTML = `
            <div class="status">😔 Ничего не найдено</div>
        `;
        return;
    }

    tracks.forEach(track => {
        const card = document.createElement("div");
        card.className = "music-card";

        card.innerHTML = `
            <img
                src="${escapeHtml(track.cover || "")}"
                alt=""
            >

            <h3>${escapeHtml(track.title)}</h3>
            <p>${escapeHtml(track.artist)}</p>

            ${track.audio ? `
                <div style="padding:12px 14px;">
                    <audio
                        controls
                        preload="none"
                        style="width:100%;"
                        src="${escapeHtml(track.audio)}"
                    ></audio>
                </div>
            ` : ""}

            ${track.link ? `
                <div style="padding:0 14px;">
                    <button class="deezer-button">
                        🎵 Открыть Deezer
                    </button>
                </div>
            ` : ""}
        `;

        const audio = card.querySelector("audio");

        if (audio) {
            // Началась музыка — включаем танцы
            audio.addEventListener("play", () => {
                startDance();
            });

            // Проверяем, не играет ли другой трек
            const checkMusic = () => {
                const allAudio = [
                    ...container.querySelectorAll("audio")
                ];

                const musicStillPlaying = allAudio.some(
                    item => !item.paused && !item.ended
                );

                if (!musicStillPlaying) {
                    stopDance();
                }
            };

            audio.addEventListener("pause", checkMusic);
            audio.addEventListener("ended", checkMusic);
        }

        const deezerButton =
            card.querySelector(".deezer-button");

        if (deezerButton) {
            deezerButton.addEventListener("click", () => {
                window.open(
                    track.link,
                    "_blank",
                    "noopener"
                );
            });
        }

        container.appendChild(card);
    });
}



/* =========================================================
   ENTER SEARCH
========================================================= */

document
    .getElementById("musicSearch")
    .addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter"
            ) {

                searchMusic();

            }

        }
    );


/* =========================================================
   ESC
========================================================= */

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape"
        ) {

            closeModal();

        }

    }
);


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================================
   START
========================================================= */

loadCharacters();

</script>

</body>

</html>
"""


# ============================================================
# ROOT
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


# ============================================================
# START SERVER
# ============================================================

def open_browser():
    time.sleep(1.5)

    webbrowser.open(
        f"http://{HOST}:{PORT}"
    )


if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🎵 GAME MUSIC DANCE")
    print("=" * 60)

    print(
        f"📁 BASE_DIR: {BASE_DIR}"
    )

    print(
        f"📁 STATIC: {STATIC_DIR}"
    )

    print(
        f"📁 CHARACTERS: {CHARACTERS_DIR}"
    )

    print()

    print(
        "🖼️ Проверка локальных файлов:"
    )

    check_files = [

        STATIC_DIR / "forza.jpg",

        CHARACTERS_DIR / "spiderman.png",
        CHARACTERS_DIR / "skyline.png",
        CHARACTERS_DIR / "mickey.png",
        CHARACTERS_DIR / "noob.png",
        CHARACTERS_DIR / "steve.png",
        CHARACTERS_DIR / "dizzy_two.png"
    ]

    for file in check_files:
        print(
            f"  {'✅' if file.exists() else '❌'} "
            f"{file}"
        )

    print()

    print(
        f"🌐 http://{HOST}:{PORT}"
    )

    print("=" * 60)
    print()

    threading.Thread(
        target=open_browser,
        daemon=True
    ).start()

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False
    )