from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass

from typing import Generator

import time
import os
import sys
import shutil
import traceback
import argparse

from base64 import b64encode

import json
from io import BytesIO

import importlib.util

from tkinter import messagebox, filedialog, simpledialog
import tkinter as Tk
import tkinter.ttk as ttk

import subprocess
from zipfile import ZipFile

# class to manipulate a vector2-type structure (X, Y)
# call the 'i' property to obtain an integer tuple to use with Pillow
dataclass(slots=True)
class v2():
    x : int|float = 0
    y : int|float = 0
    
    def __init__(self : v2, X : int|float, Y : int|float):
        self.x = X
        self.y = Y
    
    # operators
    def __add__(self : v2, other : v2|tuple|list|int|float) -> v2:
        if isinstance(other, float) or isinstance(other, int):
            return v2(self.x + other, self.y + other)
        else:
            return v2(self.x + other[0], self.y + other[1])
    
    def __radd__(self : v2, other : v2|tuple|list|int|float) -> v2:
        return self.__add__(other)

    def __mul__(self : v2, other : v2|tuple|list|int|float) -> v2:
        if isinstance(other, float) or isinstance(other, int):
            return v2(self.x * other, self.y * other)
        else:
            return v2(self.x * other[0], self.y * other[1])

    def __rmul__(self : v2, other : v2|tuple|list|int|float) -> v2:
        return self.__mul__(other)

    # for access via []
    def __getitem__(self : v2, key : int) -> int|float:
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError("Index out of range")

    def __setitem__(self : v2, key : int, value : int|float) -> None:
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Index out of range")

    # len is fixed at 2
    def __len__(self : v2) -> int:
        return 2

    # to convert to an integer tuple (needed for pillow)
    @property
    def i(self : v2) -> tuple[int, int]:
        return (int(self.x), int(self.y))

# wrapper class to store and manipulate Image objects
# handle the close() calls on destruction
dataclass(slots=True)
class IMG():
    parent : PartyBuilder = None
    image : Image = None
    buffer : BytesIO = None
    
    def __init__(self : IMG, src : str|bytes|IMG|Image) -> None:
        self.image = None
        self.buffer = None
        match src: # possible types
            case str(): # path to a local file
                self.image = Image.open(src)
                self.convert('RGBA')
            case bytes(): # bytes (usually received from a network request)
                self.buffer = BytesIO(src) # need a readable buffer for it, and it must stays alive
                self.image = Image.open(self.buffer)
                self.convert('RGBA')
            case IMG(): # another IMG wrapper
                self.image = src.image.copy()
            case _: # an Image instance. NOTE: I use 'case _' because of how import Pillow, the type isn't loaded at this point
                self.image = src

    def __del__(self : IMG) -> None:
        if self.image is not None:
            self.image.close()
        if self.buffer is not None:
            self.buffer.close()

    def convert(self : IMG, itype : str) -> None:
        tmp = self.image
        self.image = tmp.convert(itype)
        tmp.close()

    def copy(self : IMG) -> IMG:
        return IMG(self)

    def paste(self : IMG, other : IMG, offset : tuple[int, int]) -> None:
        self.image.paste(other.image, offset, other.image)

    def crop(self : IMG, size : tuple[int, int]|tuple[int, int, int, int]) -> IMG:
        # depending on the tuple size
        if len(size) == 4:
            return IMG(self.image.crop(size))
        elif len(size) == 2:
            return IMG(self.image.crop((0, 0, *size)))
        raise ValueError("Invalid size of the tuple passed to IMG.crop(). Expected 2 or 4, received {}.".format(len(size)))

    def resize(self : IMG, size : v2|tuple[int, int]) -> IMG:
        match size:
            case v2():
                return IMG(self.image.resize(size.i, Image.Resampling.LANCZOS))
            case tuple():
                return IMG(self.image.resize(size, Image.Resampling.LANCZOS))
        raise TypeError("Invalid type passed to IMG.resize(). Expected v2 or tuple[int, int], received {}.".format(type(size)))

    def alpha(self : IMG, layer : IMG) -> IMG:
        return IMG(Image.alpha_composite(self.image, layer.image))

