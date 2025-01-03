import asyncio
from contextlib import asynccontextmanager

from typing import Generator, Optional, Union

import time
import os
import sys
import shutil
import traceback

import re
from urllib.parse import quote
from base64 import b64decode, b64encode

import json
from io import BytesIO

import importlib.util

from tkinter import messagebox, filedialog, simpledialog
import tkinter as Tk
import tkinter.ttk as ttk

import subprocess
from zipfile import ZipFile


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
    DARK_OPUS_IDS = [
        "1040310600","1040310700","1040415000","1040415100","1040809400","1040809500","1040212500","1040212600","1040017000","1040017100","1040911000","1040911100",
        "1040310600_02","1040310700_02","1040415000_02","1040415100_02","1040809400_02","1040809500_02","1040212500_02","1040212600_02","1040017000_02","1040017100_02","1040911000_02","1040911100_02",
        "1040310600_03","1040310700_03","1040415000_03","1040415100_03","1040809400_03","1040809500_03","1040212500_03","1040212600_03","1040017000_03","1040017100_03","1040911000_03","1040911100_03"
    ]
    ULTIMA_OPUS_IDS = [
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
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Rosetta/Dev'
    
    def __init__(self, debug : bool = False) -> None:
        self.debug = debug
        if self.debug: print("DEBUG enabled")
        self.japanese = False # True if the data is japanese, False if not
        self.classes = None
        self.class_modified = False
        self.prev_lang = None # Language used in the previous run
        self.babyl = False # True if the data contains more than 5 allies
        self.sandbox = False # True if the data contains more than 10 weapons
        self.cache = {} # memory cache
        self.emp_cache = {} # emp cache
        self.sumcache = {} # wiki summon cache
        self.fonts = {'mini':None, 'small':None, 'medium':None, 'big':None} # font to use during the processing
        self.quality = 1 # quality ratio in use currently
        self.definition = None # image size
        self.running = False # True if the image building is in progress
        self.settings = {} # settings.json data
        self.manifest = {} # manifest.json data
        self.startup_check()
        self.load() # loading settings.json
        self.dummy_layer = self.make_canvas()
        self.gbftmr = None
        if self.importGBFTMR(self.settings.get('gbftmr_path', '')):
            print("GBFTMR imported with success")
        self.wtm = b64decode("TWl6YSdzIEdCRlBJQiA=").decode('utf-8')+self.manifest.get('version', '')
        self.client = None
        if self.manifest.get('pending', False):
            self.manifest['pending'] = False
            self.saveManifest()

    @asynccontextmanager
    async def init_client(self) -> Generator['aiohttp.ClientSession', None, None]:
        try:
            self.client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
            yield self.client
        finally:
            await self.client.close()

    def pexc(self, e : Exception) -> str:
        return "".join(traceback.format_exception(type(e), e, e.__traceback__))

    def loadManifest(self) -> None: # load manifest.json
        try:
            with open("manifest.json") as f:
                self.manifest = json.load(f)
        except:
            pass

    def saveManifest(self) -> None: # save manifest.json
        try:
            with open("manifest.json", 'w') as outfile:
                json.dump(self.manifest, outfile)
        except:
            pass

    def loadClasses(self) -> None:
        try:
            self.class_modified = False
            with open("classes.json", mode="r", encoding="utf-8") as f:
                self.classes = json.load(f)
        except:
            self.classes = {}

    def saveClasses(self) -> None:
        try:
            if self.class_modified:
                with open("classes.json", mode='w', encoding='utf-8') as outfile:
                    json.dump(self.classes, outfile)
        except:
            pass

    def importRequirements(self) -> None:
        global aiohttp
        import aiohttp
        
        global Image
        global ImageFont
        global ImageDraw
        from PIL import Image, ImageFont, ImageDraw
        
        global pyperclip
        import pyperclip

    def startup_check(self) -> None:
        self.loadManifest()
        if self.manifest.get('pending', False):
            if messagebox.askyesno(title="Info", message="I will now attempt to update required dependencies.\nDo you accept?\nElse it will be ignored if the application can start."):
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                    self.importRequirements()
                    messagebox.showinfo("Info", "Installation successful.")
                except Exception as e:
                    print(self.pexc(e))
                    if sys.platform == "win32":
                        import ctypes
                        try: is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                        except: is_admin = False
                        if not is_admin:
                            if messagebox.askyesno(title="Error", message="An error occured: {}\nDo you want to restart the application with administrator permissions?".format(e)):
                                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1) # restart as admin
                        else:
                            messagebox.showerror("Error", "An error occured: {}\nFurther troubleshooting is needed.\nYou might need to install the dependancies manually, check the README for details.")
                    else:
                        messagebox.showerror("Error", "An error occured: {}\nFurther troubleshooting is needed.\nYou might need to install the dependancies manually, check the README for details.")
                    exit(0)
        else:
            try:
                self.importRequirements()
            except Exception as e:
                print(self.pexc(e))
                if messagebox.askyesno(title="Error", message="An error occured while importing the dependencies: {}\nThey might be outdated or missing.\nRestart and attempt to install them now?".format(e)):
                    self.manifest['pending'] = True
                    self.saveManifest()
                    self.restart()
                exit(0)
        print("Granblue Fantasy Party Image Builder", self.manifest.get('version', ''))

    def load(self) -> None: # load settings.json
        try:
            with open('settings.json') as f:
                self.settings = json.load(f)
        except:
            print("Failed to load settings.json")
            while True:
                print("An empty settings.json file will be created, continue? (y/n)")
                i = input()
                if i.lower() == 'n': exit(0)
                elif i.lower() == 'y': break
                self.save()

    def save(self) -> None: # save settings.json
        try:
            with open('settings.json', 'w') as outfile:
                json.dump(self.settings, outfile)
        except:
            pass

    async def retrieveImage(self, path : str, remote : bool = True, forceDownload : bool = False) -> bytes:
        if self.japanese: path = path.replace('assets_en', 'assets')
        if forceDownload or path not in self.cache:
            try: # get from disk cache if enabled
                if forceDownload: raise Exception()
                if self.settings.get('caching', False):
                    with open("cache/" + b64encode(path.encode('utf-8')).decode('utf-8'), "rb") as f:
                        self.cache[path] = f.read()
                    await asyncio.sleep(0)
                else:
                    raise Exception()
            except: # else request it from gbf
                if remote:
                    print("[GET] *Downloading File", path)
                    response = await self.client.get('https://' + self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net/') + path, headers={'connection':'keep-alive'})
                    async with response:
                        if response.status != 200: raise Exception("HTTP Error code {} for url: {}".format(response.status, 'https://' + self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net/') + path))
                        self.cache[path] = await response.read()
                        if self.settings.get('caching', False):
                            try:
                                with open("cache/" + b64encode(path.encode('utf-8')).decode('utf-8'), "wb") as f:
                                    f.write(self.cache[path])
                                await asyncio.sleep(0)
                            except Exception as e:
                                print(e)
                                pass
                else:
                    with open(path, "rb") as f:
                        self.cache[path] = f.read()
                    await asyncio.sleep(0)
        return self.cache[path]

    async def pasteImage(self, imgs : list, file : Union[str, BytesIO], offset : tuple, resize : Optional[tuple] = None, transparency : bool = False, start : int = 0, end : int = 99999999, crop : Optional[tuple] = None) -> list: # paste an image onto another
        if isinstance(file, str):
            if self.japanese: file = file.replace('_EN', '')
            file = BytesIO(await self.retrieveImage(file, remote=False))
        buffers = [Image.open(file)]
        if crop is not None:
            if len(crop) == 4:
                buffers.append(buffers[-1].crop(crop))
            else:
                buffers.append(buffers[-1].crop((0, 0, crop[0], crop[1])))
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize, Image.Resampling.LANCZOS))
        if not transparency:
            for i in range(start, min(len(imgs), end)):
                imgs[i].paste(buffers[-1], offset, buffers[-1])
        else:
            layer = self.dummy_layer.copy()
            layer.paste(buffers[-1], offset, buffers[-1])
            for i in range(start, min(len(imgs), end)):
                tmp = Image.alpha_composite(imgs[i], layer)
                imgs[i].close()
                imgs[i] = tmp
            layer.close()
        await asyncio.sleep(0)
        for buf in buffers: buf.close()
        del buffers
        file.close()
        return imgs

    async def dlAndPasteImage(self, imgs : list, path : str, offset : tuple, resize : Optional[tuple] = None, transparency : bool = False, start : int = 0, end : int = 99999999, crop : Optional[tuple] = None) -> list: # dl an image and call pasteImage()
        with BytesIO(await self.retrieveImage(path)) as file_jpgdata:
            return await self.pasteImage(imgs, file_jpgdata, offset, resize, transparency, start, end, crop)

    def add(self, A:tuple, B:tuple):
        return (A[0]+B[0], A[1]+B[1])

    def fixCase(self, terms : str) -> str: # function to fix the case (for wiki search requests)
        terms = terms.split(' ')
        fixeds = []
        for term in terms:
            fixed = ""
            up = False
            special = {"and":"and", "of":"of", "de":"de", "for":"for", "the":"the", "(sr)":"(SR)", "(ssr)":"(SSR)", "(r)":"(R)"} # case where we don't don't fix anything and return it
            if term.lower() in special:
                return special[term.lower()]
            for i in range(0, len(term)): # for each character
                if term[i].isalpha(): # if letter
                    if term[i].isupper(): # is uppercase
                        if not up: # we haven't encountered an uppercase letter
                            up = True
                            fixed += term[i] # save
                        else: # we have
                            fixed += term[i].lower() # make it lowercase and save
                    elif term[i].islower(): # is lowercase
                        if not up: # we haven't encountered an uppercase letter
                            fixed += term[i].upper() # make it uppercase and save
                            up = True
                        else: # we have
                            fixed += term[i] # save
                    else: # other characters
                        fixed += term[i] # we just save
                elif term[i] == "/" or term[i] == ":" or term[i] == "#" or term[i] == "-": # we reset the uppercase detection if we encounter those
                    up = False
                    fixed += term[i]
                else: # everything else,
                    fixed += term[i] # we save
            fixeds.append(fixed)
        return "_".join(fixeds) # return the result

    async def get_support_summon_from_wiki(self, name : str) -> Optional[str]: # search on gbf.wiki to match a summon name to its id
        try:
            name = name.lower()
            if name in self.sumcache: return self.sumcache[name]
            response = await self.client.get("https://gbf.wiki/index.php?title=Special:CargoExport&tables=summons&fields=id,name&format=json&limit=20000", headers={'connection':'close', 'User-Agent':self.USER_AGENT})
            async with response:
                if response.status != 200: raise Exception()
                data = await response.json()
                for summon in data:
                    if summon["name"].lower() == name:
                        self.sumcache[name] = summon["id"]
                        return summon["id"]
            return None
        except:
            return None

    def get_uncap_id(self, cs : int) -> str: # to get character portraits based on uncap levels
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def get_uncap_star(self, cs : int, cl : int) -> str: # to get character star based on uncap levels
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

    def get_summon_star(self, se : int, sl : int) -> str: # to get summon star based on uncap levels
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

    def fix_character_look(self, export : dict, i : int) -> str:
        style = ("" if str(export['cst'][i]) == '1' else "_st{}".format(export['cst'][i])) # style
        if style != "":
            uncap = "01"
        else:
            uncap = self.get_uncap_id(export['cs'][i])
        cid = export['c'][i]
        # SKIN FIX START ##################
        if str(cid).startswith('371'):
            match cid:
                case 3710098000: # seox skin
                    if export['cl'][i] > 80: cid = 3040035000 # eternal seox
                    else: cid = 3040262000 # event seox
                case 3710122000: # seofon skin
                    cid = 3040036000 # eternal seofon
                case 3710143000: # vikala skin
                    if export['ce'][i] == 3: cid = 3040408000 # apply earth vikala
                    elif export['ce'][i] == 6:
                        if export['cl'][i] > 50: cid = 3040252000 # SSR dark vikala
                        else: cid = 3020073000 # R dark vikala
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
                            if export['cl'][i] > 70: cid = 3040129000 # water SSR
                            else: cid = 3030150000 # water SR
                        case 3: cid = 3040296000 # earth
                case 3710172000: # tsubasa skin
                    cid = 3040180000
                case 3710176000: # mimlemel skin
                    if export['ce'][i] == 1: cid = 3040292000 # apply fire mimlemel
                    elif export['ce'][i] == 3: cid = 3030220000 # apply earth halloween mimlemel
                    elif export['ce'][i] == 4:
                        if export['cn'][i] in ['Mimlemel', 'ミムルメモル']: cid = 3030043000 # first sr wind mimlemel
                        else: cid = 3030166000 # second sr wind mimlemel
                case 3710191000: # cidala skin 1
                    if export['ce'][i] == 3: cid = 3040377000 # apply earth cidala
                case 3710195000: # cidala skin 2
                    if export['ce'][i] == 3: cid = 3040377000 # apply earth cidala
        # SKIN FIX END ##################
        if cid in self.NULL_CHARACTER: 
            if export['ce'][i] == 99:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['pce'])
            else:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['ce'][i])
        else:
            return "{}_{}{}".format(cid, uncap, style)

    async def get_mc_job_look(self, skin : str, job : int) -> str: # get the MC unskined filename based on id
        sjob = str((job//100) * 100 + 1)
        if sjob in self.classes:
            return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:]))
        else:
            tasks = []
            for mh in ["sw", "kn", "sp", "ax", "wa", "gu", "me", "bw", "mc", "kr"]:
                tasks.append(self.get_mc_job_look_sub(sjob, mh))
            for r in await asyncio.gather(*tasks):
                if r is not None:
                    self.class_modified = True
                    self.classes[sjob] = r
                    return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:])) 
        return ""

    async def get_mc_job_look_sub(self, job : str, mh : str) -> Optional[str]:
        response = await self.client.head("https://prd-game-a5-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/s/{}_{}_0_01.jpg".format(job, mh))
        async with response:
            if response.status != 200:
                return None
            return mh

    def process_special_weapon(self, export : dict, i : int, j : int) -> bool:
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
                elif export['w'][i] in self.ULTIMA_OPUS_IDS:
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

    def make_canvas(self, size : tuple = (1800, 2160)) -> 'Image':
        i = Image.new('RGB', size, "black")
        im_a = Image.new("L", size, "black")
        i.putalpha(im_a)
        im_a.close()
        return i

    async def make_party(self, export : dict) -> Union[str, tuple]:
        try:
            imgs = [self.make_canvas(), self.make_canvas()]
            print("[CHA] * Drawing Party...")
            if self.babyl:
                offset = (15, 10)
                nchara = 12
                csize = (180, 180)
                skill_width = 420
                pos = self.add(offset, (30, 0))
                jsize = (54, 45)
                roffset = (-6, -6)
                rsize = (60, 60)
                ssize = (50, 50)
                soffset = self.add(csize, (-csize[0], -ssize[1]*5//3))
                poffset = self.add(csize, (-105, -45))
                ssoffset = self.add(pos, (0, 10+csize[1]))
                stoffset = self.add(ssoffset, (3, 3))
                plsoffset = self.add(ssoffset, (447, 0))
                # background
                await self.pasteImage(imgs, "assets/bg.png", self.add(pos, (-15, -15)), (csize[0]*8+40, csize[1]*2+55), transparency=True, start=0, end=1)
            else:
                offset = (15, 10)
                nchara = 5
                csize = (250, 250)
                skill_width = 420
                pos = self.add(offset, (skill_width-csize[0], 0))
                jsize = (72, 60)
                roffset = (-10, -10)
                rsize = (90, 90)
                ssize = (66, 66)
                soffset = self.add(csize, (-csize[0]+ssize[0]//2, -ssize[1]))
                poffset = self.add(csize, (-110, -40))
                noffset = (9, csize[1]+10)
                loffset = (10, csize[1]+6+60)
                ssoffset = self.add(offset, (0, csize[1]))
                stoffset = self.add(ssoffset, (3, 3))
                plsoffset = self.add(ssoffset, (0, -150))
                # background
                await self.pasteImage(imgs, "assets/bg.png", self.add(pos, (-15, -10)), (25+csize[0]*6+30, csize[1]+175), transparency=True, start=0, end=1)
            
            # mc
            print("[CHA] |--> MC Skin:", export['pcjs'])
            print("[CHA] |--> MC Job:", export['p'])
            print("[CHA] |--> MC Master Level:", export['cml'])
            print("[CHA] |--> MC Proof Level:", export['cbl'])
            # class
            class_id = await self.get_mc_job_look(export['pcjs'], export['p'])
            await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/leader/s/{}.jpg".format(class_id), pos, csize, start=0, end=1)
            # job icon
            await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, jsize, transparency=True, start=0, end=1)
            if export['cbl'] == '6':
                await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/job/ico_perfection.png", self.add(pos, (0, jsize[1])), jsize, transparency=True, start=0, end=1)
            # skin
            if class_id != export['pcjs']:
                await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/leader/s/{}.jpg".format(export['pcjs']), pos, csize, start=1, end=2)
                await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, jsize, transparency=True, start=1, end=2)
            # allies
            for i in range(0, nchara):
                await asyncio.sleep(0)
                if self.babyl:
                    if i < 4: pos = self.add(offset, (csize[0]*i+30, 0))
                    elif i < 8: pos = self.add(offset, (csize[0]*i+40, 0))
                    else: pos = self.add(offset, (csize[0]*(i-4)+40, 10+csize[1]*(i//8)))
                    if i == 0: continue # quirk of babyl party, mc is counted
                else:
                    pos = self.add(offset, (skill_width+csize[0]*(i+1-1), 0))
                    if i >= 3: pos = self.add(pos, (25, 0))
                # portrait
                if i >= len(export['c']) or export['c'][i] is None: # empty
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/tower/assets/npc/s/3999999999.jpg", pos, csize, start=0, end=1)
                    continue
                print("[CHA] |--> Ally #{}:".format(i+1), export['c'][i], export['cn'][i], "Lv {}".format(export['cl'][i]), "Uncap-{}".format(export['cs'][i]), "+{}".format(export['cp'][i]), "Has Ring" if export['cwr'][i] else "No Ring")
                # portrait
                cid = self.fix_character_look(export, i)
                await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/npc/s/{}.jpg".format(cid), pos, csize, start=0, end=1)
                # skin
                if cid != export['ci'][i]:
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/npc/s/{}.jpg".format(export['ci'][i]), pos, csize, start=1, end=2)
                    has_skin = True
                else:
                    has_skin = False
                # star
                await self.pasteImage(imgs, self.get_uncap_star(export['cs'][i], export['cl'][i]), self.add(pos, soffset), ssize, transparency=True, start=0, end=2 if has_skin else 1)
                # rings
                if export['cwr'][i] == True:
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", self.add(pos, roffset), rsize, transparency=True, start=0, end=2 if has_skin else 1)
                # plus
                if export['cp'][i] > 0:
                    self.text(imgs, self.add(pos, poffset), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0), start=0, end=2 if has_skin else 1)
                if not self.babyl:
                    # name
                    await self.pasteImage(imgs, "assets/chara_stat.png", self.add(pos, (0, csize[1])), (csize[0], 60), transparency=True, start=0, end=1)
                    if len(export['cn'][i]) > 11: name = export['cn'][i][:11] + ".."
                    else: name = export['cn'][i]
                    self.text(imgs, self.add(pos, noffset), name, fill=(255, 255, 255), font=self.fonts['mini'], start=0, end=1)
                    # skill count
                    await self.pasteImage(imgs, "assets/skill_count_EN.png", self.add(pos, (0, csize[1]+60)), (csize[0], 60), transparency=True, start=0, end=1)
                    self.text(imgs, self.add(self.add(pos, loffset), (150, 0)), str(export['cb'][i+1]), fill=(255, 255, 255), font=self.fonts['medium'], stroke_width=4, stroke_fill=(0, 0, 0), start=0, end=1)
            await asyncio.sleep(0)

            # mc sub skills
            await self.pasteImage(imgs, "assets/subskills.png", ssoffset, (420, 147), transparency=True)
            count = 0
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
                    self.text(imgs, self.add(stoffset, (0, 48*count+voff)), export['ps'][i], fill=(255, 255, 255), font=self.fonts[f])
                    count += 1
            await asyncio.sleep(0)
            # paladin shield/manadiver familiar
            if export['cpl'][0] is not None:
                print("[CHA] |--> Paladin shields:", export['cpl'][0], "|", export['cpl'][1])
                await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/shield/s/{}.jpg".format(export['cpl'][0]), plsoffset, (150, 150), start=0, end=1)
                if export['cpl'][1] is not None and export['cpl'][1] != export['cpl'][0] and export['cpl'][1] > 0: # skin
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/shield/s/{}.jpg".format(export['cpl'][1]), plsoffset, (150, 150), start=1, end=2)
                    await self.pasteImage(imgs, "assets/skin.png", self.add(plsoffset, (0, -70)), (153, 171), start=1, end=2)
            elif export['fpl'][0] is not None:
                print("[CHA] |--> Manadiver Manatura:", export['fpl'][0], "|", export['fpl'][1])
                await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/familiar/s/{}.jpg".format(export['fpl'][0]), plsoffset, (150, 150), start=0, end=1)
                if export['fpl'][1] is not None and export['fpl'][1] != export['fpl'][0] and export['fpl'][1] > 0: # skin
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/familiar/s/{}.jpg".format(export['fpl'][1]), plsoffset, (150, 150), start=1, end=2)
                    await self.pasteImage(imgs, "assets/skin.png", self.add(plsoffset, (0, -45)), (76, 85), start=1, end=2)
            elif self.babyl: # to fill the blank space
                await self.pasteImage(imgs, "assets/characters_EN.png", self.add(ssoffset, (skill_width, 0)), (276, 75), transparency=True)
            return ('party', imgs)
        except Exception as e:
            imgs[0].close()
            imgs[1].close()
            return self.pexc(e)

    async def make_summon(self, export : dict) -> Union[str, tuple]:
        try:
            imgs = [self.make_canvas(), self.make_canvas()]
            print("[SUM] * Drawing Summons...")
            offset = (170, 425)
            sizes = [(271, 472), (266, 200), (273, 155)]
            durls = ["assets_en/img/sp/assets/summon/ls/2999999999.jpg","assets_en/img/sp/assets/summon/m/2999999999.jpg", "assets_en/img/sp/assets/summon/m/2999999999.jpg"]
            surls = ["assets_en/img/sp/assets/summon/party_main/{}.jpg", "assets_en/img/sp/assets/summon/party_sub/{}.jpg", "assets_en/img/sp/assets/summon/m/{}.jpg"]

            # background setup
            await self.pasteImage(imgs, "assets/bg.png", self.add(offset, (-15, -15)), (100+sizes[0][0]+sizes[1][0]*2+sizes[0][0]+48, sizes[0][1]+143), transparency=True, start=0, end=1)

            for i in range(0, 7):
                await asyncio.sleep(0)
                if i == 0:
                    pos = self.add(offset, (0, 0)) 
                    idx = 0
                elif i < 5:
                    pos = self.add(offset, (sizes[0][0]+50+((i-1)%2)*sizes[1][0]+18, 266*((i-1)//2)))
                    idx = 1
                else:
                    pos = self.add(offset, (sizes[0][0]+100+2*sizes[1][0]+18, 102+(i-5)*(sizes[2][1]+60)))
                    idx = 2
                    if i == 5: await self.pasteImage(imgs, "assets/subsummon_EN.png", (pos[0]+45, pos[1]-72-30), (180, 72), transparency=True, start=0, end=1)
                # portraits
                if export['s'][i] is None:
                    await self.dlAndPasteImage(imgs, durls[idx], pos, sizes[idx], start=0, end=1)
                    continue
                else:
                    print("[SUM] |--> Summon #{}:".format(i+1), export['ss'][i], "Uncap Lv{}".format(export['se'][i]), "Lv{}".format(export['sl'][i]))
                    await self.dlAndPasteImage(imgs, surls[idx].format(export['ss'][i]), pos, sizes[idx], start=0, end=1)
                # main summon skin
                if i == 0 and export['ssm'] is not None:
                    await self.dlAndPasteImage(imgs, surls[idx].format(export['ssm']), pos, sizes[idx], start=1, end=2)
                    await self.pasteImage(imgs, "assets/skin.png", self.add(pos, (sizes[idx][0]-85, 15)), (76, 85), start=1, end=2)
                    has_skin = True
                else:
                    has_skin = False
                # star
                await self.pasteImage(imgs, self.get_summon_star(export['se'][i], export['sl'][i]), pos, (66, 66), transparency=True, start=0, end=2 if has_skin else 1)
                # quick summon
                if export['qs'] is not None and export['qs'] == i:
                    await self.pasteImage(imgs, "assets/quick.png", self.add(pos, (0, 66)), (66, 66), transparency=True, start=0, end=2 if has_skin else 1)
                # level
                await self.pasteImage(imgs, "assets/chara_stat.png", self.add(pos, (0, sizes[idx][1])), (sizes[idx][0], 60), transparency=True, start=0, end=1)
                self.text(imgs, self.add(pos, (6,sizes[idx][1]+9)), "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
                # plus
                if export['sp'][i] > 0:
                    self.text(imgs, (pos[0]+sizes[idx][0]-95, pos[1]+sizes[idx][1]-50), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0), start=0, end=2 if has_skin else 1)
            await asyncio.sleep(0)

            # stats
            spos = self.add(offset, (sizes[0][0]+50+18, sizes[0][1]+60))
            await self.pasteImage(imgs, "assets/chara_stat.png",  spos, (sizes[1][0]*2, 60), transparency=True, start=0, end=1)
            await self.pasteImage(imgs, "assets/atk.png", self.add(spos, (9, 9)), (90, 39), transparency=True, start=0, end=1)
            await self.pasteImage(imgs, "assets/hp.png", self.add(spos, (sizes[1][0]+9, 9)), (66, 39), transparency=True, start=0, end=1)
            self.text(imgs, self.add(spos, (120, 9)), "{}".format(export['satk']), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
            self.text(imgs, self.add(spos, (sizes[1][0]+80, 9)), "{}".format(export['shp']), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
            return ('summon', imgs)
        except Exception as e:
            imgs[0].close()
            imgs[1].close()
            return self.pexc(e)

    async def make_weapon(self, export : dict, do_hp : bool, do_opus : bool) -> Union[str, tuple]:
        try:
            imgs = [self.make_canvas(), self.make_canvas()]
            print("[WPN] * Drawing Weapons...")
            if self.sandbox: offset = (25, 1050)
            else: offset = (170, 1050)
            skill_box_height = 144
            skill_icon_size = 72
            ax_icon_size = 86
            ax_separator = skill_box_height
            mh_size = (300, 630)
            sub_size = (288, 165)
            self.multiline_text(imgs, (1425, 2125), self.wtm, fill=(120, 120, 120, 255), font=self.fonts['mini'])
            await self.pasteImage(imgs, "assets/grid_bg.png", self.add(offset, (-15, -15)), (mh_size[0]+(4 if self.sandbox else 3)*sub_size[0]+60, 1425+(240 if self.sandbox else 0)), transparency=True, start=0, end=1)
            if self.sandbox:
                await self.pasteImage(imgs, "assets/grid_bg_extra.png", (offset[0]+mh_size[0]+30+sub_size[0]*3, offset[1]), (288, 1145), transparency=True, start=0, end=1)

            for i in range(0, len(export['w'])):
                await asyncio.sleep(0)
                wt = "ls" if i == 0 else "m"
                if i == 0: # mainhand
                    pos = (offset[0], offset[1])
                    size = mh_size
                    bsize = size
                elif i >= 10: # sandbox
                    if not self.sandbox: break
                    x = 3
                    y = (i-1) % 3
                    size = sub_size
                    pos = (offset[0]+bsize[0]+30+size[0]*x, offset[1]+(size[1]+skill_box_height)*y)
                else: # others
                    x = (i-1) % 3
                    y = (i-1) // 3
                    size = sub_size
                    pos = (offset[0]+bsize[0]+30+size[0]*x, offset[1]+(size[1]+skill_box_height)*y)
                # dual blade class
                if i <= 1 and export['p'] in self.AUXILIARY_CLS:
                    await self.pasteImage(imgs, ("assets/mh_dual.png" if i == 0 else "assets/aux_dual.png"), self.add(pos, (-2, -2)), self.add(size, (5, 5+skill_box_height)), transparency=True, start=0, end=1)
                # portrait
                if export['w'][i] is None or export['wl'][i] is None:
                    if i >= 10:
                        await self.pasteImage(imgs, "assets/arca_slot.png", pos, size, start=0, end=1)
                    else:
                        await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt), pos, size, start=0, end=1)
                    continue
                # ax and awakening check
                has_ax = len(export['waxt'][i]) > 0
                has_awakening = (export['wakn'][i] is not None and export['wakn'][i]['is_arousal_weapon'] and export['wakn'][i]['level'] is not None and export['wakn'][i]['level'] > 1)
                pos_shift = - skill_icon_size if (has_ax and has_awakening) else 0  # vertical shift of the skill boxes (if both ax and awk are presents)
                # portrait draw
                print("[WPN] |--> Weapon #{}".format(i+1), str(export['w'][i]), ", AX:", has_ax, ", Awakening:", has_awakening)
                await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/weapon/{}/{}.jpg".format(wt, export['w'][i]), pos, size, start=0, end=1)
                # skin
                has_skin = False
                if i <= 1 and export['wsm'][i] is not None:
                    if i == 0 or (i == 1 and export['p'] in self.AUXILIARY_CLS): # aux class check for 2nd weapon
                        await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/weapon/{}/{}.jpg".format(wt, export['wsm'][i]), pos, size, start=1, end=2)
                        await self.pasteImage(imgs, "assets/skin.png", self.add(pos, (size[0]-76, 0)), (76, 85), transparency=True, start=1, end=2)
                        has_skin = True
                # skill box
                nbox = 1 # number of skill boxes to draw
                if has_ax: nbox += 1
                if has_awakening: nbox += 1
                for j in range(nbox):
                    if i != 0 and j == 0 and nbox == 3: # if 3 boxes and we aren't on the mainhand, we draw half of one for the first box
                        await self.pasteImage(imgs, "assets/skill.png", (pos[0]+size[0]//2, pos[1]+size[1]+pos_shift+skill_icon_size*j), (size[0]//2, skill_icon_size), transparency=True, start=0, end=2 if (has_skin and j == 0) else 1)
                    else:
                        await self.pasteImage(imgs, "assets/skill.png", (pos[0], pos[1]+size[1]+pos_shift+skill_icon_size*j), (size[0], skill_icon_size), transparency=True, start=0, end=2 if (has_skin and j == 0) else 1)
                # plus
                if export['wp'][i] > 0:
                    # calculate shift of the position if AX and awakening are present
                    if pos_shift != 0:
                        if i > 0: shift = (- size[0]//2, 0)
                        else: shift = (0, pos_shift)
                    else:
                        shift = (0, 0)
                    # draw plus text
                    self.text(imgs, (pos[0]+size[0]-105+shift[0], pos[1]+size[1]-60+shift[1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0), start=0, end=2 if has_skin else 1)
                # skill level
                if export['wl'][i] is not None and export['wl'][i] > 1:
                    self.text(imgs, (pos[0]+skill_icon_size*3-51, pos[1]+size[1]+pos_shift+15), "SL {}".format(export['wl'][i]), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=2 if has_skin else 1)
                if i == 0 or not has_ax or not has_awakening: # don't draw if ax and awakening and not mainhand
                    # skill icon
                    for j in range(3):
                        if export['wsn'][i][j] is not None:
                            if do_opus and self.process_special_weapon(export, i, j): # 3rd skill guessing
                                await self.dlAndPasteImage(imgs, export['wsn'][i][j], (pos[0]+skill_icon_size*j, pos[1]+size[1]+pos_shift), (skill_icon_size, skill_icon_size), start=0, end=2 if has_skin else 1)
                            else:
                                await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (pos[0]+skill_icon_size*j, pos[1]+size[1]+pos_shift), (skill_icon_size, skill_icon_size), start=0, end=2 if has_skin else 1)
                pos_shift += skill_icon_size
                main_ax_icon_size  = int(ax_icon_size * (1.5 if i == 0 else 1) * (0.75 if (has_ax and has_awakening) else 1)) # size of the big AX/Awakening icon
                # ax skills
                if has_ax:
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/augment_skill/{}.png".format(export['waxt'][i][0]), pos, (main_ax_icon_size, main_ax_icon_size), start=0, end=2 if has_skin else 1)
                    for j in range(len(export['waxi'][i])):
                        await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]), (pos[0]+ax_separator*j, pos[1]+size[1]+pos_shift), (skill_icon_size, skill_icon_size), start=0, end=1)
                        self.text(imgs, (pos[0]+ax_separator*j+skill_icon_size+6, pos[1]+size[1]+pos_shift+15), "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
                    pos_shift += skill_icon_size
                # awakening
                if has_awakening:
                    shift = main_ax_icon_size//2 if has_ax else 0 # shift the icon right a bit if also has AX icon
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']), self.add(pos, (shift, 0)), (main_ax_icon_size, main_ax_icon_size), start=0, end=2 if has_skin else 1)
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']), (pos[0]+skill_icon_size, pos[1]+size[1]+pos_shift), (skill_icon_size, skill_icon_size), start=0, end=1)
                    self.text(imgs, (pos[0]+skill_icon_size*3-51, pos[1]+size[1]+pos_shift+15), "LV {}".format(export['wakn'][i]['level']), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)

            if self.sandbox:
                await self.pasteImage(imgs, "assets/sandbox.png", (pos[0], offset[1]+(skill_box_height+sub_size[1])*3), (size[0], int(66*size[0]/159)), transparency=True, start=0, end=1)
            # stats
            pos = (offset[0], offset[1]+bsize[1]+150)
            await self.pasteImage(imgs, "assets/skill.png", (pos[0], pos[1]), (bsize[0], 75), transparency=True, start=0, end=1)
            await self.pasteImage(imgs, "assets/skill.png", (pos[0], pos[1]+75), (bsize[0], 75), transparency=True, start=0, end=1)
            await self.pasteImage(imgs, "assets/atk.png", (pos[0]+9, pos[1]+15), (90, 39), transparency=True, start=0, end=1)
            await self.pasteImage(imgs, "assets/hp.png", (pos[0]+9, pos[1]+15+75), (66, 39), transparency=True, start=0, end=1)
            self.text(imgs, (pos[0]+111, pos[1]+15), "{}".format(export['watk']), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
            self.text(imgs, (pos[0]+111, pos[1]+15+75), "{}".format(export['whp']), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
            await asyncio.sleep(0)

            # estimated damage
            pos = (pos[0]+bsize[0]+15, pos[1]+165)
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
                    await self.pasteImage(imgs, "assets/big_stat.png", (pos[0]-bsize[0]-15, pos[1]+9*2-15), (bsize[0], 150), transparency=True, start=0, end=1)
                    self.text(imgs, (pos[0]-bsize[0], pos[1]+9*2), ("サポーター" if self.japanese else "Support"), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                    if len(export['sps']) > 10: supp = export['sps'][:10] + "..."
                    else: supp = export['sps']
                    self.text(imgs, (pos[0]-bsize[0], pos[1]+9*2+60), supp, fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                else:
                    print("[WPN] |--> Support summon ID is", supp)
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/summon/m/{}.jpg".format(supp), (pos[0]-bsize[0]-15+9, pos[1]), (261, 150), start=0, end=1)
            # weapon grid stats
            est_width = ((size[0]*3)//2)
            for i in range(0, 2):
                await asyncio.sleep(0)
                await self.pasteImage(imgs, "assets/big_stat.png", (pos[0]+est_width*i , pos[1]), (est_width-15, 150), transparency=True, start=0, end=1)
                self.text(imgs, (pos[0]+9+est_width*i, pos[1]+9), "{}".format(export['est'][i+1]), fill=self.COLORS[int(export['est'][0])], font=self.fonts['big'], stroke_width=6, stroke_fill=(0, 0, 0), start=0, end=1)
                if i == 0:
                    self.text(imgs, (pos[0]+est_width*i+15 , pos[1]+90), ("予測ダメ一ジ" if self.japanese else "Estimated"), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                elif i == 1:
                    if int(export['est'][0]) <= 4: vs = (int(export['est'][0]) + 2) % 4 + 1
                    else: vs = (int(export['est'][0]) - 5 + 1) % 2 + 5
                    if self.japanese:
                        self.text(imgs, (pos[0]+est_width*i+15 , pos[1]+90), "対", fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                        self.text(imgs, (pos[0]+est_width*i+54 , pos[1]+90), "{}属性".format(self.COLORS_JP[vs]), fill=self.COLORS[vs], font=self.fonts['medium'], start=0, end=1)
                        self.text(imgs, (pos[0]+est_width*i+162 , pos[1]+90), "予測ダメ一ジ", fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                    else:
                        self.text(imgs, (pos[0]+est_width*i+15 , pos[1]+90), "vs", fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                        self.text(imgs, (pos[0]+est_width*i+66 , pos[1]+90), "{}".format(self.COLORS_EN[vs]), fill=self.COLORS[vs], font=self.fonts['medium'], start=0, end=1)
            # hp gauge
            if do_hp:
                await asyncio.sleep(0)
                hpratio = 100
                for et in export['estx']:
                    if et[0].replace('txt-gauge-num ', '') == 'hp':
                        hpratio = et[1]
                        break
                await self.pasteImage(imgs, "assets/big_stat.png", (pos[0] ,pos[1]), (est_width-15, 150), transparency=True, start=1, end=2)
                if self.japanese:
                    self.text(imgs, (pos[0]+25 , pos[1]+25), "HP{}%".format(hpratio), fill=(255, 255, 255), font=self.fonts['medium'], start=1, end=2)
                else:
                    self.text(imgs, (pos[0]+25 , pos[1]+25), "{}% HP".format(hpratio), fill=(255, 255, 255), font=self.fonts['medium'], start=1, end=2)
                await self.pasteImage(imgs, "assets/hp_bottom.png", (pos[0]+25 , pos[1]+90), (363, 45), transparency=True, start=1, end=2)
                await self.pasteImage(imgs, "assets/hp_mid.png", (pos[0]+25 , pos[1]+90), (int(363*int(hpratio)/100), 45), transparency=True, start=1, end=2, crop=(int(484*int(hpratio)/100), 23))
                await self.pasteImage(imgs, "assets/hp_top.png", (pos[0]+25 , pos[1]+90), (363, 45), transparency=True, start=1, end=2)
                
            return ('weapon', imgs)
        except Exception as e:
            imgs[0].close()
            imgs[1].close()
            return self.pexc(e)

    async def make_modifier(self, export : dict) -> Union[str, tuple]:
        try:
            imgs = [self.make_canvas()]
            print("[MOD] * Drawing Modifiers...")
            if self.babyl:
                offset = (1560, 10)
                limit = [32, 25, 20]
            else:
                offset = (1560, 410)
                limit = [27, 20, 16]
            print("[MOD] |--> Found", len(export['mods']), "modifier(s)...")
            
            # weapon modifier list
            if len(export['mods']) > 0:
                mod_font = ['mini', 'mini', 'small', 'medium']
                mod_off =[15, 15, 27, 15]
                mod_bg_size = [(258, 114), (185, 114), (222, 114), (258, 114)]
                mod_size = [(80, 40), (150, 38), (174, 45), (241, 60)]
                mod_img_off = [(-10, 0), (0, 0), (0, 0), (0, 0)]
                mod_text_off = [(80, 5), (0, 35), (0, 45), (0, 60)]
                mod_step = [42, 66, 84, 105]
                mod_crop = [(68, 34), None, None, None]
                
                # auto sizing
                if len(export['mods']) >= limit[0]: idx = 0 # compact mode
                elif len(export['mods']) >= limit[1]: idx = 1 # smallest size
                elif len(export['mods']) >= limit[2]: idx = 2
                else: idx = 3 # biggest size
                print("[MOD] |--> Display mode:", idx)
                
                await asyncio.sleep(0)
                # background
                await self.pasteImage(imgs, "assets/mod_bg.png", (offset[0]-mod_off[idx], offset[1]-mod_off[idx]//2), mod_bg_size[idx])
                try:
                    await self.pasteImage(imgs, "assets/mod_bg_supp.png", (offset[0]-mod_off[idx], offset[1]-mod_off[idx]+mod_bg_size[idx][1]), (mod_bg_size[idx][0], mod_step[idx] * (len(export['mods'])-1)))
                    await self.pasteImage(imgs, "assets/mod_bg_bot.png", (offset[0]-mod_off[idx], offset[1]+mod_step[idx]*(len(export['mods'])-1)), mod_bg_size[idx])
                except:
                    await self.pasteImage(imgs, "assets/mod_bg_bot.png", (offset[0]-mod_off[idx], offset[1]+50), mod_bg_size[idx])
                offset = (offset[0], offset[1])
                # modifier draw
                for m in export['mods']:
                    await asyncio.sleep(0)
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/weapon_skill_label/" + m['icon_img'], self.add(offset, mod_img_off[idx]), mod_size[idx], transparency=True, crop=mod_crop[idx])
                    self.text(imgs, self.add(offset, mod_text_off[idx]), str(m['value']), fill=((255, 168, 38, 255) if m['is_max'] else (255, 255, 255, 255)), font=self.fonts[mod_font[idx]])
                    offset = (offset[0], offset[1]+mod_step[idx])
            return ('modifier', imgs)
        except Exception as e:
            imgs[0].close()
            return self.pexc(e)

    async def loadEMP(self, id):
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

    async def make_emp(self, export : dict) -> Union[str, tuple]:
        try:
            imgs = [self.make_canvas()]
            print("[EMP] * Drawing EMPs...")
            offset = (15, 0)
            eoffset = (15, 10)
            ersize = (80, 80)
            roffset = (-10, -10)
            rsize = (90, 90)
            # get chara count
            ccount = 0
            if self.babyl:
                nchara = 12 # max number for babyl (mc included)
            else:
                nchara = 5 # max number of allies
            for i in range(0, nchara):
                if self.babyl and i == 0: continue # quirk of babyl party, mc is counted
                if i >= len(export['c']) or export['c'][i] is None: continue
                cid = self.fix_character_look(export, i)
                data = await self.loadEMP(cid.split('_')[0]) # preload and cache emp
                if data is None:
                    print("[EMP] |--> Ally #{}: {}.json can't be loaded".format(i+1, cid.split('_')[0]))
                    continue
                elif self.japanese != (data['lang'] == 'ja'):
                    print("[EMP] |--> Ally #{}: WARNING, language doesn't match".format(i+1))
                ccount += 1
            # set positions and offsets we'll need
            if ccount > 5:
                if ccount > 8: compact = 2
                else: compact = 1
                portrait_type = 's'
                csize = (196, 196)
                shift = 74 if compact == 1 else 0
                esizes = [(104, 104), (77, 77)]
                eroffset = (100, 25)
            else:
                compact = 0
                portrait_type = 'f'
                csize = (207, 432)
                shift = 0
                esizes = [(133, 133), (100, 100)]
                eroffset = (100, 15)
            bg_size = (imgs[0].size[0] - csize[0] - offset[0], csize[1]+shift)
            loffset = self.add(csize, (-150, -50))
            poffset = self.add(csize, (-110, -100))
            pos = self.add(offset, (0, offset[1]-csize[1]-shift))

            # allies
            for i in range(0, nchara):
                await asyncio.sleep(0)
                if self.babyl and i == 0: continue # quirk of babyl party, mc is counted
                if i < len(export['c']) and export['c'][i] is not None:
                    cid = self.fix_character_look(export, i)
                    data = self.emp_cache.get(cid.split('_')[0], None)
                    if data is None: continue
                    pos = self.add(pos, (0, csize[1]+shift)) # set chara position
                    # portrait
                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/npc/{}/{}.jpg".format(portrait_type, cid), pos, csize)
                    # rings
                    if export['cwr'][i] == True:
                        await self.dlAndPasteImage(imgs, "assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", self.add(pos, roffset), rsize, transparency=True)
                    # level
                    self.text(imgs, self.add(pos, loffset), "Lv{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0))
                    # plus
                    if export['cp'][i] > 0:
                        self.text(imgs, self.add(pos, poffset), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0))
                    # background
                    await self.pasteImage(imgs, "assets/bg_emp.png", self.add(pos, (csize[0], 0)), bg_size, transparency=True)
                    # main EMP
                    nemp = len(data['emp'])
                    extra_lb = ""
                    if 'domain' in data and len(data['domain']) > 0: extra_lb = ", Has Domain"
                    elif 'saint' in data and len(data['saint']) > 0: extra_lb = ", Has Yupei"
                    elif 'extra' in data and len(data['extra']) > 0: extra_lb = ", Has Extra EMP"
                    print("[EMP] |--> Ally #{}: {} EMPs, {} Ring EMPs, {}{}".format(i+1, nemp, len(data['ring']), ('{} Lv{}'.format(data['awaktype'], data['awakening'].split('lv')[-1]) if 'awakening' in data else 'Awakening not found'), extra_lb))
                    if nemp > 15: # transcended eternal only (for now)
                        idx = 1
                        off = ((esizes[0][0] - esizes[1][0]) * 5) // 2
                    else:
                        idx = 0
                        off = 0
                    for j, emp in enumerate(data['emp']):
                        await asyncio.sleep(0)
                        if compact:
                            epos = self.add(pos, (csize[0]+15+esizes[idx][0]*j, 5))
                        elif j % 5 == 0: # new line
                            epos = self.add(pos, (csize[0]+15+off, 7+esizes[idx][1]*j//5))
                        else:
                            epos = self.add(epos, (esizes[idx][0], 0))
                        if emp.get('is_lock', False):
                            await self.dlAndPasteImage(imgs, "assets_en/img/sp/zenith/assets/ability/lock.png", epos, esizes[idx])
                        else:
                            await self.dlAndPasteImage(imgs, "assets_en/img/sp/zenith/assets/ability/{}.png".format(emp['image']), epos, esizes[idx])
                            if str(emp['current_level']) != "0":
                                self.text(imgs, self.add(epos, eoffset), str(emp['current_level']), fill=(235, 227, 250), font=self.fonts['medium'] if compact and nemp > 15 else self.fonts['big'], stroke_width=6, stroke_fill=(0, 0, 0))
                            else:
                                await self.pasteImage(imgs, "assets/emp_unused.png", epos, esizes[idx], transparency=True)
                    # ring EMP
                    for j, ring in enumerate(data['ring']):
                        await asyncio.sleep(0)
                        if compact:
                            epos = self.add(pos, (csize[0]+15+(200+ersize[0])*j, csize[1]-ersize[1]-15))
                        else:
                            epos = self.add(pos, (csize[0]+50+off*2+esizes[idx][0]*5, 15+ersize[1]*j))
                        await self.pasteImage(imgs, "assets/{}.png".format(ring['type']['image']), epos, ersize, transparency=True)
                        if compact:
                            self.text(imgs, self.add(epos, eroffset), ring['param']['disp_total_param'], fill=(255, 255, 95), font=self.fonts['small'], stroke_width=6, stroke_fill=(0, 0, 0))
                        else:
                            self.text(imgs, self.add(epos, eroffset), ring['type']['name'] + " " + ring['param']['disp_total_param'], fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
                    if compact != 2:
                        await asyncio.sleep(0)
                        icon_size = (65, 65)
                        icon_index = 1
                        # calc pos
                        if compact:
                            apos1 = (pos[0] + csize[0] + 25, pos[1] + csize[1])
                            apos2 = (pos[0] + csize[0] + 225, pos[1] + csize[1])
                        else:
                            apos1 = (imgs[0].size[0] - 420, pos[1]+20)
                            apos2 = (imgs[0].size[0] - 420, pos[1]+85)
                        # awakening
                        if data.get('awakening', None) is not None:
                            match data['awaktype']:
                                case "Attack"|"攻撃":
                                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/item/npcarousal/s/1.jpg", apos1, icon_size)
                                case "Defense"|"防御":
                                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/item/npcarousal/s/2.jpg", apos1, icon_size)
                                case "Multiattack"|"連続攻撃":
                                    await self.dlAndPasteImage(imgs, "assets_en/img/sp/assets/item/npcarousal/s/3.jpg", apos1, icon_size)
                                case _: # "Balanced"|"バランス"or others
                                    await self.pasteImage(imgs, "assets/bal_awakening.png", apos1, icon_size, transparency=True)
                            self.text(imgs, self.add(apos1, (75, 10)), "Lv" + data['awakening'].split('lv')[-1], fill=(198, 170, 240), font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
                        # domain and other extra upgrades
                        for key in ['domain', 'saint', 'extra']:
                            if key in data and len(data[key]) > 0:
                                extra_txt = ""
                                # set txt, icon and color according to specifics
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
                                                if el[0].endswith(" on"): lv[0] += 1
                                                lv[1] += 1
                                        extra_txt = "{}/{}".format(lv[0], lv[1])
                                    case _:
                                        icon_path = "assets_en/img/sp/ui/icon/skill/skill_job_weapon.png"
                                        text_color = (207, 145, 64)
                                        extra_txt = "Lv" + str(len(data[key]))
                                # add to image
                                await self.dlAndPasteImage(imgs, icon_path, apos2, icon_size)
                                self.text(imgs, self.add(apos2, (75, 10)), extra_txt, fill=text_color, font=self.fonts['medium'], stroke_width=6, stroke_fill=(0, 0, 0))
                                # increase index and move position accordingly
                                # NOTE: Should be unused for now, it's in case they add multiple in the future
                                icon_index += 1
                                if compact:
                                    apos2 = self.add(apos2, (200, 0))
                                else:
                                    if icon_index % 2 == 0:
                                        apos2 = self.add(apos2, (200, -icon_size[1]))
                                    else:
                                        apos2 = self.add(apos2, (0, icon_size[1]))
            return ('emp', imgs)
        except Exception as e:
            imgs[0].close()
            return self.pexc(e)

    def text(self, imgs : list, *args, **kwargs) -> None:
        start = kwargs.pop('start',0)
        end = kwargs.pop('end',9999999999)
        for i in range(start, min(len(imgs), end)):
            ImageDraw.Draw(imgs[i], 'RGBA').text(*args, **kwargs)

    def multiline_text(self, imgs : list, *args, **kwargs) -> None:
        start = kwargs.pop('start',0)
        end = kwargs.pop('end',9999999999)
        for i in range(start, min(len(imgs), end)):
            ImageDraw.Draw(imgs[i], 'RGBA').multiline_text(*args, **kwargs)

    def saveImage(self, img : 'Image', filename : str, resize : Optional[tuple] = None) -> Optional[str]:
        try:
            if resize is not None:
                tmp = img.resize(self.definition)
                tmp.save(filename, "PNG")
                tmp.close()
            else:
                img.save(filename, "PNG")
            print("[OUT] *'{}' has been generated".format(filename))
            return None
        except Exception as e:
            return self.pexc(e)

    def clipboardToJSON(self):
        return json.loads(pyperclip.paste())

    def clean_memory_caches(self):
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

    async def make(self, fast : bool = False) -> bool: # main function
        try:
            if not fast:
                print("Instructions:")
                print("1) Go to the party or EMP screen you want to export")
                print("2) Click the bookmarklet")
                print("3) Come back here and press Return to continue")
                input()
            self.running = True
            # get the data from clipboard
            export = self.clipboardToJSON()
            if export.get('ver', 0) < 1:
                print("Your bookmark is outdated, please update it!")
                self.running = False
                return False
            # start
            if 'emp' in export:
                self.make_sub_emp(export)
            else:
                await self.make_sub_party(export)
                self.saveClasses()
                if self.gbftmr is not None and self.settings.get('gbftmr_use', False):
                    print("Do you want to make a thumbnail with this party? (Y to confirm)")
                    s = input()
                    if s.lower() == "y":
                        try:
                            self.gbftmr.makeThumbnailManual(export)
                        except Exception as xe:
                            print(self.parent.pb.pexc(xe))
                            print("The above exception occured while trying to generate the thumbnail")
            self.running = False
            return True
        except Exception as e:
            print("An error occured")
            print(e)
            print("Did you follow the instructions?")
            self.running = False
            return False

    def applyAlphaComposite(self, base : 'Image', paste : 'Image') -> 'Image':
        res = Image.alpha_composite(base, paste)
        base.close()
        return res

    def completeBaseImages(self, imgs : list, do_skin : bool, resize : Optional[tuple] = None) -> None:
        # party - Merge the images and save the resulting image
        for k in ['summon', 'weapon', 'modifier']:
            imgs['party'][0] = self.applyAlphaComposite(imgs['party'][0], imgs[k][0])
        self.saveImage(imgs['party'][0], "party.png", resize)
        # skin - Merge the images (if enabled) and save the resulting image
        if do_skin:
            tmp = imgs['party'][1]
            imgs['party'][1] = Image.alpha_composite(imgs['party'][0], tmp) # we don't close imgs['party'][0] in case its save process isn't finished
            tmp.close()
            for k in ['summon', 'weapon']:
                imgs['party'][1] = self.applyAlphaComposite(imgs['party'][1], imgs[k][1])
            self.saveImage(imgs['party'][1], "skin.png", resize)

    async def make_sub_party(self, export : dict) -> bool:
        if self.classes is None:
            self.loadClasses()
        self.clean_memory_caches()
        start = time.time()
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
        end = time.time()
        print("* Task completed with success!")
        print("* Ended in {:.2f} seconds".format(end - start))
        return True

    def make_sub_emp(self, export : dict) -> None:
        if 'emp' not in export or 'id' not in export or 'ring' not in export: raise Exception("Invalid EMP data, check your bookmark")
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

    async def settings_menu(self) -> None:
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
            s = input()
            if s == "0":
                v = ({'720p':0, '1080p':1, '4K':2}[self.settings.get('quality', '4k')] + 1) % 4
                self.settings['quality'] = {0:'720p', 1:'1080p', 2:'4K'}.get(v, 0)
            elif s == "1":
                self.settings['caching'] = not self.settings.get('caching', False)
            elif s == "2":
                self.settings['skin'] = not self.settings.get('skin', False)
            elif s == "3":
                self.settings['emp'] = not self.settings.get('emp', False)
            elif s == "4":
                print("Input the url of the asset server to use (Leave blank to cancel): ")
                url = input()
                if url != "":
                    url = url.lower().replace('http://', '').replace('https://', '')
                    if not url.endswith('/'): url += '/'
                    tmp = self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net')
                    self.settings['endpoint'] = url
                    try:
                        await self.retrieveImage("assets_en/img/sp/zenith/assets/ability/1.png", forceDownload=True)
                        print("Asset Server test: Success")
                        print("Asset Server set to:", url)
                    except:
                        self.settings['endpoint'] = tmp
                        print("Asset Server test: Failed")
                        print("Did you input the right url?")
            elif s == "5":
                self.settings['hp'] = not self.settings.get('hp', True)
            elif s == "6":
                self.settings['opus'] = not self.settings.get('opus', False)
            elif s == "7":
                print("Input the path of the GBFTMR folder (Leave blank to cancel): ")
                folder = input()
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
            elif s == "8":
                self.settings['gbftmr_use'] = not self.settings.get('gbftmr_use', False)
            elif s == "9":
                self.emptyCache()
            elif s == "10":
                self.emptyCache()
            else:
                return

    def checkEMP(self) -> None: # check if emp folder exists (and create it if needed)
        if not os.path.isdir('emp'):
            os.mkdir('emp')

    def emptyEMP(self) -> None: # delete the emp folder
        try:
            shutil.rmtree('emp')
            print("Deleted the emp folder")
        except:
            print("Failed to delete the emp folder")

    def checkDiskCache(self) -> None: # check if cache folder exists (and create it if needed)
        if not os.path.isdir('cache'):
            os.mkdir('cache')

    def emptyCache(self) -> None: # delete the cache folder
        try:
            shutil.rmtree('cache')
            print("Deleted the cache folder")
        except:
            print("Failed to delete the cache folder")

    def cpyBookmark(self) -> None:
        # check bookmarklet.txt for a more readable version
        # note: when updating it in this piece of code, you need to double the \
        pyperclip.copy("javascript:(function(){if(window.location.hash.startsWith(\"#party/index/\")||window.location.hash.startsWith(\"#party/expectancy_damage/index\")||window.location.hash.startsWith(\"#tower/party/index/\")||(window.location.hash.startsWith(\"#event/sequenceraid\")&&window.location.hash.indexOf(\"/party/index/\")>0)&&!window.location.hash.startsWith(\"#tower/party/expectancy_damage/index/\")){let obj={ver:1,lang:window.Game.lang,p:parseInt(window.Game.view.deck_model.attributes.deck.pc.job.master.id,10),pcjs:window.Game.view.deck_model.attributes.deck.pc.param.image,ps:[],pce:window.Game.view.deck_model.attributes.deck.pc.param.attribute,c:[],ce:[],ci:[],cb:[window.Game.view.deck_model.attributes.deck.pc.skill.count],cst:[],cn:[],cl:[],cs:[],cp:[],cwr:[],cpl:[window.Game.view.deck_model.attributes.deck.pc.shield_id,window.Game.view.deck_model.attributes.deck.pc.skin_shield_id],fpl:[window.Game.view.deck_model.attributes.deck.pc.familiar_id,window.Game.view.deck_model.attributes.deck.pc.skin_familiar_id],qs:null,cml:window.Game.view.deck_model.attributes.deck.pc.job.param.master_level,cbl:window.Game.view.deck_model.attributes.deck.pc.job.param.perfection_proof_level,s:[],sl:[],ss:[],se:[],sp:[],ssm:window.Game.view.deck_model.attributes.deck.pc.skin_summon_id,w:[],wsm:[window.Game.view.deck_model.attributes.deck.pc.skin_weapon_id,window.Game.view.deck_model.attributes.deck.pc.skin_weapon_id_2],wl:[],wsn:[],wll:[],wp:[],wakn:[],wax:[],waxi:[],waxt:[],watk:window.Game.view.deck_model.attributes.deck.pc.weapons_attack,whp:window.Game.view.deck_model.attributes.deck.pc.weapons_hp,satk:window.Game.view.deck_model.attributes.deck.pc.summons_attack,shp:window.Game.view.deck_model.attributes.deck.pc.summons_hp,est:[window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage_attribute,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_advantage_damage],estx:[],mods:window.Game.view.deck_model.attributes.deck.pc.damage_info.effect_value_info,sps:(window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name?window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name:null),spsid:(Game.view.expectancyDamageData?(Game.view.expectancyDamageData.imageId?Game.view.expectancyDamageData.imageId:null):null)};let qid=JSON.stringify(Game.view.deck_model.attributes.deck.pc.quick_user_summon_id);if(qid!=null){for(const i in Game.view.deck_model.attributes.deck.pc.summons){if(Game.view.deck_model.attributes.deck.pc.summons[i].param!=null&&Game.view.deck_model.attributes.deck.pc.summons[i].param.id==qid){obj.qs=parseInt(i)-1;break}}};try{for(let i=0;i<4-window.Game.view.deck_model.attributes.deck.pc.set_action.length;i++){obj.ps.push(null)}Object.values(window.Game.view.deck_model.attributes.deck.pc.set_action).forEach(e=>{obj.ps.push(e.name?e.name.trim():null)})}catch(error){obj.ps=[null,null,null,null]};if(window.location.hash.startsWith(\"#tower/party/index/\")){Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(x=>{Object.values(x).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.ce.push(e.master?parseInt(e.master.attribute,10):null);obj.ci.push(e.param?e.param.image_id_3:null);obj.cb.push(e.param?e.skill.count:null);obj.cst.push(e.param?e.param.style:1);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null);obj.cn.push(e.master?e.master.short_name:null)})})}else{Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.ce.push(e.master?parseInt(e.master.attribute,10):null);obj.ci.push(e.param?e.param.image_id_3:null);obj.cb.push(e.param?e.skill.count:null);obj.cst.push(e.param?e.param.style:1);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null);obj.cn.push(e.master?e.master.short_name:null)})}Object.values(window.Game.view.deck_model.attributes.deck.pc.summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.sub_summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.weapons).forEach(e=>{obj.w.push(e.master?e.param.image_id:null);obj.wl.push(e.param?parseInt(e.param.skill_level,10):null);obj.wsn.push(e.param?[e.skill1?e.skill1.image:null,e.skill2?e.skill2.image:null,e.skill3?e.skill3.image:null]:null);obj.wll.push(e.param?parseInt(e.param.level,10):null);obj.wp.push(e.param?parseInt(e.param.quality,10):null);obj.wakn.push(e.param?e.param.arousal:null);obj.waxt.push(e.param?e.param.augment_image:null);obj.waxi.push(e.param?e.param.augment_skill_icon_image:null);obj.wax.push(e.param?e.param.augment_skill_info:null)});Array.from(document.getElementsByClassName(\"txt-gauge-num\")).forEach(x=>{obj.estx.push([x.classList[1],x.textContent])});let copyListener=event=>{document.removeEventListener(\"copy\",copyListener,!0);event.preventDefault();let clipboardData=event.clipboardData;clipboardData.clearData();clipboardData.setData(\"text/plain\",JSON.stringify(obj))};document.addEventListener(\"copy\",copyListener,!0);document.execCommand(\"copy\")}else if(window.location.hash.startsWith(\"#zenith/npc\")||window.location.hash.startsWith(\"#tower/zenith/npc\")||/^#event\\/[a-zA-Z0-9]+\\/zenith\\/npc/.test(window.location.hash)){let obj={ver:1,lang:window.Game.lang,id:parseInt(window.Game.view.npcId,10),emp:window.Game.view.bonusListModel.attributes.bonus_list,ring:window.Game.view.npcaugmentData.param_data,awakening:null,awaktype:null,domain:[],saint:[],extra:[]};try{obj.awakening=document.getElementsByClassName(\"prt-current-awakening-lv\")[0].firstChild.className;obj.awaktype=document.getElementsByClassName(\"prt-arousal-form-info\")[0].children[1].textContent;let domains=document.getElementById(\"prt-domain-evoker-list\").getElementsByClassName(\"prt-bonus-detail\");for(let i=0;i<domains.length;++i){obj.domain.push([domains[i].children[0].className,domains[i].children[1].textContent,domains[i].children[2]?domains[i].children[2].textContent:null])}if(document.getElementById(\"prt-shisei-wrapper\").getElementsByClassName(\"prt-progress-gauge\").length>0){let saints=document.getElementById(\"prt-shisei-wrapper\").getElementsByClassName(\"prt-progress-gauge\")[0].getElementsByClassName(\"ico-progress-gauge\");for(let i=0;i<saints.length;++i){obj.saint.push([saints[i].className,null,null])}saints=document.getElementById(\"prt-shisei-wrapper\").getElementsByClassName(\"prt-bonus-detail\");for(let i=0;i<saints.length;++i){obj.saint.push([saints[i].children[0].className,saints[i].children[1].textContent,saints[i].children[2]?saints[i].children[2].textContent:null])}}if(document.getElementsByClassName(\"cnt-extra-lb extra numbers\").length > 0){let extras=document.getElementsByClassName(\"cnt-extra-lb extra numbers\")[0].getElementsByClassName(\"prt-bonus-detail\");for(let i=0;i<extras.length;++i){obj.extra.push([extras[i].children[0].className,extras[i].children[1].textContent,extras[i].children[2]?extras[i].children[2].textContent:null])}}}catch(error){};let copyListener=event=>{document.removeEventListener(\"copy\",copyListener,!0);event.preventDefault();let clipboardData=event.clipboardData;clipboardData.clearData();clipboardData.setData(\"text/plain\",JSON.stringify(obj))};document.addEventListener(\"copy\",copyListener,!0);document.execCommand(\"copy\")}else{alert('Please go to a GBF Party or EMP screen')}}())")

    def importGBFTMR(self, path : str) -> bool:
        try:
            if self.gbftmr is not None: return True
            module_name = "gbftmr.py"

            spec = importlib.util.spec_from_file_location("GBFTMR.gbftmr", path + module_name)
            module = importlib.util.module_from_spec(spec)
            sys.modules["GBFTMR.gbftmr"] = module
            spec.loader.exec_module(module)
            self.gbftmr = module.GBFTMR(path)
            if self.gbftmr.version[0] >= 1 and self.gbftmr.version[1] >= 25:
                return True
            self.gbftmr = None
            return False
        except:
            self.gbftmr = None
            return False

    def cmpVer(self, mver : str, tver : str) -> bool: # compare version strings, True if mver greater or equal, else False
        me = mver.split('.')
        te = tver.split('.')
        for i in range(0, min(len(me), len(te))):
            if int(me[i]) < int(te[i]):
                return False
            elif int(me[i]) > int(te[i]):
                return True
        return True

    async def update_check(self, command_line : bool = True) -> bool:
        interacted = False
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
                                response = await self.client.get("https://github.com/MizaGBF/GBFPIB/archive/refs/heads/main.zip", allow_redirects=True)
                                async with response:
                                    if response.status != 200: raise Exception()
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
                                exit(0)
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

    async def cmd(self) -> None: # old command line menu
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
                    await self.make()
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

    def restart(self) -> None:
        subprocess.Popen([sys.executable] + sys.argv)
        exit(0)

    async def start(self) -> None:
        async with self.init_client():
            if '-fast' in sys.argv:
                await self.make(fast=True)
                if '-nowait' not in sys.argv:
                    print("Closing in 10 seconds...")
                    time.sleep(10)
            elif '-cmd' in sys.argv:
                await self.update_check(True)
                await self.cmd()
            else:
                await self.update_check()
                await (Interface(asyncio.get_event_loop(), self).run())

class GBFTMR_Select(Tk.Tk):
    def __init__(self, interface : 'Interface', loop, export : dict) -> None:
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.interface = interface
        self.loop = loop
        self.export = export
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
        
        self.options = None
        self.optelems = []
        self.update_UI()
        self.apprunning = True
        self.result = False
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    async def run(self) -> bool:
        while self.apprunning:
            self.update()
            await asyncio.sleep(0.02)
        try: self.destroy()
        except: pass
        return self.result

    def update_UI(self, *args) -> None:
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

    async def confirm(self) -> None:
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
            await asyncio.to_thread(self.interface.pb.gbftmr.makeThumbnail, self.options["settings"], self.options["template"])
            self.result = True
        except Exception as e:
            print(self.interface.pb.pexc(e))
            self.interface.events.append(("Error", "An error occured, impossible to generate the thumbnail"))
        self.apprunning = False

    def cancel(self) -> None:
        self.apprunning = False

class Interface(Tk.Tk): # interface
    BW = 15
    BH = 1
    def __init__(self, loop, pb : PartyBuilder) -> None:
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.loop = loop
        self.pb = pb
        self.apprunning = True
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

    async def run(self) -> None:
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

    def close(self) -> None: # called by the app when closed
        self.apprunning = False

    async def build(self) -> None:
        if self.process_running:
            messagebox.showinfo("Info", "Wait for the current process to finish")
            return
        await self.make()

    async def make(self, thumbnailOnly : bool = False) -> None:
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
                    tasks.append(tg.create_task(self.pb.make_sub_party(export)))
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

    def add_emp(self) -> None:
        try:
            self.pb.make_sub_emp(self.pb.clipboardToJSON())
            self.events.append(("Info", "EMP saved with success"))
        except:
            self.events.append(("Error", "An error occured, did you press the bookmark?"))

    def bookmark(self) -> None:
        self.pb.cpyBookmark()
        messagebox.showinfo("Info", "Bookmarklet copied!\nTo setup on chrome:\n1) Make a new bookmark (of GBF for example)\n2) Right-click and edit\n3) Change the name if you want\n4) Paste the code in the url field")

    def qual_changed(self, *args) -> None:
        self.pb.settings['quality'] = args[0]

    def toggleCaching(self) -> None:
        self.pb.settings['caching'] = (self.cache_var.get() != 0)
        
    def toggleSkin(self) -> None:
        self.pb.settings['skin'] = (self.skin_var.get() != 0)

    def toggleEMP(self) -> None:
        self.pb.settings['emp'] = (self.emp_var.get() != 0)

    def toggleUpdate(self) -> None:
        self.pb.settings['update'] = (self.update_var.get() != 0)

    def toggleHP(self) -> None:
        self.pb.settings['hp'] = (self.hp_var.get() != 0)

    def toggleOpus(self) -> None:
        self.pb.settings['opus'] = (self.opus_var.get() != 0)

    def toggleGBFTMR(self) -> None:
        self.pb.settings['gbftmr_use'] = (self.gbftmr_var.get() != 0)

    async def setserver(self) -> None:
        url = simpledialog.askstring("Set Asset Server", "Input the URL of the Asset Server to use\nLeave blank to reset to the default setting.")
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

    def setGBFTMR(self) -> None:
        folder_selected = filedialog.askdirectory(title="Select the GBFTMR folder")
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

    async def runGBFTMR(self) -> None:
        if self.pb.gbftmr:
            if self.process_running:
                messagebox.showinfo("Info", "Wait for the current process to finish")
                return
            await self.make(True)
        else:
            self.events.append(("Error", "GBFTMR isn't loaded"))

    async def update_check(self) -> None:
        if not await self.pb.update_check():
            messagebox.showinfo("Info", "GBFPIB is up to date")

if __name__ == "__main__":
    asyncio.run(PartyBuilder('-debug' in sys.argv).start())