# Main class
class PartyBuilder():
    NULL_CHARACTER = [3030182000, 3020072000] # null character id list (lyria, cat...), need to be hardcoded
    COLORS = { # color for estimated advantage
        1:(243, 48, 33),
        2:(85, 176, 250),
        3:(227, 124, 32),
        4:(55, 232, 16),
        5:(253, 216, 67),
        6:(176, 84, 251)
    }
    COLORS_EN = { # color string
        1:"Fire",
        2:"Water",
        3:"Earth",
        4:"Wind",
        5:"Light",
        6:"Dark"
    }
    COLORS_JP = { # color string
        1:"火",
        2:"水",
        3:"土",
        4:"風",
        5:"光",
        6:"闇"
    }
    AUXILIARY_CLS = [100401, 300301, 300201, 120401, 140401] # aux classes
    # IDs for special weapons
    DARK_OPUS_IDS = [
        "1040310600","1040310700","1040415000","1040415100","1040809400","1040809500","1040212500","1040212600","1040017000","1040017100","1040911000","1040911100",
        "1040310600_02","1040310700_02","1040415000_02","1040415100_02","1040809400_02","1040809500_02","1040212500_02","1040212600_02","1040017000_02","1040017100_02","1040911000_02","1040911100_02",
        "1040310600_03","1040310700_03","1040415000_03","1040415100_03","1040809400_03","1040809500_03","1040212500_03","1040212600_03","1040017000_03","1040017100_03","1040911000_03","1040911100_03"
    ]
    ULTIMA_IDS = [
        "1040011900","1040012000","1040012100","1040012200","1040012300","1040012400",
        "1040109700","1040109800","1040109900","1040110000","1040110100","1040110200",
        "1040208800","1040208900","1040209000","1040209100","1040209200","1040209300",
        "1040307800","1040307900","1040308000","1040308100","1040308200","1040308300",
        "1040410800","1040410900","1040411000","1040411100","1040411200","1040411300",
        "1040507400","1040507500","1040507600","1040507700","1040507800","1040507900",
        "1040608100","1040608200","1040608300","1040608400","1040608500","1040608600",
        "1040706900","1040707000","1040707100","1040707200","1040707300","1040707400",
        "1040807000","1040807100","1040807200","1040807300","1040807400","1040807500",
        "1040907500","1040907600","1040907700","1040907800","1040907900","1040908000"
    ]
    ORIGIN_DRACONIC_IDS = [
        "1040815900","1040316500","1040712800","1040422200","1040915600","1040516500"
    ]
    # User Agent (required for the wiki)
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Rosetta/Dev'
    
    def __init__(self : PartyBuilder) -> None:
        self.gbftmr = None # will contain a GBFTMR instance if configured properly
        self.bookmark : str|None = None # cached copy of bookmarklet.txt
        self.japanese : bool = False # True if the data is japanese, False if not
        self.classes : dict[str, str] = None # cached classes
        self.class_modified : bool = False
        self.prev_lang : str = None # Language used in the previous run
        self.babyl : bool = False # True if the data contains more than 5 allies
        self.sandbox : bool = False # True if the data contains more than 10 weapons
        self.pending : set[str] = set() # pending download
        self.cache : dict[str, IMG] = {} # memory cache
        self.emp_cache : dict[str, dict] = {} # emp cache
        self.sumcache : dict[str, str] = {} # wiki summon cache
        self.fonts : dict[str, ImageFont] = {'mini':None, 'small':None, 'medium':None, 'big':None} # font to use during the processing
        self.quality : float = 1 # quality ratio in use currently
        self.definition : tuple[int, int] = None # image size
        self.running : bool = False # True if the image building is in progress
        self.settings : dict[str, str|int|bool] = {} # settings.json data
        self.manifest : dict[str, str] = {} # manifest.json data
        # load stuff (import libraries, load JSON...)
        self.startup_check()
        self.load()
        # finish the initialization
        self.dummy_layer : IMG = self.blank_image()
        self.name : str = "GBFPIB " + self.manifest.get('version', '')
        self.client : aiohttp.ClientSession = None # container for the HTTP client
        if self.manifest.get('pending', False):
            self.manifest['pending'] = False
            self.saveManifest()

    # init the HTTP client
    @asynccontextmanager
    async def init_client(self : PartyBuilder) -> Generator[aiohttp.ClientSession, None, None]:
        try:
            self.client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
            yield self.client
        finally:
            await self.client.close()

    # transform an exception to a readable string
    def pexc(self : PartyBuilder, e : Exception) -> str:
        return "".join(traceback.format_exception(type(e), e, e.__traceback__))

    # load manifest.json
    def loadManifest(self : PartyBuilder) -> None:
        try:
            with open("manifest.json") as f:
                self.manifest = json.load(f)
        except:
            pass

    # save manifest.json
    def saveManifest(self : PartyBuilder) -> None:
        try:
            with open("manifest.json", 'w') as outfile:
                json.dump(self.manifest, outfile)
        except:
            pass

    # load classes.json
    def loadClasses(self : PartyBuilder) -> None:
        try:
            self.class_modified = False
            with open("classes.json", mode="r", encoding="utf-8") as f:
                self.classes = json.load(f)
        except:
            self.classes = {}

    # save classes.json
    def saveClasses(self : PartyBuilder) -> None:
        try:
            if self.class_modified:
                with open("classes.json", mode='w', encoding='utf-8') as outfile:
                    json.dump(self.classes, outfile)
        except:
            pass

    # import third-party modules
    def importRequirements(self : PartyBuilder) -> None:
        global aiohttp
        import aiohttp
        
        global Image
        global ImageFont
        global ImageDraw
        from PIL import Image, ImageFont, ImageDraw
        
        global pyperclip
        import pyperclip

    # ran on class creation
    def startup_check(self : PartyBuilder) -> None:
        self.loadManifest()
        if self.manifest.get('pending', False):
            if messagebox.askyesno(title="Info", message="I will now attempt to update required dependencies.\nDo you accept?\nElse it will be ignored if the application can start."):
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                    self.importRequirements()
                    messagebox.showinfo("Info", "Installation successful.")
                except Exception as e:
                    print(self.pexc(e))
                    if sys.platform == "win32": # Windows
                        import ctypes
                        is_admin : bool
                        try: is_admin = ctypes.windll.shell32.IsUserAnAdmin() # check for admin
                        except: is_admin = False
                        if not is_admin:
                            if messagebox.askyesno(title="Error", message="An error occured: {}\nDo you want to restart the application with administrator permissions?".format(e)):
                                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1) # restart as admin
                        else:
                            messagebox.showerror("Error", "An error occured: {}\nFurther troubleshooting is needed.\nYou might need to install the dependancies manually, check the README for details.")
                    else:
                        messagebox.showerror("Error", "An error occured: {}\nFurther troubleshooting is needed.\nYou might need to install the dependancies manually, check the README for details.")
                    os._exit(0)
        else:
            try:
                self.importRequirements()
            except Exception as e:
                print(self.pexc(e))
                if messagebox.askyesno(title="Error", message="An error occured while importing the dependencies: {}\nThey might be outdated or missing.\nRestart and attempt to install them now?".format(e)):
                    self.manifest['pending'] = True
                    self.saveManifest()
                    self.restart()
                os._exit(0)
        print("Granblue Fantasy Party Image Builder", self.manifest.get('version', ''))

    # load settings.json
    def load(self : PartyBuilder) -> None:
        try:
            with open('settings.json') as f:
                self.settings = json.load(f)
        except:
            print("Failed to load settings.json")
            while True:
                print("An empty settings.json file will be created, continue? (y/n)")
                match input().lower():
                    case 'n':
                        os._exit(0)
                    case 'y':
                        break
            self.save()

    # save settings.json
    def save(self : PartyBuilder) -> None:
        try:
            with open('settings.json', 'w') as outfile:
                json.dump(self.settings, outfile)
        except:
            pass

    # retrieve an image from the given path/url
    async def get(self : PartyBuilder, path : str, remote : bool = True, forceDownload : bool = False) -> bytes:
        # check language
        if self.japanese:
            path = path.replace('assets_en', 'assets')
        # check if retrieval is pending
        while path in self.pending:
            await asyncio.sleep(0.005)
        self.pending.add(path)
        try:
            # retrieve
            if forceDownload or path not in self.cache:
                try: # get from disk cache if enabled
                    if forceDownload:
                        raise Exception() # go to exception/download block
                    if self.settings.get('caching', False):
                        with open("cache/" + b64encode(path.encode('utf-8')).decode('utf-8'), "rb") as f:
                            self.cache[path] = IMG(f.read())
                        await asyncio.sleep(0)
                    else:
                        raise Exception()
                except: # else request it from gbf
                    if remote:
                        print("[GET] *Downloading File", path)
                        response : aiohttp.Response = await self.client.get('https://' + self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net/') + path, headers={'connection':'keep-alive'})
                        async with response:
                            if response.status != 200:
                                raise Exception("HTTP Error code {} for url: {}".format(response.status, 'https://' + self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net/') + path))
                            io : bytes = await response.read()
                            self.cache[path] = IMG(io)
                            if self.settings.get('caching', False):
                                try:
                                    with open("cache/" + b64encode(path.encode('utf-8')).decode('utf-8'), "wb") as f:
                                        f.write(io)
                                    await asyncio.sleep(0)
                                except Exception as e:
                                    print(self.pexc(e))
                                    pass
                    else:
                        with open(path, "rb") as f:
                            self.cache[path] = IMG(f.read())
                        await asyncio.sleep(0)
            # end
            self.pending.remove(path)
            return self.cache[path]
        except Exception as ex:
            self.pending.remove(path) # failsafe
            raise ex

    # paste an image onto our list of images for given range
    async def paste(self : PartyBuilder, imgs : list[IMG], indexes : range, file : str|IMG, offset : tuple[int, int], *, resize : tuple[int, int]|None = None, transparency : bool = False, crop : tuple[int, int]|tuple[int, int, int, int]|None = None) -> list[IMG]:
        # get file
        if isinstance(file, str):
            if self.japanese:
                file = file.replace('_EN', '')
            file = await self.get(file, remote=False)
        # crop
        if crop is not None:
            file = file.crop(crop)
        # resize
        if resize is not None:
            file = file.resize(resize)
        # paste
        if not transparency:
            for i in indexes:
                imgs[i].paste(file, offset)
        else:
            layer = self.dummy_layer.copy()
            layer.paste(file, offset)
            for i in indexes:
                imgs[i] = imgs[i].alpha(layer)
        await asyncio.sleep(0)
        # return
        return imgs

    # download and paste an image onto our list of images for given range
    async def pasteDL(self : PartyBuilder, imgs : list[IMG], indexes : range, path : str, offset : tuple[int, int], *, resize : tuple[int, int]|None = None, transparency : bool = False, crop : tuple[int, int]|tuple[int, int, int, int]|None = None) -> list: # dl an image and call pasteImage()
        return await self.paste(imgs, indexes, await self.get(path), offset, resize=resize, transparency=transparency, crop=crop)

    # write text on images
    def text(self : PartyBuilder, imgs : list[IMG], indexes : range, *args, **kwargs) -> None:
        for i in indexes:
            ImageDraw.Draw(imgs[i].image, 'RGBA').text(*args, **kwargs)

    # write multiline text on images
    def multiline_text(self : PartyBuilder, imgs : list[IMG], indexes : range, *args, **kwargs) -> None:
        for i in indexes:
            ImageDraw.Draw(imgs[i].image, 'RGBA').multiline_text(*args, **kwargs)

    # search in the gbf.wiki cargo table to match a summon name to its id
    async def get_support_summon_from_wiki(self : PartyBuilder, name : str) -> str|None: 
        try:
            name = name.lower()
            if name in self.sumcache: return self.sumcache[name]
            response : aiohttp.Response = await self.client.get("https://gbf.wiki/index.php?title=Special:CargoExport&tables=summons&fields=id,name&format=json&limit=20000", headers={'connection':'close', 'User-Agent':self.USER_AGENT})
            async with response:
                if response.status != 200: raise Exception()
                data : list = await response.json()
                for summon in data:
                    if summon["name"].lower() == name:
                        self.sumcache[name] = summon["id"]
                        return summon["id"]
            return None
        except:
            return None
    
    # get character portraits based on uncap levels
    def get_uncap_id(self : PartyBuilder, cs : int) -> str:
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    # get character uncap star based on uncap levels
    def get_uncap_star(self : PartyBuilder, cs : int, cl : int) -> str:
        match cs:
            case 4: return "assets/star_1.png"
            case 5: return "assets/star_2.png"
            case 6:
                if cl <= 110: return "assets/star_4_1.png"
                elif cl <= 120: return "assets/star_4_2.png"
                elif cl <= 130: return "assets/star_4_3.png"
                elif cl <= 140: return "assets/star_4_4.png"
                elif cl <= 150: return "assets/star_4_5.png"
            case _: return "assets/star_0.png"

     # get summon star based on uncap levels
    def get_summon_star(self : PartyBuilder, se : int, sl : int) -> str:
        match se:
            case 3: return "assets/star_1.png"
            case 4: return "assets/star_2.png"
            case 5: return "assets/star_3.png"
            case 6:
                if sl <= 210: return "assets/star_4_1.png"
                elif sl <= 220: return "assets/star_4_2.png"
                elif sl <= 230: return "assets/star_4_3.png"
                elif sl <= 240: return "assets/star_4_4.png"
                elif sl <= 250: return "assets/star_4_5.png"
            case _: return "assets/star_0.png"

    # get portrait of character for given skin
    def get_character_look(self : PartyBuilder, export : dict, i : int) -> str:
        style = ("" if str(export['cst'][i]) == '1' else "_st{}".format(export['cst'][i])) # style check
        # get uncap
        if style != "":
            uncap = "01"
        else:
            uncap = self.get_uncap_id(export['cs'][i])
        cid = export['c'][i]
        # Beginning of the part to fix some exceptions
        if str(cid).startswith('371'):
            match cid:
                case 3710098000: # seox skin
                    if export['cl'][i] > 80:
                        cid = 3040035000 # eternal seox
                    else:
                        cid = 3040262000 # event seox
                case 3710122000: # seofon skin
                    cid = 3040036000 # eternal seofon
                case 3710143000: # vikala skin
                    if export['ce'][i] == 3:
                        cid = 3040408000 # apply earth vikala
                    elif export['ce'][i] == 6:
                        if export['cl'][i] > 50:
                            cid = 3040252000 # SSR dark vikala
                        else:
                            cid = 3020073000 # R dark vikala
                case 3710154000: # clarisse skin
                    match export['ce'][i]:
                        case 2: cid = 3040413000 # water
                        case 3: cid = 3040067000 # earth
                        case 5: cid = 3040121000 # light
                        case 6: cid = 3040206000 # dark
                        case _: cid = 3040046000 # fire
                case 3710165000: # diantha skin
                    match export['ce'][i]:
                        case 2:
                            if export['cl'][i] > 70:
                                cid = 3040129000 # water SSR
                            else:
                                cid = 3030150000 # water SR
                        case 3:
                            cid = 3040296000 # earth
                case 3710172000: # tsubasa skin
                    cid = 3040180000
                case 3710176000: # mimlemel skin
                    if export['ce'][i] == 1:
                        cid = 3040292000 # apply fire mimlemel
                    elif export['ce'][i] == 3:
                        cid = 3030220000 # apply earth halloween mimlemel
                    elif export['ce'][i] == 4:
                        if export['cn'][i] in ('Mimlemel', 'ミムルメモル'):
                            cid = 3030043000 # first sr wind mimlemel
                        else:
                            cid = 3030166000 # second sr wind mimlemel
                case 3710191000: # cidala skin 1
                    if export['ce'][i] == 3:
                        cid = 3040377000 # apply earth cidala
                    elif export['ce'][i] == 5:
                        cid = 3040512000 # apply dark cidala
                case 3710195000: # cidala skin 2
                    if export['ce'][i] == 3:
                        cid = 3040377000 # apply earth cidala
                    elif export['ce'][i] == 5:
                        cid = 3040512000 # apply dark cidala
        # End of the exceptions
        
        # Return string
        if cid in self.NULL_CHARACTER: 
            if export['ce'][i] == 99:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['pce'])
            else:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['ce'][i])
        else:
            return "{}_{}{}".format(cid, uncap, style)

    # get MC portrait without skin
    async def get_mc_job_look(self : PartyBuilder, skin : str, job : int) -> str:
        sjob : str = str((job//100) * 100 + 1)
        if sjob in self.classes:
            return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:]))
        else:
            tasks = []
            # look for job MH
            for mh in ["sw", "kn", "sp", "ax", "wa", "gu", "me", "bw", "mc", "kr"]:
                tasks.append(self.get_mc_job_look_sub(sjob, mh))
            for r in await asyncio.gather(*tasks):
                if r is not None:
                    self.class_modified = True
                    self.classes[sjob] = r
                    return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:])) 
        return ""

    # subroutine of get_mc_job_look
    async def get_mc_job_look_sub(self : PartyBuilder, job : str, mh : str) -> str|None:
        response : aiohttp.Response = await self.client.head("https://prd-game-a5-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/s/{}_{}_0_01.jpg".format(job, mh))
        async with response:
            if response.status != 200:
                return None
            return mh

    def process_special_weapon(self : PartyBuilder, export : dict, i : int, j : int) -> bool:
        if export['wsn'][i][j] is not None and export['wsn'][i][j] == "skill_job_weapon":
            if j == 2: # skill 3, ultima, opus
                if export['w'][i] in self.DARK_OPUS_IDS:
                    bar_gain = 0
                    hp_cut = 0
                    turn_dmg = 0
                    prog = 0
                    ca_dmg = 0
                    ca_dmg_cap = 0
                    auto_amp_sp = 0
                    skill_amp_sp = 0
                    ca_amp_sp = 0
                    for m in export['mods']:
                        try:
                            match m['icon_img']:
                                case '04_icon_ca_gage.png':
                                    bar_gain = float(m['value'].replace('%', ''))
                                case '03_icon_hp_cut.png':
                                    hp_cut = float(m['value'].replace('%', ''))
                                case '03_icon_turn_dmg.png':
                                    turn_dmg = float(m['value'].replace('%', ''))
                                case '01_icon_e_atk_01.png':
                                    prog = float(m['value'].replace('%', ''))
                                case '04_icon_ca_dmg.png':
                                    ca_dmg = float(m['value'].replace('%', ''))
                                case '04_icon_ca_dmg_cap.png':
                                    ca_dmg_cap = float(m['value'].replace('%', ''))
                                case '04_icon_normal_dmg_amp_other.png':
                                    auto_amp_sp = float(m['value'].replace('%', ''))
                                case '04_icon_ability_dmg_amplify_other.png':
                                    skill_amp_sp = float(m['value'].replace('%', ''))
                                case '04_icon_ca_dmg_amplify_other.png':
                                    ca_amp_sp = float(m['value'].replace('%', ''))
                        except:
                            pass
                    if hp_cut >= 30: # temptation
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14014.jpg"
                        return True
                    elif auto_amp_sp >= 10: # extremity
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14005.jpg"
                        return True
                    elif skill_amp_sp >= 10: # sagacity
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14006.jpg"
                        return True
                    elif ca_amp_sp >= 10: # supremacy
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14007.jpg"
                        return True
                    elif bar_gain <= -50 and bar_gain > -200: # falsehood
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14017.jpg"
                        return True
                    elif prog > 0: # progression
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14004.jpg"
                        return True
                    elif ca_dmg >= 100 and ca_dmg_cap >= 30: # forbiddance
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14015.jpg"
                        return True
                    elif turn_dmg >= 5: # depravity
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14016.jpg"
                        return True
                elif export['w'][i] in self.ULTIMA_IDS:
                    seraphic = 0
                    heal_cap = 0
                    bar_gain = 0
                    cap_up = 0
                    for m in export['mods']:
                        try:
                            match m['icon_img']:
                                case '04_icon_elem_amplify.png':
                                    seraphic = float(m['value'].replace('%', ''))
                                case '04_icon_dmg_cap.png':
                                    cap_up = float(m['value'].replace('%', ''))
                                case '04_icon_ca_gage.png':
                                    bar_gain = float(m['value'].replace('%', ''))
                                case '03_icon_heal_cap.png':
                                    heal_cap = float(m['value'].replace('%', ''))
                        except:
                            pass
                    if seraphic >= 25: # tria
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17003.jpg"
                        return True
                    elif heal_cap >= 50 and bar_gain >= 10: # dio / tessera better guess (EXPERIMENTAL)
                        count = 0
                        for a in export['wsn']:
                            for b in a:
                                if b is None: continue
                                elif "heal_limit_m" in b: count += 1
                                elif "heal_limit" in b: count += 1
                        if count >= 3: export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17004.jpg"
                        elif count == 2: return False # unsure
                        else: export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17002.jpg"
                        return True
                    elif heal_cap >= 50: # dio
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17002.jpg"
                        return True
                    elif bar_gain >= 10: # tessera
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17004.jpg"
                        return True
                    elif cap_up >= 10: # ena
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17001.jpg"
                        return True
            elif j == 1: # skill 2, hexa draconic
                if export['w'][i] in self.ORIGIN_DRACONIC_IDS:
                    seraphic = 0
                    for m in export['mods']:
                        try:
                            match m['icon_img']:
                                case '04_icon_plain_amplify.png':
                                    seraphic = float(m['value'].replace('%', ''))
                        except:
                            pass
                    if seraphic >= 10: # oblivion teluma
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/15009.jpg"
                        return True
        return False

    def blank_image(self : PartyBuilder, size : tuple = (1800, 2160)) -> IMG:
        i = Image.new('RGB', size, "black")
        im_a = Image.new("L", size, "black")
        i.putalpha(im_a)
        im_a.close()
        return IMG(i)

    async def make_party(self : PartyBuilder, export : dict) -> str|tuple[str, list[IMG]]:
        try:
            imgs : list[IMG] = [self.blank_image(), self.blank_image()]
            print("[CHA] * Drawing Party...")
            # setting offsets and background
            if self.babyl:
                offset : v2 = v2(15, 10) # offset of party section
                nchara : int = 12 # max character (12 for babyl because MC is counted)
                csize : v2 = v2(180, 180) # character portrait size
                skill_width : int = 420 # skill name width
                pos : v2 = offset + v2(30, 0) # first character (MC) position
                jsize : v2 = v2(54, 45) # job icon size
                roffset : v2 = v2(-6, -6) # ring offset
                rsize : v2 = v2(60, 60) # ring icon size
                ssize : v2 = v2(50, 50) # star icon size
                soffset : v2 = csize + v2(- csize.y, - ssize.y * 5 // 3) # star offset
                poffset : v2 = csize + v2(-105, -45) # plus mark offset
                ssoffset : v2 = pos + v2(0, 10 + csize.y) # subskill offset
                stoffset : v2 = ssoffset + v2(3, 3) # subskill text offset
                plsoffset : v2 = ssoffset + v2(447, 0) # shield/manatura offset
                # background
                await self.paste(imgs, range(1), "assets/bg.png", (pos + (-15, -15)).i, resize=(csize*(8,2)+(40,55)).i, transparency=True)
            else:
                offset : v2 = v2(15, 10)
                nchara : int = 5
                csize : v2 = v2(250, 250)
                skill_width : int = 420
                pos : v2 = offset + (skill_width - csize.x, 0)
                jsize : v2 = v2(72, 60)
                roffset : v2 = v2(-10, -10)
                rsize : v2 = v2(90, 90)
                ssize : v2 = v2(66, 66)
                soffset : v2 = csize + (- csize.x + ssize.x //2, - ssize.y)
                poffset : v2 = csize + (-110, -40)
                noffset : v2 = v2(9, csize.y + 10)
                loffset : v2 = v2(10, csize.y + 6 + 60)
                ssoffset : v2 = offset + (0, csize.y)
                stoffset : v2 = ssoffset + (3, 3)
                plsoffset : v2 = ssoffset + (0, -150)
                # background
                await self.paste(imgs, range(1), "assets/bg.png", (pos + (-15, -10)).i, resize=(csize*(6,1)+(30+25,175)).i, transparency=True)
            # mc
            print("[CHA] |--> MC Skin:", export['pcjs'])
            print("[CHA] |--> MC Job:", export['p'])
            print("[CHA] |--> MC Master Level:", export['cml'])
            print("[CHA] |--> MC Proof Level:", export['cbl'])
            # class
            class_id = await self.get_mc_job_look(export['pcjs'], export['p'])
            await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/leader/s/{}.jpg".format(class_id), pos.i, resize=csize.i)
            # job icon
            await self.pasteDL(imgs, range(1), "assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos.i, resize=jsize.i, transparency=True)
            if export['cbl'] == '6':
                await self.pasteDL(imgs, range(1), "assets_en/img/sp/ui/icon/job/ico_perfection.png", (pos + (0, jsize[1])).i, resize=jsize.i, transparency=True)
            # skin
            if class_id != export['pcjs']:
                await self.pasteDL(imgs, range(1, 2), "assets_en/img/sp/assets/leader/s/{}.jpg".format(export['pcjs']), pos.i, resize=csize.i)
                await self.pasteDL(imgs, range(1, 2), "assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos.i, resize=jsize, transparency=True)
            # allies
            for i in range(0, nchara):
                await asyncio.sleep(0)
                if self.babyl:
                    if i < 4:
                        pos = offset + (csize.x * i + 30, 0)
                    elif i < 8:
                        pos = offset + (csize.x * i + 40, 0)
                    else:
                        pos = offset + (csize.x * (i - 4) + 40, 10 + csize.y * (i // 8))
                    if i == 0:
                        continue # quirk of babyl party, mc is at index 0
                else:
                    pos = offset + (skill_width + csize.x * i, 0)
                    if i >= 3:
                        pos = pos + (25, 0)
                # portrait
                if i >= len(export['c']) or export['c'][i] is None: # empty
                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/tower/assets/npc/s/3999999999.jpg", pos.i, resize=csize.i)
                    continue
                print("[CHA] |--> Ally #{}:".format(i+1), export['c'][i], export['cn'][i], "Lv {}".format(export['cl'][i]), "Uncap-{}".format(export['cs'][i]), "+{}".format(export['cp'][i]), "Has Ring" if export['cwr'][i] else "No Ring")
                # portrait
                cid = self.get_character_look(export, i)
                await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/npc/s/{}.jpg".format(cid), pos.i, resize=csize.i)
                # skin
                has_skin : bool
                if cid != export['ci'][i]:
                    await self.pasteDL(imgs, range(1, 2), "assets_en/img/sp/assets/npc/s/{}.jpg".format(export['ci'][i]), pos.i, resize=csize.i)
                    has_skin = True
                else:
                    has_skin = False
                # star
                await self.paste(imgs, range(2 if has_skin else 1), self.get_uncap_star(export['cs'][i], export['cl'][i]), (pos + soffset).i, resize=ssize.i, transparency=True)
                # rings
                if export['cwr'][i] == True:
                    await self.pasteDL(imgs, range(2 if has_skin else 1), "assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (pos + roffset).i, resize=rsize.i, transparency=True)
                # plus
                if export['cp'][i] > 0:
                    self.text(imgs, range(2 if has_skin else 1), (pos + poffset).i, "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0))
                if not self.babyl:
                    # name
                    await self.paste(imgs, range(1), "assets/chara_stat.png", (pos + (0, csize.y)).i, resize=(csize.x, 60), transparency=True)
                    if len(export['cn'][i]) > 11: name = export['cn'][i][:11] + ".."
                    else: name = export['cn'][i]
                    self.text(imgs, range(1), (pos + noffset).i, name, fill=(255, 255, 255), font=self.fonts['mini'])
                    # skill count
                    await self.paste(imgs, range(1), "assets/skill_count_EN.png", (pos + (0, csize.y + 60)).i, resize=(csize.x, 60), transparency=True)
                    self.text(imgs, range(1), (pos + loffset + (150, 0)).i, str(export['cb'][i+1]), fill=(255, 255, 255), font=self.fonts['medium'], stroke_width=4, stroke_fill=(0, 0, 0))
            await asyncio.sleep(0)
            # mc sub skills
            await self.paste(imgs, range(2), "assets/subskills.png", ssoffset.i, resize=(420, 147))
            count : int = 0
            f : str
            voff : int
            for i in range(len(export['ps'])):
                if export['ps'][i] is not None:
                    print("[CHA] |--> MC Skill #{}:".format(i), export['ps'][i])
                    if len(export['ps'][i]) > 20:
                        f = 'mini'
                        voff = 5
                    elif len(export['ps'][i]) > 15:
                        f = 'small'
                        voff = 2
                    else:
                        f = 'medium'
                        voff = 0
                    self.text(imgs, range(2), (stoffset + (0, 48*count+voff)).i, export['ps'][i], fill=(255, 255, 255), font=self.fonts[f])
                    count += 1
            await asyncio.sleep(0)
            # paladin shield/manadiver familiar
            if export['cpl'][0] is not None:
                print("[CHA] |--> Paladin shields:", export['cpl'][0], "|", export['cpl'][1])
                await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/shield/s/{}.jpg".format(export['cpl'][0]), plsoffset.i, resize=(150, 150))
                if export['cpl'][1] is not None and export['cpl'][1] != export['cpl'][0] and export['cpl'][1] > 0: # skin
                    await self.pasteDL(imgs, range(1, 2), "assets_en/img/sp/assets/shield/s/{}.jpg".format(export['cpl'][1]), plsoffset.i, resize=(150, 150))
                    await self.paste(imgs, range(1, 2), "assets/skin.png", (plsoffset + (0, -70)).i, (153, 171))
            elif export['fpl'][0] is not None:
                print("[CHA] |--> Manadiver Manatura:", export['fpl'][0], "|", export['fpl'][1])
                await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/familiar/s/{}.jpg".format(export['fpl'][0]), plsoffset.i, resize=(150, 150))
                if export['fpl'][1] is not None and export['fpl'][1] != export['fpl'][0] and export['fpl'][1] > 0: # skin
                    await self.pasteDL(imgs, range(1, 2), "assets_en/img/sp/assets/familiar/s/{}.jpg".format(export['fpl'][1]), plsoffset.i, resize=(150, 150))
                    await self.paste(imgs, range(1, 2), "assets/skin.png", (plsoffset + (0, -45)).i, resize=(76, 85))
            elif self.babyl: # to fill the blank space
                await self.paste(imgs, range(2), "assets/characters_EN.png", (ssoffset, (skill_width, 0)).i, resize=(276, 75), transparency=True)
            return ('party', imgs)
        except Exception as e:
            return self.pexc(e)

    async def make_summon(self : PartyBuilder, export : dict) -> str|tuple:
        try:
            imgs : list[IMG] = [self.blank_image(), self.blank_image()]
            print("[SUM] * Drawing Summons...")
            offset : v2 = v2(170, 425) # offset of this section
            variants : list[dict] = [
                {
                    "size":v2(271, 472),
                    "empty":"assets_en/img/sp/assets/summon/ls/2999999999.jpg",
                    "summon":"assets_en/img/sp/assets/summon/party_main/{}.jpg"
                },
                {
                    "size":v2(266, 200),
                    "empty":"assets_en/img/sp/assets/summon/m/2999999999.jpg",
                    "summon":"assets_en/img/sp/assets/summon/party_sub/{}.jpg"
                },
                {
                    "size":v2(273, 155),
                    "empty":"assets_en/img/sp/assets/summon/m/2999999999.jpg",
                    "summon":"assets_en/img/sp/assets/summon/m/{}.jpg"
                }
            ]
            # background setup
            await self.paste(imgs, range(1), "assets/bg.png", (offset + (-15, -15)).i, resize=(100 + (variants[0]["size"].x + variants[1]["size"].x) * 2+ 48, variants[0]["size"].y + 143), transparency=True)
            pos : v2
            idx : int
            for i in range(0, 7):
                await asyncio.sleep(0)
                if i == 0: # main summon
                    pos = offset + (0, 0)
                    idx = 0
                elif i < 5: # secondary summons
                    pos = offset + (variants[0]["size"].x + 50 + 18, 0)
                    pos += (((i - 1) % 2) * variants[1]["size"].x, 266 * ((i - 1) // 2)) # modulo% to set on a 2x2 grid
                    idx = 1
                else: # sub summons
                    pos = offset + (variants[0]["size"].x + 100 + 18, 102)
                    pos += (2*variants[1]["size"].x, (i - 5) * (variants[2]["size"].y + 60)) # sub summon pos
                    idx = 2
                    if i == 5: # add sub summon marker
                        await self.paste(imgs, range(1), "assets/subsummon_EN.png", (pos.x + 45, pos.y - 72 - 30), resize=(180, 72), transparency=True)
                # portraits
                if export['s'][i] is None:
                    await self.pasteDL(imgs, range(1), variants[idx]["empty"], pos.i, resize=variants[idx]["size"].i)
                    continue
                else:
                    print("[SUM] |--> Summon #{}:".format(i+1), export['ss'][i], "Uncap Lv{}".format(export['se'][i]), "Lv{}".format(export['sl'][i]))
                    await self.pasteDL(imgs, range(1), variants[idx]["summon"].format(export['ss'][i]), pos.i, resize=variants[idx]["size"].i)
                # main summon skin
                has_skin : bool
                if i == 0 and export['ssm'] is not None:
                    await self.pasteDL(imgs, range(1, 2), variants[idx]["summon"].format(export['ssm']), pos.i, resize=variants[idx]["size"].i)
                    await self.paste(imgs, range(1, 2), "assets/skin.png", (pos + (variants[idx]["size"].x - 85, 15)).i, resize=(76, 85))
                    has_skin = True
                else:
                    has_skin = False
                # star
                await self.paste(imgs, range(2 if has_skin else 1), self.get_summon_star(export['se'][i], export['sl'][i]), pos.i, resize=(66, 66), transparency=True)
                # quick summon
                if export['qs'] is not None and export['qs'] == i:
                    await self.paste(imgs, range(2 if has_skin else 1), "assets/quick.png", (pos + (0, 66)).i, resize=(66, 66), transparency=True)
                # level
                await self.paste(imgs, range(1), "assets/chara_stat.png", (pos + (0, variants[idx]["size"].y)).i, resize=(variants[idx]["size"].x, 60), transparency=True)
                self.text(imgs, range(1), (pos + (6 , variants[idx]["size"].y + 9)).i, "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.fonts['small'])
                # plus
                if export['sp'][i] > 0:
                    self.text(imgs, range(2 if has_skin else 1), (pos + variants[idx]["size"] + (-95, -50)), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
            await asyncio.sleep(0)
            # stats
            spos = offset + variants[0]["size"] + (50+18, 60) # position
            await self.paste(imgs, range(1), "assets/chara_stat.png",  spos.i, resize=(variants[1]["size"].x * 2, 60), transparency=True)
            await self.paste(imgs, range(1), "assets/atk.png", (spos + (9, 9)).i, resize=(90, 39), transparency=True)
            await self.paste(imgs, range(1), "assets/hp.png", (spos + (variants[1]["size"].x + 9, 9)).i, resize=(66, 39), transparency=True)
            self.text(imgs, range(1), (spos + (120, 9)).i, "{}".format(export['satk']), fill=(255, 255, 255), font=self.fonts['small'])
            self.text(imgs, range(1), (spos + (variants[1]["size"].x + 80, 9)).i, "{}".format(export['shp']), fill=(255, 255, 255), font=self.fonts['small'])
            return ('summon', imgs)
        except Exception as e:
            return self.pexc(e)

    async def make_weapon(self : PartyBuilder, export : dict, do_hp : bool, do_opus : bool) -> str|tuple:
        try:
            imgs = [self.blank_image(), self.blank_image()]
            print("[WPN] * Drawing Weapons...")
            # setting offsets
            offset : v2
            if self.sandbox:
                offset = v2(25, 1050)
            else:
                offset = v2(170, 1050)
            skill_box_height : int = 144
            skill_icon_size : int = 72
            ax_icon_size : int = 86
            ax_separator : int = skill_box_height
            mh_size : v2 = v2(300, 630)
            sub_size : v2 = v2(288, 165)
            self.multiline_text(imgs, range(2), (1540, 2125), self.name, fill=(120, 120, 120, 255), font=self.fonts['mini'])
            await self.paste(imgs, range(1), "assets/grid_bg.png", (offset + (-15, -15)).i, resize=(mh_size.x+(4 if self.sandbox else 3)*sub_size.x+60, 1425+(240 if self.sandbox else 0)), transparency=True)
            if self.sandbox:
                await self.paste(imgs, range(1), "assets/grid_bg_extra.png", (offset.x+mh_size.x+30+sub_size.x*3, offset.y), resize=(288, 1145), transparency=True)

            for i in range(0, len(export['w'])):
                await asyncio.sleep(0)
                wt : str = "ls" if i == 0 else "m"
                pos : v2
                size : v2
                bsize : v2
                if i == 0: # mainhand
                    pos = offset
                    size = mh_size
                    bsize = size
                elif i >= 10: # sandbox
                    if not self.sandbox: break
                    size = sub_size
                    pos = offset + (bsize.x + 30, 0) + (size + (0, skill_box_height)) * (3, (i - 1) % 3)
                else: # others
                    size = sub_size
                    pos = offset + (bsize.x + 30, 0) + (size + (0, skill_box_height)) * ((i - 1) % 3, (i - 1) // 3)
                # dual blade class
                if i <= 1 and export['p'] in self.AUXILIARY_CLS:
                    await self.paste(imgs, range(1), ("assets/mh_dual.png" if i == 0 else "assets/aux_dual.png"), (pos, (-2, -2)).i, resize=(size, (5, 5+skill_box_height)).i, transparency=True)
                # portrait
                if export['w'][i] is None or export['wl'][i] is None:
                    if i >= 10:
                        await self.paste(imgs, range(1), "assets/arca_slot.png", pos.i, resize=size.i)
                    else:
                        await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt), pos.i, resize=size.i)
                    continue
                # ax and awakening check
                has_ax : bool = len(export['waxt'][i]) > 0
                has_awakening : bool = (export['wakn'][i] is not None and export['wakn'][i]['is_arousal_weapon'] and export['wakn'][i]['level'] is not None and export['wakn'][i]['level'] > 1)
                pos_shift : int = - skill_icon_size if (has_ax and has_awakening) else 0  # vertical shift of the skill boxes (if both ax and awk are presents)
                # portrait draw
                print("[WPN] |--> Weapon #{}".format(i+1), str(export['w'][i]), ", AX:", has_ax, ", Awakening:", has_awakening)
                await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/weapon/{}/{}.jpg".format(wt, export['w'][i]), pos.i, resize=size.i)
                # skin
                has_skin : bool = False
                if i <= 1 and export['wsm'][i] is not None:
                    if i == 0 or (i == 1 and export['p'] in self.AUXILIARY_CLS): # aux class check for 2nd weapon
                        await self.pasteDL(imgs, range(1, 2), "assets_en/img/sp/assets/weapon/{}/{}.jpg".format(wt, export['wsm'][i]), pos.i, resize=size.i)
                        await self.paste(imgs, range(1, 2), "assets/skin.png", (pos + (size.x-76, 0)).i, resize=(76, 85), transparency=True)
                        has_skin = True
                # skill box
                nbox : int = 1 # number of skill boxes to draw
                if has_ax:
                    nbox += 1
                if has_awakening:
                    nbox += 1
                for j in range(nbox):
                    if i != 0 and j == 0 and nbox == 3: # if 3 boxes and we aren't on the mainhand, we draw half of one for the first box
                        await self.paste(imgs, range(2 if (has_skin and j == 0) else 1), "assets/skill.png", (pos.x+size.x//2, pos.y+size.y+pos_shift+skill_icon_size*j), resize=(size.x//2, skill_icon_size), transparency=True)
                    else:
                        await self.paste(imgs, range(2 if (has_skin and j == 0) else 1), "assets/skill.png", (pos.x, pos.y+size.y+pos_shift+skill_icon_size*j), resize=(size.x, skill_icon_size), transparency=True)
                # plus
                if export['wp'][i] > 0:
                    # calculate shift of the position if AX and awakening are present
                    shift : v2
                    if pos_shift != 0:
                        if i > 0:
                            shift = v2(- size.x // 2, 0)
                        else:
                            shift = v2(0, pos_shift)
                    else:
                        shift = v2(0, 0)
                    # draw plus text
                    self.text(imgs, range(2 if has_skin else 1), (pos.x + size.x - 105 + shift.x, pos.y + size.y - 60 + shift.y), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
                # skill level
                if export['wl'][i] is not None and export['wl'][i] > 1:
                    self.text(imgs, range(2 if has_skin else 1), (pos.x + skill_icon_size * 3 - 51, pos.y + size.y + pos_shift + 15), "SL {}".format(export['wl'][i]), fill=(255, 255, 255), font=self.fonts['small'])
                if i == 0 or not has_ax or not has_awakening: # don't draw if ax and awakening and not mainhand
                    # skill icon
                    for j in range(3):
                        if export['wsn'][i][j] is not None:
                            if do_opus and self.process_special_weapon(export, i, j): # 3rd skill guessing
                                await self.pasteDL(imgs, range(2 if has_skin else 1), export['wsn'][i][j], (pos.x + skill_icon_size * j, pos.y + size.y + pos_shift), resize=(skill_icon_size, skill_icon_size))
                            else:
                                await self.pasteDL(imgs, range(2 if has_skin else 1), "assets_en/img/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (pos.x + skill_icon_size * j, pos.y + size.y + pos_shift), resize=(skill_icon_size, skill_icon_size))
                pos_shift += skill_icon_size
                main_ax_icon_size : int  = int(ax_icon_size * (1.5 if i == 0 else 1) * (0.75 if (has_ax and has_awakening) else 1)) # size of the big AX/Awakening icon
                # ax skills
                if has_ax:
                    await self.pasteDL(imgs, range(2 if has_skin else 1), "assets_en/img/sp/ui/icon/augment_skill/{}.png".format(export['waxt'][i][0]), pos.i, resize=(main_ax_icon_size, main_ax_icon_size))
                    for j in range(len(export['waxi'][i])):
                        await self.pasteDL(imgs, range(1), "assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]), (pos.x + ax_separator * j, pos.y + size.y + pos_shift), resize=(skill_icon_size, skill_icon_size))
                        self.text(imgs, range(1), (pos + (ax_separator*j+skill_icon_size+6, size.y+pos_shift+15)).i, "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''), fill=(255, 255, 255), font=self.fonts['small'])
                    pos_shift += skill_icon_size
                # awakening
                if has_awakening:
                    shift = main_ax_icon_size//2 if has_ax else 0 # shift the icon right a bit if also has AX icon
                    await self.pasteDL(imgs, range(2 if has_skin else 1), "assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']), (pos + (shift, 0)).i, resize=(main_ax_icon_size, main_ax_icon_size))
                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']), (pos.x+skill_icon_size, pos.y+size.y+pos_shift), resize=(skill_icon_size, skill_icon_size))
                    self.text(imgs, range(1), (pos + (skill_icon_size*3-51, +size.y+pos_shift+15)).i, "LV {}".format(export['wakn'][i]['level']), fill=(255, 255, 255), font=self.fonts['small'])

            if self.sandbox:
                await self.paste(imgs, range(1), "assets/sandbox.png", (pos.x, offset.y+(skill_box_height+sub_size.y)*3), resize=(size.x, int(66*size.x/159)), transparency=True)
            # stats
            pos = v2(offset.x, offset.y+bsize.y+150)
            await self.paste(imgs, range(1), "assets/skill.png", pos.i, resize=(bsize.x, 75), transparency=True)
            await self.paste(imgs, range(1), "assets/skill.png", (pos + (0, 75)).i, resize=(bsize.x, 75), transparency=True)
            await self.paste(imgs, range(1), "assets/atk.png", (pos + (9, 15)).i, resize=(90, 39), transparency=True)
            await self.paste(imgs, range(1), "assets/hp.png", (pos + (9, 15+75)).i, resize=(66, 39), transparency=True)
            self.text(imgs, range(1), (pos + (111, 15)).i, "{}".format(export['watk']), fill=(255, 255, 255), font=self.fonts['medium'])
            self.text(imgs, range(1), (pos + (111, 15+75)).i, "{}".format(export['whp']), fill=(255, 255, 255), font=self.fonts['medium'])
            await asyncio.sleep(0)

            # estimated damage
            pos = pos + (bsize.x+15, 165)
            if (export['sps'] is not None and export['sps'] != '') or export['spsid'] is not None:
                await asyncio.sleep(0)
                # support summon
                if export['spsid'] is not None:
                    supp = export['spsid']
                else:
                    print("[WPN] |--> Looking up summon ID of", export['sps'], "on the wiki")
                    supp = await self.get_support_summon_from_wiki(export['sps'])
                if supp is None:
                    print("[WPN] |--> Support summon is", export['sps'], "(Note: searching its ID on gbf.wiki failed)")
                    await self.paste(imgs, range(1), "assets/big_stat.png", (pos + (-bsize.x-15, 9*2-15)).i, resize=(bsize.x, 150), transparency=True)
                    self.text(imgs, range(1), (pos + (-bsize.x, 9*2)).i, ("サポーター" if self.japanese else "Support"), fill=(255, 255, 255), font=self.fonts['medium'])
                    supp = ""
                    if len(export['sps']) > 10:
                        supp = export['sps'][:10] + "..."
                    else:
                        supp = export['sps']
                    self.text(imgs, range(1), (pos + (-bsize.x, 9*2+60)).i, supp, fill=(255, 255, 255), font=self.fonts['medium'])
                else:
                    print("[WPN] |--> Support summon ID is", supp)
                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/summon/m/{}.jpg".format(supp), (pos.x-bsize.x-15+9, pos.y), resize=(261, 150))
            # weapon grid stats
            est_width : int = ((size.x*3)//2)
            for i in range(0, 2):
                await asyncio.sleep(0)
                await self.paste(imgs, range(1), "assets/big_stat.png", (pos + (est_width*i, 0)).i, resize=(est_width-15, 150), transparency=True)
                self.text(imgs, range(1), (pos + (9+est_width*i, 9)).i, "{}".format(export['est'][i+1]), fill=self.COLORS[int(export['est'][0])], font=self.fonts['big'], stroke_width=6, stroke_fill=(0, 0, 0))
                if i == 0:
                    self.text(imgs, range(1), (pos + (est_width*i+15, 90)).i, ("予測ダメ一ジ" if self.japanese else "Estimated"), fill=(255, 255, 255), font=self.fonts['medium'])
                elif i == 1:
                    vs : int
                    if int(export['est'][0]) <= 4:
                        vs = (int(export['est'][0]) + 2) % 4 + 1
                    else:
                        vs = (int(export['est'][0]) - 5 + 1) % 2 + 5
                    if self.japanese:
                        self.text(imgs, range(1), (pos + (est_width * i + 15, 90)).i, "対", fill=(255, 255, 255), font=self.fonts['medium'])
                        self.text(imgs, range(1), (pos + (est_width * i + 54, 90)).i, "{}属性".format(self.COLORS_JP[vs]), fill=self.COLORS[vs], font=self.fonts['medium'])
                        self.text(imgs, range(1), (pos + (est_width * i + 162, 90)).i, "予測ダメ一ジ", fill=(255, 255, 255), font=self.fonts['medium'])
                    else:
                        self.text(imgs, range(1), (pos + (est_width * i + 15, 90)).i, "vs", fill=(255, 255, 255), font=self.fonts['medium'])
                        self.text(imgs, range(1), (pos + (est_width * i + 66, 90)).i, "{}".format(self.COLORS_EN[vs]), fill=self.COLORS[vs], font=self.fonts['medium'])
            # hp gauge
            if do_hp:
                await asyncio.sleep(0)
                hpratio : int = 100
                for et in export['estx']:
                    if et[0].replace('txt-gauge-num ', '') == 'hp':
                        hpratio = et[1]
                        break
                await self.paste(imgs, range(1, 2), "assets/big_stat.png", pos.i, resize=(est_width-15, 150), transparency=True)
                if self.japanese:
                    self.text(imgs, range(1, 2), (pos + (25, 25)).i, "HP{}%".format(hpratio), fill=(255, 255, 255), font=self.fonts['medium'])
                else:
                    self.text(imgs, range(1, 2), (pos + (25, 25)).i, "{}% HP".format(hpratio), fill=(255, 255, 255), font=self.fonts['medium'])
                await self.paste(imgs, range(1, 2), "assets/hp_bottom.png", (pos + (25, 90)).i, resize=(363, 45), transparency=True)
                await self.paste(imgs, range(1, 2), "assets/hp_mid.png", (pos + (25, 90)).i, resize=(int(363*int(hpratio)/100), 45), transparency=True, crop=(int(484*int(hpratio)/100), 23))
                await self.paste(imgs, range(1, 2), "assets/hp_top.png", (pos + (25, 90)).i, resize=(363, 45), transparency=True)
            return ('weapon', imgs)
        except Exception as e:
            return self.pexc(e)

    async def make_modifier(self : PartyBuilder, export : dict) -> str|tuple:
        try:
            imgs : list[IMG] = [self.blank_image()]
            print("[MOD] * Drawing Modifiers...")
            # setting offsets
            offset : v2 = v2(1560, 10) if self.babyl else v2(1560, 410)
            mod_set : list[dict] = [
                {
                    "minimum":32 if self.babyl else 27,
                    "font":'mini',
                    "offset":15,
                    "bg_size":v2(258, 114),
                    "size":v2(80, 40),
                    "img_offset":v2(-10, 0),
                    "text_offset":v2(80, 5),
                    "space":42,
                    "crop":v2(68, 34)
                },
                {
                    "minimum":25 if self.babyl else 20,
                    "font":'mini',
                    "offset":15,
                    "bg_size":v2(185, 114),
                    "size":v2(150, 38),
                    "img_offset":v2(0, 0),
                    "text_offset":v2(0, 35),
                    "space":66,
                    "crop":None
                },
                {
                    "minimum":20 if self.babyl else 16,
                    "font":'small',
                    "offset":27,
                    "bg_size":v2(222, 114),
                    "size":v2(174, 45),
                    "img_offset":v2(0, 0),
                    "text_offset":v2(0, 45),
                    "space":84,
                    "crop":None
                },
                {
                    "minimum":0,
                    "font":'medium',
                    "offset":15,
                    "bg_size":v2(258, 114),
                    "size":v2(241, 60),
                    "img_offset":v2(0, 0),
                    "text_offset":v2(0, 60),
                    "space":105,
                    "crop":None
                }
            ]
            print("[MOD] |--> Found", len(export['mods']), "modifier(s)...")
            
            # weapon modifier list
            if len(export['mods']) > 0:
                mod : dict
                for i in range(len(mod_set)):
                    if len(export['mods']) >= mod_set[i]["minimum"]:
                        mod = mod_set[i]
                        break
                await asyncio.sleep(0)
                # background
                await self.paste(imgs, range(1), "assets/mod_bg.png", (offset.x-mod["offset"], offset.y-mod["offset"]//2), resize=mod["bg_size"].i)
                try:
                    await self.paste(imgs, range(1), "assets/mod_bg_supp.png", (offset.x-mod["offset"], offset.y-mod["offset"]+mod["bg_size"].y), resize=(mod["bg_size"].x, mod["space"] * (len(export['mods'])-1)))
                    await self.paste(imgs, range(1), "assets/mod_bg_bot.png", (offset.x-mod["offset"], offset.y+mod["space"]*(len(export['mods'])-1)), resize=mod["bg_size"].i)
                except:
                    await self.paste(imgs, range(1), "assets/mod_bg_bot.png", (offset.x-mod["offset"], offset.y+50), resize=mod["bg_size"].i)
                offset = offset
                # modifier draw
                for m in export['mods']:
                    await asyncio.sleep(0)
                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/ui/icon/weapon_skill_label/" + m['icon_img'], (offset + mod["img_offset"]).i, resize=mod["size"].i, transparency=True, crop=mod["crop"])
                    self.text(imgs, range(1), (offset + mod["text_offset"]).i, str(m['value']), fill=((255, 168, 38, 255) if m['is_max'] else (255, 255, 255, 255)), font=self.fonts[mod["font"]])
                    offset += (0, mod["space"])
            return ('modifier', imgs)
        except Exception as e:
            return self.pexc(e)

    async def loadEMP(self : PartyBuilder, id : str) -> dict|None:
        try:
            if id in self.emp_cache:
                return self.emp_cache[id]
            else:
                with open("emp/{}.json".format(id), mode="r", encoding="utf-8") as f:
                    self.emp_cache[id] = json.load(f)
                    await asyncio.sleep(0)
                    return self.emp_cache[id]
        except:
            return None

    async def make_emp(self : PartyBuilder, export : dict) -> str|tuple:
        try:
            imgs : list[IMG] = [self.blank_image()]
            print("[EMP] * Drawing EMPs...")
            # setting offsets
            offset : v2 = v2(15, 0)
            eoffset : v2 = v2(15, 10)
            ersize : v2 = v2(80, 80)
            roffset : v2 = v2(-10, -10)
            rsize : v2 = v2(90, 90)
            # first, we attempt to load emp files
            # get chara count
            ccount : int = 0
            nchara : int
            if self.babyl:
                nchara = 12 # max number for babyl (mc included)
            else:
                nchara = 5 # max number of allies
            for i in range(0, nchara):
                if self.babyl and i == 0:
                    continue # quirk of babyl party, mc is at index 0
                if i >= len(export['c']) or export['c'][i] is None: # no charater in this spot
                    continue
                cid : str = self.get_character_look(export, i)
                data : dict|None = await self.loadEMP(cid.split('_')[0]) # preload and cache emp
                if data is None:
                    print("[EMP] |--> Ally #{}: {}.json can't be loaded".format(i+1, cid.split('_')[0]))
                    continue
                elif self.japanese != (data['lang'] == 'ja'):
                    print("[EMP] |--> Ally #{}: WARNING, language doesn't match".format(i+1))
                ccount += 1
            # next
            # set positions and offsets we'll need
            compact : int
            portrait_type : str
            csize : v2
            shift : int
            esizes : list[v2]
            eroffset : v2
            if ccount > 5:
                if ccount > 8:
                    compact = 2
                else:
                    compact = 1
                portrait_type = 's'
                csize = v2(196, 196)
                shift = 74 if compact == 1 else 0
                esizes = [v2(104, 104), v2(77, 77)]
                eroffset = v2(100, 25)
            else:
                compact = 0
                portrait_type = 'f'
                csize = v2(207, 432)
                shift = 0
                esizes = [v2(133, 133), v2(100, 100)]
                eroffset = v2(100, 15)
            bg_size : v2 = v2(imgs[0].image.size[0] - csize.x - offset.x, csize.y + shift)
            loffset : v2 = csize + (-150, -50)
            poffset : v2 = csize + (-110, -100)
            pos : v2 = offset + (0, offset.y - csize.y -shift)

            # allies
            for i in range(0, nchara):
                await asyncio.sleep(0)
                if self.babyl and i == 0:
                    continue # quirk of babyl party, mc is at index 0
                if i < len(export['c']) and export['c'][i] is not None:
                    cid : str = self.get_character_look(export, i)
                    data : dict|None = self.emp_cache.get(cid.split('_')[0], None)
                    if data is None:
                        continue
                    pos = pos + (0, csize.y + shift) # set chara position
                    # portrait
                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/npc/{}/{}.jpg".format(portrait_type, cid), pos.i, resize=csize.i)
                    # rings
                    if export['cwr'][i] == True:
                        await self.pasteDL(imgs, range(1), "assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (pos + roffset).i, resize=rsize.i, transparency=True)
                    # level
                    self.text(imgs, range(1), (pos + loffset).i, "Lv{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0))
                    # plus
                    if export['cp'][i] > 0:
                        self.text(imgs, range(1), (pos + poffset).i, "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0))
                    # background
                    await self.paste(imgs, range(1), "assets/bg_emp.png", (pos + (csize.x, 0)).i, resize=bg_size.i, transparency=True)
                    # main EMP
                    nemp = len(data['emp'])
                    extra_lb = ""
                    if 'domain' in data and len(data['domain']) > 0:
                        extra_lb = ", Has Domain"
                    elif 'saint' in data and len(data['saint']) > 0:
                        extra_lb = ", Has Yupei"
                    elif 'extra' in data and len(data['extra']) > 0:
                        extra_lb = ", Has Extra EMP"
                    print("[EMP] |--> Ally #{}: {} EMPs, {} Ring EMPs, {}{}".format(i+1, nemp, len(data['ring']), ('{} Lv{}'.format(data['awaktype'], data['awakening'].split('lv')[-1]) if 'awakening' in data else 'Awakening not found'), extra_lb))
                    idx : int
                    off : int
                    if nemp > 15: # transcended eternal only (for now)
                        idx = 1
                        off = ((esizes[0].x - esizes[1].x) * 5) // 2
                    else:
                        idx = 0
                        off = 0
                    for j, emp in enumerate(data['emp']):
                        await asyncio.sleep(0)
                        if compact:
                            epos : v2 = pos + (csize.x + 15 + esizes[idx].x * j, 5)
                        elif j % 5 == 0: # new line
                            epos : v2 = pos + (csize.x + 15 + off, 7 + esizes[idx].y * j // 5)
                        else:
                            epos : v2 = epos + (esizes[idx].x, 0)
                        if emp.get('is_lock', False):
                            await self.pasteDL(imgs, range(1), "assets_en/img/sp/zenith/assets/ability/lock.png", epos.i, resize=esizes[idx].i)
                        else:
                            await self.pasteDL(imgs, range(1), "assets_en/img/sp/zenith/assets/ability/{}.png".format(emp['image']), epos.i, resize=esizes[idx].i)
                            if str(emp['current_level']) != "0":
                                self.text(imgs, range(1), (epos + eoffset).i, str(emp['current_level']), fill=(235, 227, 250), font=self.fonts['medium'] if compact and nemp > 15 else self.fonts['big'], stroke_width=6, stroke_fill=(0, 0, 0))
                            else:
                                await self.paste(imgs, range(1), "assets/emp_unused.png", epos.i, resize=esizes[idx].i, transparency=True)
                    # ring EMP
                    for j, ring in enumerate(data['ring']):
                        await asyncio.sleep(0)
                        if compact:
                            epos : v2 = pos + (csize.x + 15 + (200 + ersize.x)*j, csize.y - ersize.y - 15)
                        else:
                            epos : v2 = pos + (csize.x + 50 + off * 2 + esizes[idx].x * 5, 15 + ersize.y * j)
                        await self.paste(imgs, range(1), "assets/{}.png".format(ring['type']['image']), epos.i, resize=ersize.i, transparency=True)
                        if compact:
                            self.text(imgs, range(1), (epos + eroffset).i, ring['param']['disp_total_param'], fill=(255, 255, 95), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0))
                        else:
                            self.text(imgs, range(1), (epos + eroffset).i, ring['type']['name'] + " " + ring['param']['disp_total_param'], fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
                    if compact != 2:
                        await asyncio.sleep(0)
                        icon_size : v2 = v2(65, 65)
                        icon_index : int = 1
                        # calc pos
                        apos1 : v2
                        apos2 : v2
                        if compact:
                            apos1 = v2(pos.x + csize.x + 25, pos.y + csize.y)
                            apos2 = v2(pos.x + csize.x + 225, pos.y + csize.y)
                        else:
                            apos1 = v2(imgs[0].image.size[0] - 420, pos.y + 20)
                            apos2 = v2(imgs[0].image.size[0] - 420, pos.y + 85)
                        # awakening
                        if data.get('awakening', None) is not None:
                            match data['awaktype']:
                                case "Attack"|"攻撃":
                                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/item/npcarousal/s/1.jpg", apos1.i, resize=icon_size.i)
                                case "Defense"|"防御":
                                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/item/npcarousal/s/2.jpg", apos1.i, resize=icon_size.i)
                                case "Multiattack"|"連続攻撃":
                                    await self.pasteDL(imgs, range(1), "assets_en/img/sp/assets/item/npcarousal/s/3.jpg", apos1.i, resize=icon_size.i)
                                case _: # "Balanced"|"バランス"or others
                                    await self.paste(imgs, range(1), "assets/bal_awakening.png", apos1.i, resize=icon_size.i, transparency=True)
                            self.text(imgs, range(1), (apos1 + (75, 10)).i, "Lv" + data['awakening'].split('lv')[-1], fill=(198, 170, 240), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
                        # domain and other extra upgrades
                        for key in ['domain', 'saint', 'extra']:
                            if key in data and len(data[key]) > 0:
                                extra_txt : str = ""
                                # set txt, icon and color according to specifics
                                icon_path : str
                                text_color : tuple[int, int, int]
                                match key:
                                    case 'domain':
                                        icon_path = "assets_en/img/sp/ui/icon/ability/m/1426_3.png"
                                        text_color = (100, 210, 255)
                                        lv = 0
                                        for el in data[key]:
                                            if el[2] is not None: lv += 1
                                        extra_txt = "Lv" + str(lv)
                                    case 'extra':
                                        icon_path = "assets_en/img/sp/ui/icon/ability/m/2487_3.png"
                                        text_color = (110, 140, 250)
                                        extra_txt = "Lv" + str(len(data[key]))
                                    case 'saint':
                                        icon_path = "assets_en/img/sp/ui/icon/skill/skill_job_weapon.png"
                                        text_color = (207, 145, 64)
                                        lv = [0, 0]
                                        for el in data[key]:
                                            if el[0].startswith("ico-progress-gauge"):
                                                if el[0].endswith(" on"):
                                                    lv[0] += 1
                                                lv[1] += 1
                                        extra_txt = "{}/{}".format(lv[0], lv[1])
                                    case _:
                                        icon_path = "assets_en/img/sp/ui/icon/skill/skill_job_weapon.png"
                                        text_color = (207, 145, 64)
                                        extra_txt = "Lv" + str(len(data[key]))
                                # add to image
                                await self.pasteDL(imgs, range(1), icon_path, apos2.i, resize=icon_size.i)
                                self.text(imgs, range(1), (apos2 + (75, 10)).i, extra_txt, fill=text_color, font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
                                # increase index and move position accordingly
                                # NOTE: Should be unused for now, it's in case they add multiple in the future
                                icon_index += 1
                                if compact:
                                    apos2 += (200, 0)
                                else:
                                    if icon_index % 2 == 0:
                                        apos2 += (200, - icon_size.y)
                                    else:
                                        apos2 += (0, icon_size.y)
            return ('emp', imgs)
        except Exception as e:
            return self.pexc(e)

    def saveImage(self : PartyBuilder, img : IMG, filename : str, resize : tuple|None = None) -> str|None:
        try:
            if resize is not None:
                img.resize(resize).image.save(filename, "PNG")
            else:
                img.image.save(filename, "PNG")
            print("[OUT] *'{}' has been generated".format(filename))
            return None
        except Exception as e:
            return self.pexc(e)

    def clipboardToJSON(self : PartyBuilder) -> dict:
        return json.loads(pyperclip.paste())

    def clean_memory_caches(self : PartyBuilder) -> None:
        if len(self.cache.keys()) > 100:
            print("* Cleaning File Memory Cache...")
            tmp = {}
            for k, v in self.cache.items():
                if '/skill/' in k or '/zenith/' in k or len(k.split('/')) == 2: # keep important files
                    tmp[k] = v
            self.cache = tmp
        if len(self.emp_cache.keys()) > 100:
            print("* Cleaning EMP Memory Cache...")
            self.emp_cache = {}

    async def generate(self : PartyBuilder, fast : bool = False) -> bool: # main function
        try:
            if not fast:
                print("Instructions:")
                print("1) Go to the party or EMP screen you want to export")
                print("2) Click the bookmarklet")
                print("3) Come back here and press Return to continue")
                input()
            self.running = True
            # get the data from clipboard
            export : dict = self.clipboardToJSON()
            if export.get('ver', 0) < 1:
                print("Your bookmark is outdated, please update it!")
                self.running = False
                return False
            # start
            if 'emp' in export:
                self.generate_emp(export)
            else:
                await self.generate_party(export)
                self.saveClasses()
                if self.gbftmr is not None and self.settings.get('gbftmr_use', False):
                    print("Do you want to make a thumbnail with this party? (Y to confirm)")
                    if input().lower() == "y":
                        try:
                            await self.gbftmr.makeThumbnailManual(export)
                        except Exception as xe:
                            print(self.pexc(xe))
                            print("The above exception occured while trying to generate the thumbnail")
            self.running = False
            return True
        except Exception as e:
            print("An error occured")
            print(e)
            print("Did you follow the instructions?")
            self.running = False
            return False

    def completeBaseImages(self : PartyBuilder, imgs : list, do_skin : bool, resize : tuple|None = None) -> None:
        # party - Merge the images and save the resulting image
        for k in ['summon', 'weapon', 'modifier']:
            imgs['party'][0] = imgs['party'][0].alpha(imgs[k][0])
        self.saveImage(imgs['party'][0], "party.png", resize)
        # skin - Merge the images (if enabled) and save the resulting image
        if do_skin:
            imgs['party'][1] = imgs['party'][0].alpha(imgs['party'][1]) # we don't close imgs['party'][0] in case its save process isn't finished

            for k in ['summon', 'weapon']:
                imgs['party'][1] = imgs['party'][1].alpha(imgs[k][1])
            self.saveImage(imgs['party'][1], "skin.png", resize)

    async def generate_party(self : PartyBuilder, export : dict) -> bool:
        if self.classes is None:
            self.loadClasses()
        self.clean_memory_caches()
        start : float = time.time()
        do_emp = self.settings.get('emp', False)
        do_skin = self.settings.get('skin', True)
        do_hp = self.settings.get('hp', True)
        do_opus = self.settings.get('opus', False)
        if self.settings.get('caching', False):
            self.checkDiskCache()
        self.quality = {'720p':1/3, '1080p':1/2, '4k':1}.get(self.settings.get('quality', '4k').lower(), 1/3)
        self.definition = {'720p':(600, 720), '1080p':(900, 1080), '4k':(1800, 2160)}.get(self.settings.get('quality', '4k').lower(), (600, 720))
        resize = None if self.quality == 1 else self.definition
        print("* Image Quality ratio:", self.quality)
        print("* Image Definition:", self.definition)
        self.japanese = (export['lang'] == 'ja')
        if self.japanese: print("* Japanese detected")
        else: print("* English detected")
        self.babyl = (len(export['c']) > 5)
        if self.babyl: print("* Tower of Babyl Party detectd")
        self.sandbox = (len(export['w']) > 10 and not isinstance(export['est'][0], str))
        if self.sandbox: print("* Extra Party Weapon Grid detected")

        if self.prev_lang != self.japanese:
            print("* Preparing Font...")
            if self.japanese:
                self.fonts['big'] = ImageFont.truetype("assets/font_japanese.ttf", 72, encoding="unic")
                self.fonts['medium'] = ImageFont.truetype("assets/font_japanese.ttf", 36, encoding="unic")
                self.fonts['small'] = ImageFont.truetype("assets/font_japanese.ttf", 33, encoding="unic")
                self.fonts['mini'] = ImageFont.truetype("assets/font_japanese.ttf", 27, encoding="unic")
            else:
                self.fonts['big'] = ImageFont.truetype("assets/font_english.ttf", 90, encoding="unic")
                self.fonts['medium'] = ImageFont.truetype("assets/font_english.ttf", 48, encoding="unic")
                self.fonts['small'] = ImageFont.truetype("assets/font_english.ttf", 42, encoding="unic")
                self.fonts['mini'] = ImageFont.truetype("assets/font_english.ttf", 36, encoding="unic")
        self.prev_lang = self.japanese
        
        tasks = []
        imgs = {}
        async with asyncio.TaskGroup() as tg:
            print("* Starting...")
            if do_emp: # only start if enabled
                tasks.append(tg.create_task(self.make_emp(export)))
            tasks.append(tg.create_task(self.make_party(export)))
            tasks.append(tg.create_task(self.make_summon(export)))
            tasks.append(tg.create_task(self.make_weapon(export, do_hp, do_opus)))
            tasks.append(tg.create_task(self.make_modifier(export)))
        for t in tasks:
            r = t.result()
            if isinstance(r, tuple):
                imgs[r[0]] = r[1]
            else: # exception check
                raise Exception("Exception error and traceback:\n" + r)
            # as soon as available, we start generating the final images
        async with asyncio.TaskGroup() as tg:
            tasks.append(tg.create_task(asyncio.to_thread(self.completeBaseImages, imgs, do_skin, resize)))
            if do_emp:
                tasks.append(tg.create_task(asyncio.to_thread(self.saveImage, imgs['emp'][0], "emp.png", resize)))
        for t in tasks:
            r = t.result()
        for k, v in imgs.items():
            for i in v:
                try: i.close()
                except: pass
        end : float = time.time()
        print("* Task completed with success!")
        print("* Ended in {:.2f} seconds".format(end - start))
        return True

    def generate_emp(self : PartyBuilder, export : dict) -> None:
        if 'emp' not in export or 'id' not in export or 'ring' not in export:
            raise Exception("Invalid EMP data, check your bookmark")
        print("* Saving EMP for Character", export['id'], "...")
        print("*", len(export['emp']), "Extended Masteries")
        print("*", len(export['ring']), "Over Masteries")
        if 'awakening' not in export:
            print("* No Awakening Data found, please update your bookmark")
        else:
            print("* Awakening Lvl Image:", export['awakening'], ", Awakening Type:", export['awaktype'])
        if 'domain' not in export:
            print("* No Domain Data found, please update your bookmark")
        else:
            print("* Domain #", len(export['domain']))
        if 'saint' not in export:
            print("* No Saint Data found, please update your bookmark")
        else:
            print("* Saint #", len(export['saint']))
        if 'extra' not in export:
            print("* No Extra Data found, please update your bookmark")
        else:
            print("* Extra #", len(export['extra']))
        self.checkEMP()
        self.emp_cache[str(export['id'])] = export
        with open('emp/{}.json'.format(export['id']), mode='w', encoding="utf-8") as outfile:
            json.dump(export, outfile)
        print("* Task completed with success!")

    async def settings_menu(self : PartyBuilder) -> None:
        while True:
            print("")
            print("Settings:")
            print("[0] Change quality ( Current:", self.settings.get('quality', '4k'),")")
            print("[1] Enable Disk Caching ( Current:", self.settings.get('caching', False),")")
            print("[2] Generate skin.png ( Current:", self.settings.get('skin', True),")")
            print("[3] Generate emp.png ( Current:", self.settings.get('emp', False),")")
            print("[4] Set Asset Server ( Current:", self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net'),")")
            print("[5] Show HP bar on skin.png ( Current:", self.settings.get('hp', True),")")
            print("[6] Guess Opus / Draco / Ultima 3rd skill ( Current:", self.settings.get('opus', True),")")
            print("[7] Set GBFTMR Path ( Current:", self.settings.get('gbftmr_path', ''),")")
            print("[8] Use GBFTMR if imported ( Current:", self.settings.get('gbftmr_use', False),")")
            print("[9] Empty Asset Cache")
            print("[10] Empty EMP Cache")
            print("[Any] Back")
            match input():
                case "0":
                    v = ({'720p':0, '1080p':1, '4K':2}[self.settings.get('quality', '4k')] + 1) % 3
                    self.settings['quality'] = {0:'720p', 1:'1080p', 2:'4K'}.get(v, '4k')
                case "1":
                    self.settings['caching'] = not self.settings.get('caching', False)
                case "2":
                    self.settings['skin'] = not self.settings.get('skin', False)
                case "3":
                    self.settings['emp'] = not self.settings.get('emp', False)
                case "4":
                    print("Input the url of the asset server to use (Leave blank to cancel): ")
                    url : str = input()
                    if url != "":
                        url = url.lower().replace('http://', '').replace('https://', '')
                        if not url.endswith('/'):
                            url += '/'
                        tmp : str = self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net')
                        self.settings['endpoint'] = url
                        try:
                            await self.retrieveImage("assets_en/img/sp/zenith/assets/ability/1.png", forceDownload=True)
                            print("Asset Server test: Success")
                            print("Asset Server set to:", url)
                        except:
                            self.settings['endpoint'] = tmp
                            print("Asset Server test: Failed")
                            print("Did you input the right url?")
                case "5":
                    self.settings['hp'] = not self.settings.get('hp', True)
                case "6":
                    self.settings['opus'] = not self.settings.get('opus', False)
                case "7":
                    print("Input the path of the GBFTMR folder (Leave blank to cancel): ")
                    folder : str = input()
                    if folder != "":
                        folder = folder.replace('\\', '/').replace('//', '/')
                        if not folder.endswith('/'): folder += '/'
                        self.settings['gbftmr_path'] = folder
                        if self.gbftmr is not None:
                            print("The change will take effect the next time")
                        elif self.importGBFTMR(self.settings['gbftmr_path']):
                            print("GBFTMR is imported with success")
                        else:
                            print("Failed to import GBFTMR")
                case "8":
                    self.settings['gbftmr_use'] = not self.settings.get('gbftmr_use', False)
                case "9":
                    self.emptyCache()
                case "10":
                    self.emptyCache()
                case _:
                    return

    def checkEMP(self : PartyBuilder) -> None: # check if emp folder exists (and create it if needed)
        if not os.path.isdir('emp'):
            os.mkdir('emp')

    def emptyEMP(self : PartyBuilder) -> None: # delete the emp folder
        try:
            shutil.rmtree('emp')
            print("Deleted the emp folder")
        except:
            print("Failed to delete the emp folder")

    def checkDiskCache(self : PartyBuilder) -> None: # check if cache folder exists (and create it if needed)
        if not os.path.isdir('cache'):
            os.mkdir('cache')

    def emptyCache(self : PartyBuilder) -> None: # delete the cache folder
        try:
            shutil.rmtree('cache')
            print("Deleted the cache folder")
        except:
            print("Failed to delete the cache folder")

    def cpyBookmark(self : PartyBuilder) -> bool:
        try:
            if self.bookmark is None:
                with open("bookmarklet.txt", mode="r", encoding="utf-8") as f:
                    self.bookmark = f.read()
            pyperclip.copy(self.bookmark)
            return True
        except Exception as e:
            print(self.pexc(e))
            print("Couldn't open bookmarklet.txt")
            return False

    def importGBFTMR(self : PartyBuilder, path : str) -> bool:
        try:
            if self.gbftmr is not None:
                return True
            module_name = "gbftmr.py"

            spec = importlib.util.spec_from_file_location("GBFTMR.gbftmr", path + module_name)
            module = importlib.util.module_from_spec(spec)
            sys.modules["GBFTMR.gbftmr"] = module
            spec.loader.exec_module(module)
            self.gbftmr = module.GBFTMR(path, self.client)
            if self.gbftmr.VERSION[0] >= 2 and self.gbftmr.VERSION[1] >= 0:
                return True
            self.gbftmr = None
            return False
        except:
            self.gbftmr = None
            return False

    def cmpVer(self : PartyBuilder, mver : str, tver : str) -> bool: # compare version strings, True if mver greater or equal, else False
        me : str = mver.split('.')
        te : str = tver.split('.')
        for i in range(0, min(len(me), len(te))):
            if int(me[i]) < int(te[i]):
                return False
            elif int(me[i]) > int(te[i]):
                return True
        return True

    async def update_check(self : PartyBuilder, command_line : bool = True) -> bool:
        interacted : bool = False
        if self.settings.get('update', False):
            try:
                response = await self.client.get("https://raw.githubusercontent.com/MizaGBF/GBFPIB/main/manifest.json")
                async with response:
                    if response.status != 200: raise Exception()
                    manifest = await response.json(content_type=None)
                    if not self.cmpVer(self.manifest.get('version', '10.0'), manifest.get('version', '10.1')):
                        interacted = True
                        if (command_line and input("An update is available.\nCurrent Version: {}\nNew Version: {}\nUpdate now? (type 'y' to accept):".format(self.manifest.get('version', 'Unknown version 10'), manifest.get('version', 'Unknown version 10 or higher'))).lower() == 'y') or (not command_line and messagebox.askyesno(title="Update", message="An update is available.\nCurrent Version: {}\nNew Version: {}\nUpdate now?".format(self.manifest.get('version', 'Unknown version 10'), manifest.get('version', 'Unknown version 10 or higher')))):
                            try:
                                response : aiohttp.Response = await self.client.get("https://github.com/MizaGBF/GBFPIB/archive/refs/heads/main.zip", allow_redirects=True)
                                async with response:
                                    if response.status != 200:
                                        raise Exception()
                                    with BytesIO(await response.read()) as zip_content:
                                        with ZipFile(zip_content, 'r') as zip_ref:
                                            # list files
                                            folders = set()
                                            file_list = zip_ref.namelist()
                                            for file in file_list:
                                                if ".git" in file: continue
                                                folders.add("/".join(file.split('/')[1:-1]))
                                            # make folders (if missing)
                                            for path in folders:
                                                if path == "": continue
                                                os.makedirs(os.path.dirname(path if path.endswith("/") else path+"/"), exist_ok=True)
                                            # write files
                                            for file in file_list:
                                                if ".git" in file: continue
                                                if file.split("/")[-1] in ["settings.json"] or file.endswith("/"): continue
                                                path = "/".join(file.split('/')[1:])
                                                with open(path, mode="wb") as f:
                                                    f.write(zip_ref.read(file))
                                if command_line:
                                    print("Update successful.\nThe application will now restart.\nMake sure to update your Bookmarklet if needed.")
                                    input("Press a key to continue:")
                                else:
                                    messagebox.showinfo("Update", "Update successful.\nThe application will now restart.\nMake sure to update your Bookmarklet if needed.")
                                try:
                                    if int(self.manifest['requirements']) < int(manifest['requirements']):
                                        self.manifest = manifest
                                        manifest['pending'] = True
                                        self.saveManifest()
                                except:
                                    pass
                                self.restart()
                                os._exit(0)
                            except Exception as eb:
                                raise eb
            except Exception as ea:
                print(self.pexc(ea))
                if command_line:
                    print("An error occured.\nYou might need to update manually.")
                else:
                    messagebox.showerror("Error", "An error occured: {}\nYou might need to update manually.".format(ea))
                interacted = True
        return interacted

    async def cli(self) -> None: # old command line menu
        while True:
            try:
                print("")
                print("Main Menu:")
                print("[0] Run")
                print("[1] Get Party Bookmarklet")
                print("[2] Change settings")
                print("[Any] Exit")
                s = input()
                if s == "0":
                    await self.generate()
                elif s == "1":
                    self.cpyBookmark()
                    print("Bookmarklet copied!")
                    print("To setup on chrome:")
                    print("1) Make a new bookmark (of GBF for example)")
                    print("2) Right-click and edit")
                    print("3) Change the name if you want")
                    print("4) Paste the code in the url field")
                elif s == "2":
                    await self.settings_menu()
                    self.save()
                else:
                    self.save()
                    return
            except Exception as e:
                print(e)
                self.save()
                return

    def restart(self : PartyBuilder) -> None:
        subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)

    async def start(self : PartyBuilder) -> None:
        async with self.init_client():
            if self.importGBFTMR(self.settings.get('gbftmr_path', '')):
                print("GBFTMR imported with success")
            
                # parse parameters
                prog_name : str
                try: prog_name = sys.argv[0].replace('\\', '/').split('/')[-1]
                except: prog_name = "gbfpib.pyw" # fallback to default
                # Set Argument Parser
                parser : argparse.ArgumentParser = argparse.ArgumentParser(prog=prog_name, description="Granblue Fantasy Party Image Builder v{} https://github.com/MizaGBF/GBFPIB".format(self.manifest.get('version', '')))
                settings = parser.add_argument_group('settings', 'commands to alter the update behavior.')
                settings.add_argument('-c', '--cli', help="invoke the CLI.", action='store_const', const=True, default=False, metavar='')
                settings.add_argument('-f', '--fast', help="directly call the generate function. The party or EMP data must be in your clipboard beforehand.", action='store_const', const=True, default=False, metavar='')
                settings.add_argument('-w', '--wait', help="wait 10 seconds after the generation using -f/--fast", action='store_const', const=True, default=False, metavar='')
                args : argparse.Namespace = parser.parse_args()
                
            if args.fast:
                await self.generate(fast=True)
                if not args.wait:
                    print("Closing in 10 seconds...")
                    time.sleep(10)
            elif args.cli:
                await self.update_check(True)
                await self.cli()
            else:
                await self.update_check()
                await (Interface(asyncio.get_event_loop(), self).run())

class GBFTMR_Select(Tk.Tk):
    def __init__(self : GBFTMR_Select, interface : Interface, loop, export : dict) -> None:
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.interface : Interface = interface
        self.loop = loop
        self.export : dict = export
        self.title("GBFTMR")
        self.iconbitmap('icon.ico')
        self.resizable(width=False, height=False) # not resizable
        template_list = self.interface.pb.gbftmr.getTemplateList()
        Tk.Label(self, text="Generate a Video Thumbnail with GBFTMR").grid(row=0, column=0, columnspan=4, sticky="w")
        Tk.Label(self, text="Template").grid(row=1, column=0, columnspan=1, sticky="w")
        self.tempopt = ttk.Combobox(self, values=template_list)
        self.tempopt.bind("<<ComboboxSelected>>", self.update_UI)
        self.tempopt.set(template_list[0])
        self.tempopt.grid(row=1, column=1, columnspan=3, stick="ws")

        self.make_bt = Tk.Button(self, text="Make", command=lambda: self.loop.create_task(self.confirm()))
        self.make_bt.grid(row=90, column=0, columnspan=2, sticky="we")
        Tk.Button(self, text="Cancel", command=self.cancel).grid(row=90, column=2, columnspan=2, sticky="we")
        
        self.options : None|dict = None
        self.optelems : list = []
        self.update_UI()
        self.apprunning : bool = True
        self.result : bool = False
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    async def run(self : GBFTMR_Select) -> bool:
        while self.apprunning:
            self.update()
            await asyncio.sleep(0.02)
        try:
            self.destroy()
        except:
            pass
        return self.result

    def update_UI(self : GBFTMR_Select, *args) -> None:
        self.options = self.interface.pb.gbftmr.getThumbnailOptions(self.tempopt.get())
        for t in self.optelems:
            t[0].destroy()
            t[1].destroy()
        self.optelems = []
        for i, e in enumerate(self.options["choices"]):
            label = Tk.Label(self, text=e[0])
            label.grid(row=2+i, column=0, columnspan=2, sticky="w")
            if e[1] is None:
                widget = Tk.Entry(self)
                widget.grid(row=2+i, column=2, columnspan=2, sticky="we")
            else:
                widget = ttk.Combobox(self, values=e[1])
                widget.set(e[1][0])
                widget.grid(row=2+i, column=2, columnspan=2, sticky="we")
            self.optelems.append((label, widget))

    async def confirm(self : GBFTMR_Select) -> None:
        for i in range(len(self.optelems)):
            if self.options["choices"][i][1] is None:
                choice = self.optelems[i][1].get()
            else:
                for j in range(len(self.options["choices"][i][1])):
                    if self.options["choices"][i][1][j] == self.optelems[i][1].get():
                        break
                choice = self.options["choices"][i][2][j]
            self.options["choices"][i][-1](self.options, self.options["choices"][i][-2], choice)
        self.options["settings"]["gbfpib"] = self.export
        self.destroy()
        try:
            await self.interface.pb.gbftmr.makeThumbnail(self.options["settings"], self.options["template"])
            self.result = True
        except Exception as e:
            print(self.interface.pb.pexc(e))
            self.interface.events.append(("Error", "An error occured, impossible to generate the thumbnail"))
        self.apprunning = False

    def cancel(self : GBFTMR_Select) -> None:
        self.apprunning = False

class Interface(Tk.Tk): # interface
    BW = 15
    BH = 1
    def __init__(self : Interface, loop, pb : PartyBuilder) -> None:
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.loop = loop
        self.pb : PartyBuilder = pb
        self.apprunning : bool = True
        self.iconbitmap('icon.ico')
        self.title("GBFPIB {}".format(self.pb.manifest.get('version', '')))
        self.resizable(width=False, height=False) # not resizable
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.to_disable = []
        
        # run part
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=0, rowspan=2, sticky="nwe")
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Run")
        self.to_disable.append(Tk.Button(tabcontent, text="Build Images", command=lambda: self.loop.create_task(self.build()), width=self.BW, height=self.BH))
        self.to_disable[-1].grid(row=0, column=0, sticky="we")
        self.to_disable.append(Tk.Button(tabcontent, text="Add EMP", command=self.add_emp, width=self.BW, height=self.BH))
        self.to_disable[-1].grid(row=1, column=0, sticky="we")
        self.to_disable.append(Tk.Button(tabcontent, text="Bookmark", command=self.bookmark, width=self.BW, height=self.BH))
        self.to_disable[-1].grid(row=2, column=0, sticky="we")
        self.to_disable.append(Tk.Button(tabcontent, text="Set Server", command=lambda: self.loop.create_task(self.setserver()), width=self.BW, height=self.BH))
        self.to_disable[-1].grid(row=3, column=0, sticky="we")
        self.to_disable.append(Tk.Button(tabcontent, text="Check Update", command=lambda: self.loop.create_task(self.update_check()), width=self.BW, height=self.BH))
        self.to_disable[-1].grid(row=4, column=0, sticky="we")
        
        # setting part
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=1, rowspan=2, sticky="nwe")
        ### Settings Tab
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Settings")
        self.qual_variable = Tk.StringVar(self)
        options = ['720p', '1080p', '4K']
        self.qual_variable.set(self.pb.settings.get('quality', options[-1]))
        Tk.Label(tabcontent, text="Quality").grid(row=0, column=0, sticky="ws")
        opt = Tk.OptionMenu(tabcontent, self.qual_variable, *options, command=self.qual_changed)
        opt.grid(row=0, column=1)
        self.to_disable.append(opt)
        
        self.skin_var = Tk.IntVar(value=self.pb.settings.get('skin', True))
        Tk.Label(tabcontent, text="Do Skins").grid(row=1, column=0, sticky="ws")
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.skin_var, command=self.toggleSkin))
        self.to_disable[-1].grid(row=1, column=1)
        
        self.emp_var = Tk.IntVar(value=self.pb.settings.get('emp', False))
        Tk.Label(tabcontent, text="Do EMP").grid(row=2, column=0, sticky="ws")
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.emp_var, command=self.toggleEMP))
        self.to_disable[-1].grid(row=2, column=1)
        
        self.update_var = Tk.IntVar(value=self.pb.settings.get('update', False))
        Tk.Label(tabcontent, text="Auto Update").grid(row=3, column=0, sticky="ws")
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.update_var, command=self.toggleUpdate))
        self.to_disable[-1].grid(row=3, column=1)
        
        ### Settings Tab
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Advanced")
        
        self.cache_var = Tk.IntVar(value=self.pb.settings.get('caching', False))
        Tk.Label(tabcontent, text="Cache Assets").grid(row=0, column=0, sticky="ws")
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.cache_var, command=self.toggleCaching))
        self.to_disable[-1].grid(row=0, column=1)
        
        self.hp_var = Tk.IntVar(value=self.pb.settings.get('hp', True))
        Tk.Label(tabcontent, text="HP Bar on skin.png").grid(row=1, column=0, sticky="ws")
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.hp_var, command=self.toggleHP))
        self.to_disable[-1].grid(row=1, column=1)
        
        self.opus_var = Tk.IntVar(value=self.pb.settings.get('opus', False))
        Tk.Label(tabcontent, text="Guess Opus/Draco/Ultima Key").grid(row=3, column=0, sticky="ws")
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.opus_var, command=self.toggleOpus))
        self.to_disable[-1].grid(row=3, column=1)
        
        ### GBFTMR plugin Tab
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="GBFTMR")
        self.to_disable.append(Tk.Button(tabcontent, text="Set Path", command=self.setGBFTMR, width=self.BW, height=self.BH))
        self.to_disable[-1].grid(row=0, column=0, columnspan=2, sticky="we")
        self.gbftmr_var = Tk.IntVar(value=self.pb.settings.get('gbftmr_use', False))
        self.gbftmr_status = Tk.Label(tabcontent, text="Not Imported")
        self.gbftmr_status.grid(row=1, column=0, sticky="ws")
        Tk.Label(tabcontent, text="Enable").grid(row=2, column=0, sticky="ws")
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.gbftmr_var, command=self.toggleGBFTMR))
        self.to_disable[-1].grid(row=2, column=1)
        self.to_disable.append(Tk.Button(tabcontent, text="Make Thumbnail", command=lambda: self.loop.create_task(self.runGBFTMR()), width=self.BW, height=self.BH))
        self.to_disable[-1].grid(row=3, column=0, columnspan=2, sticky="we")
        if self.pb.gbftmr is not None:
            self.gbftmr_status.config(text="Imported")
        
        # other
        self.status = Tk.Label(self, text="Starting")
        self.status.grid(row=0, column=0, sticky="w")
        
        self.process_running = False
        self.events = []

    async def run(self : Interface) -> None:
        # main loop
        run_flag = False
        while self.apprunning:
            if len(self.events) > 0:
                ev = self.events.pop(0)
                if ev[0] == "Info": messagebox.showinfo(ev[0], ev[1])
                elif ev[0] == "Error": messagebox.showerror(ev[0], ev[1])
            if not self.process_running:
                if run_flag:
                    for e in self.to_disable:
                        e.configure(state=Tk.NORMAL)
                    run_flag = False
                self.status.config(text="Idle", background='#c7edcd')
            else:
                if not run_flag:
                    for e in self.to_disable:
                        e.configure(state=Tk.DISABLED)
                    run_flag = True
                self.status.config(text="Running", background='#edc7c7')
            self.update()
            await asyncio.sleep(0.02)
        self.pb.save()
        self.destroy() # destroy the window

    def close(self : Interface) -> None: # called by the app when closed
        self.apprunning = False

    async def build(self) -> None:
        if self.process_running:
            messagebox.showinfo("Info", "Wait for the current process to finish")
            return
        await self.generate()

    async def generate(self : Interface, thumbnailOnly : bool = False) -> None:
        try:
            self.process_running = True
            gbftmr_use = self.pb.settings.get('gbftmr_use', False)
            export = self.pb.clipboardToJSON()
            if export.get('ver', 0) < 1:
                self.events.append(("Error", "Your bookmark is outdated, please update it!"))
                self.thread = None
                return
            
            tasks = []
            async with asyncio.TaskGroup() as tg:
                if not thumbnailOnly:
                    tasks.append(tg.create_task(self.pb.generate_party(export)))
                if self.pb.gbftmr and gbftmr_use:
                    tasks.append(tg.create_task(GBFTMR_Select(self, self.loop, export).run()))
            result = False
            for t in tasks:
                result = (t.result() is True) or result
            if result:
                if not thumbnailOnly:
                    self.events.append(("Info", "Image(s) generated with success"))
                else:
                    self.events.append(("Info", "Thumbnail generated with success"))
        except Exception as e:
            print(self.pb.pexc(e))
            self.events.append(("Error", "An error occured, did you press the bookmark?"))
        self.process_running = False

    def add_emp(self : Interface) -> None:
        try:
            self.pb.generate_emp(self.pb.clipboardToJSON())
            self.events.append(("Info", "EMP saved with success"))
        except:
            self.events.append(("Error", "An error occured, did you press the bookmark?"))

    def bookmark(self : Interface) -> None:
        self.pb.cpyBookmark()
        messagebox.showinfo("Info", "Bookmarklet copied!\nTo setup on chrome:\n1) Make a new bookmark (of GBF for example)\n2) Right-click and edit\n3) Change the name if you want\n4) Paste the code in the url field")

    def qual_changed(self : Interface, *args) -> None:
        self.pb.settings['quality'] = args[0]

    def toggleCaching(self : Interface) -> None:
        self.pb.settings['caching'] = (self.cache_var.get() != 0)
        
    def toggleSkin(self : Interface) -> None:
        self.pb.settings['skin'] = (self.skin_var.get() != 0)

    def toggleEMP(self : Interface) -> None:
        self.pb.settings['emp'] = (self.emp_var.get() != 0)

    def toggleUpdate(self : Interface) -> None:
        self.pb.settings['update'] = (self.update_var.get() != 0)

    def toggleHP(self : Interface) -> None:
        self.pb.settings['hp'] = (self.hp_var.get() != 0)

    def toggleOpus(self : Interface) -> None:
        self.pb.settings['opus'] = (self.opus_var.get() != 0)

    def toggleGBFTMR(self : Interface) -> None:
        self.pb.settings['gbftmr_use'] = (self.gbftmr_var.get() != 0)

    async def setserver(self : Interface) -> None:
        url : str|None = simpledialog.askstring("Set Asset Server", "Input the URL of the Asset Server to use\nLeave blank to reset to the default setting.")
        if url is not None:
            if url == '': url = 'prd-game-a-granbluefantasy.akamaized.net/'
            url = url.lower().replace('http://', '').replace('https://', '')
            if not url.endswith('/'): url += '/'
            tmp = self.pb.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net')
            self.pb.settings['endpoint'] = url
            try:
                await self.pb.retrieveImage("assets_en/img/sp/zenith/assets/ability/1.png", forceDownload=True)
                messagebox.showinfo("Info", "Asset Server set with success to:\n" + url)
            except:
                self.pb.settings['endpoint'] = tmp
                messagebox.showerror("Error", "Failed to find the specified server:\n" + url + "\nCheck if the url is correct")

    def setGBFTMR(self : Interface) -> None:
        folder_selected : str|None = filedialog.askdirectory(title="Select the GBFTMR folder")
        if folder_selected == '': return
        self.pb.settings['gbftmr_path'] = folder_selected + "/"
        if self.pb.gbftmr is not None:
            messagebox.showinfo("Info", "GBFTMR is already loaded, the change will take affect at the next startup")
        else:
            self.pb.importGBFTMR(self.pb.settings.get('gbftmr_path', ''))
            if self.pb.gbftmr is not None:
                messagebox.showinfo("Info", "Imported GBFTMR with success")
                self.gbftmr_status.config(text="Imported")
            else:
                messagebox.showinfo("Error", "Failed to import GBFTMR")

    async def runGBFTMR(self : Interface) -> None:
        if self.pb.gbftmr:
            if self.process_running:
                messagebox.showinfo("Info", "Wait for the current process to finish")
                return
            await self.make(True)
        else:
            self.events.append(("Error", "GBFTMR isn't loaded"))

    async def update_check(self : Interface) -> None:
        if not await self.pb.update_check():
            messagebox.showinfo("Info", "GBFPIB is up to date")

if __name__ == "__main__":
    asyncio.run(PartyBuilder().start())