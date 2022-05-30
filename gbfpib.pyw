from urllib import request, parse
from urllib.parse import quote
import json
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import pyperclip
import re
import sys
import time
import os
import base64
import tkinter as Tk
import tkinter.ttk as ttk
from tkinter import messagebox
import threading
import concurrent.futures
from multiprocessing import Manager
import shutil

class PartyBuilder():
    def __init__(self, ver):
        self.version = ver
        self.japanese = False # True if the data is japanese, False if not
        self.prev_lang = None # Language used in the previous run
        self.babyl = False # True if the data contains more than 5 allies
        self.sandbox = False # True if the data contains more than 10 weapons
        manager = Manager()
        self.cache = manager.dict() # memory cache
        self.lock = manager.Lock() # lock object for cache
        self.sumcache = manager.dict()# wiki summon cache
        self.fonts = {'small':None, 'medium':None, 'big':None, 'mini':None} # font to use during the processing
        self.quality = 1 # quality ratio in use currently
        self.definition = None # image size
        self.running = False # True if the image building is in progress
        self.nullchar = [3030182000, 3020072000] # null character id list (lyria, cat...), need to be hardcoded
        self.colors = { # color for estimated advantage
            1:(243, 48, 33),
            2:(85, 176, 250),
            3:(227, 124, 32),
            4:(55, 232, 16),
            5:(253, 216, 67),
            6:(176, 84, 251)
        }
        self.color_strs = { # color string
            1:"Fire",
            2:"Water",
            3:"Earth",
            4:"Wind",
            5:"Light",
            6:"Dark"
        }
        self.color_strs_jp = { # color string
            1:"火",
            2:"水",
            3:"土",
            4:"風",
            5:"光",
            6:"闇"
        }
        self.color_awakening = { # color for awakening string
            "Balanced" : (211, 193, 148),
            "Attack" : (255, 121, 90),
            "Defense" : (133, 233, 245),
            "Multiattack" : (255, 255, 95)
        }
        self.color_awakening_jp = { # color for awakening string
            "バランス" : (211, 193, 148),
            "攻撃" : (255, 121, 90),
            "防御" : (133, 233, 245),
            "連続攻撃" : (255, 255, 95)
        }
        self.classes = { # class prefix (gotta add them manually, sadly)
            10: 'sw',
            11: 'sw',
            12: 'wa',
            13: 'wa',
            14: 'kn',
            15: 'sw',
            16: 'me',
            17: 'bw',
            18: 'mc',
            19: 'sp',
            30: 'sw',
            41: 'ax',
            42: 'sp',
            43: 'me',
            44: 'bw',
            45: 'sw',
            20: 'kn',
            21: 'kt',
            22: 'kt',
            23: 'sw',
            24: 'gu',
            25: 'wa',
            26: 'kn',
            27: 'mc',
            28: 'kn',
            29: 'gu'
        }
        self.aux_class = [100401, 300301, 300201] # aux classes
        self.supp_summon_re = [ # regex used for the wiki support summon id search
            re.compile('(20[0-9]{8})\\.'),
            re.compile('(20[0-9]{8}_02)\\.')
        ]
        self.dummy_layer = self.make_canvas()
        self.settings = {} # settings.json data
        self.load() # loading settings.json

    def load(self): # load settings.json
        try:
            with open('settings.json') as f:
                self.settings = json.load(f)
        except Exception as e:
            print("Failed to load settings.json")
            while True:
                print("An empty settings.json file will be created, continue? (y/n)")
                i = input()
                if i.lower() == 'n': exit(0)
                elif i.lower() == 'y': break
                self.save()

    def save(self): # save settings.json
        try:
            with open('settings.json', 'w') as outfile:
                json.dump(self.settings, outfile)
        except:
            pass

    def retrieveImage(self, path, remote=True):
        if self.japanese: path = path.replace('assets_en', 'assets')
        with self.lock:
            if path not in self.cache:
                try: # get from disk cache if enabled
                    if self.settings.get('caching', False):
                        with open("cache/" + base64.b64encode(path.encode('utf-8')).decode('utf-8'), "rb") as f:
                            self.cache[path] = f.read()
                    else:
                        raise Exception()
                except: # else request it from gbf
                    if remote:
                        print("[GET] *Downloading File", path)
                        req = request.Request(path)
                        path_handle = request.urlopen(req)
                        self.cache[path] = path_handle.read()
                        if self.settings.get('caching', False):
                            try:
                                with open("cache/" + base64.b64encode(path.encode('utf-8')).decode('utf-8'), "wb") as f:
                                    f.write(self.cache[path])
                            except Exception as e:
                                print(e)
                                pass
                        path_handle.close()
                    else:
                        with open(path, "rb") as f:
                            self.cache[path] = f.read()
            return self.cache[path]

    def pasteImage(self, imgs, file, offset, resize=None, transparency=False, start=0, end=99999999): # paste an image onto another
        if isinstance(file, str):
            if self.japanese: file = file.replace('_EN', '')
            file = BytesIO(self.retrieveImage(file, remote=False))
        buffers = [Image.open(file)]
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
        for buf in buffers: buf.close()
        del buffers
        file.close()
        return imgs

    def dlAndPasteImage(self, imgs, url, offset, resize=None, transparency=False, start=0, end=99999999): # dl an image and call pasteImage()
        with BytesIO(self.retrieveImage(url)) as file_jpgdata:
            return self.pasteImage(imgs, file_jpgdata, offset, resize, transparency, start, end)

    def addTuple(self, A:tuple, B:tuple):
        return (A[0]+B[0], A[1]+B[1])

    def subTuple(self, A:tuple, B:tuple):
        return (A[0]-B[0], A[1]-B[1])

    def fixCase(self, terms): # function to fix the case (for wiki search requests)
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

    def get_support_summon(self, sps): # search on gbf.wiki to match a summon name to its id
        try:
            if sps in self.sumcache: return self.sumcache[sps]
            req = request.Request("https://gbf.wiki/" + quote(self.fixCase(sps)))
            url_handle = request.urlopen(req)
            data = url_handle.read().decode('utf-8')
            url_handle.close()
            group = self.supp_summon_re[1].findall(data)
            if len(group) > 0:
                self.sumcache[sps] = group[0]
                return group[0]
            group = self.supp_summon_re[0].findall(data)
            self.sumcache[sps] = group[0]
            return group[0]
        except:
            if "(summon)" not in sps.lower():
                return self.get_support_summon(sps + ' (Summon)')
            else:
                try:
                    return self.advanced_support_summon_search(sps.replace(' (Summon)', ''))
                except:
                    pass
            return None

    def advanced_support_summon_search(self, summon_name): # advanced search on gbf.wiki to match a summon name to its id
        try:
            req = request.Request("https://gbf.wiki/index.php?title=Special:Search&search=" + quote(summon_name))
            url_handle = request.urlopen(req)
            data = url_handle.read().decode('utf-8')
            url_handle.close()
            cur = 0
            while True: # iterate search results for an id
                x = data.find("<div class='searchresult'>ID ", cur)
                if x == -1: break
                x += len("<div class='searchresult'>ID ")
                if 'title="Demi ' not in data[cur:x]: # skip demi optimus
                    return data[x:x+10]
                cur = x
            return None
        except Exception as e:
            print(e)
            return None

    def get_uncap_id(self, cs): # to get character portraits based on uncap levels
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def get_mc_job_look(self, skin, job): # get the MC unskined filename based on id
        jid = job // 10000
        if jid not in self.classes: return skin
        return "{}_{}_{}".format(job, self.classes[jid], '_'.join(skin.split('_')[2:]))

    def make_canvas(self, size=(3600, 4320)):
        i = Image.new('RGB', size, "black")
        im_a = Image.new("L", size, "black")
        i.putalpha(im_a)
        im_a.close()
        return i

    def make_party(self, export):
        try:
            imgs = [self.make_canvas(), self.make_canvas()]
            print("[CHA] * Drawing Party...")
            # version number
            self.text(imgs, (3420, 0), self.version, fill=(150, 150, 150, 60), font=self.fonts['mini'])
            if self.babyl:
                offset = (30, 20)
                nchara = 12
                csize = (360, 360)
                skill_width = 840
                pos = self.addTuple(offset, (60, 0))
                jsize = (108, 90)
                roffset = (-12, -12)
                rsize = (120, 120)
                poffset = self.addTuple(csize, (-210, -90))
                ssoffset = self.addTuple(pos, (0, 20+csize[1]))
                stoffset = self.addTuple(ssoffset, (6, 6))
                plsoffset = self.addTuple(ssoffset, (894, 0))
                # background
                self.pasteImage(imgs, "assets/bg.png", self.addTuple(pos, (-30, -30)), (csize[0]*8+80, csize[1]*2+110), transparency=True, start=0, end=1)
            else:
                offset = (30, 10)
                nchara = 5
                csize = (500, 500)
                skill_width = 840
                pos = self.addTuple(offset, (skill_width-csize[0], 0))
                jsize = (144, 120)
                roffset = (-20, -20)
                rsize = (180, 180)
                poffset = self.addTuple(csize, (-220, -80))
                noffset = (18, csize[1]+20)
                loffset = (20, csize[1]+12+120)
                ssoffset = self.addTuple(offset, (0, csize[1]))
                stoffset = self.addTuple(ssoffset, (6, 6))
                plsoffset = self.addTuple(ssoffset, (0, -300))
                # background
                self.pasteImage(imgs, "assets/bg.png", self.addTuple(pos, (-30, -20)), (50+csize[0]*6+60, csize[1]+350), transparency=True, start=0, end=1)
            
            # mc
            print("[CHA] |--> MC Skin:", export['pcjs'])
            print("[CHA] |--> MC Job:", export['p'])
            # class
            class_id = self.get_mc_job_look(export['pcjs'], export['p'])
            self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/s/{}.jpg".format(class_id), pos, csize, start=0, end=1)
            # job icon
            self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, jsize, transparency=True, start=0, end=1)
            # skin
            if class_id != export['pcjs']:
                self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/s/{}.jpg".format(export['pcjs']), pos, csize, start=1, end=2)
                self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, jsize, transparency=True, start=1, end=2)

            # allies
            for i in range(0, nchara):
                if self.babyl:
                    if i < 4: pos = self.addTuple(offset, (csize[0]*i+60, 0))
                    elif i < 8: pos = self.addTuple(offset, (csize[0]*i+80, 0))
                    else: pos = self.addTuple(offset, (csize[0]*(i-4)+80, 20+csize[1]*(i//8)))
                    if i == 0: continue # quirk of babyl party, mc is counted
                else:
                    pos = self.addTuple(offset, (skill_width+csize[0]*(i+1-1), 0))
                    if i >= 3: pos = self.addTuple(pos, (50, 0))
                # portrait
                if i >= len(export['c']) or export['c'][i] is None:
                    self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/tower/assets/npc/s/3999999999.jpg", pos, csize, start=0, end=1)
                    continue
                else:
                    print("[CHA] |--> Ally #{}:".format(i+1), export['c'][i], export['cn'][i], "Lv {}".format(export['cl'][i]), "+{}".format(export['cp'][i]), "Has Ring" if export['cwr'][i] else "No Ring")
                    # portrait
                    if export['c'][i] in self.nullchar: 
                        cid = "{}_{}_0{}".format(export['c'][i], self.get_uncap_id(export['cs'][i]), export['ce'][i])
                    else:
                        cid = "{}_{}".format(export['c'][i], self.get_uncap_id(export['cs'][i]))
                    self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/s/{}.jpg".format(cid), pos, csize, start=0, end=1)
                    # skin
                    if cid != export['ci'][i]:
                        self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/s/{}.jpg".format(export['ci'][i]), pos, csize, start=1, end=2)
                        has_skin = True
                    else:
                        has_skin = False
                # rings
                if export['cwr'][i] == True:
                    self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", self.addTuple(pos, roffset), rsize, transparency=True, start=0, end=2 if has_skin else 1)
                # plus
                if export['cp'][i] > 0:
                    self.text(imgs, self.addTuple(pos, poffset), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.fonts['small'], stroke_width=12, stroke_fill=(0, 0, 0), start=0, end=2 if has_skin else 1)
                if not self.babyl:
                    # name
                    self.pasteImage(imgs, "assets/chara_stat.png", self.addTuple(pos, (0, csize[1])), (csize[0], 120), transparency=True, start=0, end=1)
                    if len(export['cn'][i]) > 11: name = export['cn'][i][:11] + ".."
                    else: name = export['cn'][i]
                    self.text(imgs, self.addTuple(pos, noffset), name, fill=(255, 255, 255), font=self.fonts['mini'], start=0, end=1)
                    # level
                    self.pasteImage(imgs, "assets/chara_stat.png", self.addTuple(pos, (0, csize[1]+120)), (csize[0], 120), transparency=True, start=0, end=1)
                    self.text(imgs, self.addTuple(pos, loffset), "Lv {}".format(export['cl'][i]), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)

            # mc sub skills
            self.pasteImage(imgs, "assets/subskills.png", ssoffset, (840, 294), transparency=True)
            count = 0
            for i in range(len(export['ps'])):
                if export['ps'][i] is not None:
                    print("[CHA] |--> MC Skill #{}:".format(i), export['ps'][i])
                    self.text(imgs, self.addTuple(stoffset, (0, 96*count)), export['ps'][i], fill=(255, 255, 255), font=self.fonts['small'] if (len(export['ps'][i]) > 15) else self.fonts['medium'])
                    count += 1
            # paladin shield
            if export['cpl'] is not None:
                print("[CHA] |--> Paladin shield:".format(i), export['cpl'])
                self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/shield/s/{}.jpg".format(export['cpl']), plsoffset, (300, 300))
            elif self.babyl: # to fill the blank space
                self.pasteImage(imgs, "assets/characters_EN.png", self.addTuple(ssoffset, (skill_width, 0)), (552, 150), transparency=True)
            return ('party', imgs)
        except Exception as e:
            imgs[0].close()
            imgs[1].close()
            return e

    def make_summon(self, export):
        try:
            imgs = [self.make_canvas(), self.make_canvas()]
            print("[SUM] * Drawing Summons...")
            offset = (340, 850)
            sizes = [(543, 944), (532, 400), (547, 310)]
            durls = ["http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/2999999999.jpg","http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/2999999999.jpg", "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/2999999999.jpg"]
            surls = ["http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/party_main/{}.jpg", "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/party_sub/{}.jpg", "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg"]

            # background setup
            self.pasteImage(imgs, "assets/bg.png", self.addTuple(offset, (-30, -30)), (200+sizes[0][0]+sizes[1][0]*2+sizes[0][0]+96, sizes[0][1]+286), transparency=True, start=0, end=1)

            for i in range(0, 7):
                if i == 0:
                    pos = self.addTuple(offset, (0, 0)) 
                    idx = 0
                elif i < 5:
                    pos = self.addTuple(offset, (sizes[0][0]+100+((i-1)%2)*sizes[1][0]+36, 532*((i-1)//2)))
                    idx = 1
                else:
                    pos = self.addTuple(offset, (sizes[0][0]+200+2*sizes[1][0]+36, 204+(i-5)*(sizes[2][1]+120)))
                    idx = 2
                    if i == 5: self.pasteImage(imgs, "assets/subsummon_EN.png", (pos[0]+90, pos[1]-144-60), (360, 144), transparency=True, start=0, end=1)
                # portraits
                if export['s'][i] is None:
                    self.dlAndPasteImage(imgs, durls[idx], pos, sizes[idx], start=0, end=1)
                    continue
                else:
                    print("[SUM] |--> Summon #{}:".format(i+1), export['ss'][i], "Uncap Lv{}".format(export['se'][i]), "Lv{}".format(export['sl'][i]))
                    self.dlAndPasteImage(imgs, surls[idx].format(export['ss'][i]), pos, sizes[idx], start=0, end=1)
                # main summon skin
                if i == 0 and export['ssm'] is not None:
                    self.dlAndPasteImage(imgs, surls[idx].format(export['ssm']), pos, sizes[idx], start=1, end=2)
                    self.pasteImage(imgs, "assets/skin.png", self.addTuple(pos, (sizes[idx][0]-170, 30)), (153, 171), start=1, end=2)
                    has_skin = True
                else:
                    has_skin = False
                # star
                self.pasteImage(imgs, "assets/star_{}.png".format({3:1, 4:2, 5:3, 6:3, 7:3}.get(export['se'][i], 0)), pos, (132, 132), transparency=True, start=0, end=2 if has_skin else 1)
                # level
                self.pasteImage(imgs, "assets/chara_stat.png", self.addTuple(pos, (0, sizes[idx][1])), (sizes[idx][0], 120), transparency=True, start=0, end=1)
                self.text(imgs, self.addTuple(pos, (12,sizes[idx][1]+18)), "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
                # plus
                if export['sp'][i] > 0:
                    self.text(imgs, (pos[0]+sizes[idx][0]-190, pos[1]+sizes[idx][1]-100), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0), start=0, end=2 if has_skin else 1)

            # stats
            spos = self.addTuple(offset, (sizes[0][0]+100+36, sizes[0][1]+120))
            self.pasteImage(imgs, "assets/chara_stat.png",  spos, (sizes[1][0]*2, 120), transparency=True, start=0, end=1)
            self.pasteImage(imgs, "assets/atk.png", self.addTuple(spos, (18, 18)), (180, 78), transparency=True, start=0, end=1)
            self.pasteImage(imgs, "assets/hp.png", self.addTuple(spos, (sizes[1][0]+18, 18)), (132, 78), transparency=True, start=0, end=1)
            self.text(imgs, self.addTuple(spos, (240, 18)), "{}".format(export['satk']), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
            self.text(imgs, self.addTuple(spos, (sizes[1][0]+160, 18)), "{}".format(export['shp']), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
            return ('summon', imgs)
        except Exception as e:
            imgs[0].close()
            imgs[1].close()
            return e

    def make_weapon(self, export):
        try:
            imgs = [self.make_canvas(), self.make_canvas()]
            print("[WPN] * Drawing Weapons...")
            if self.sandbox: offset = (50, 2100)
            else: offset = (340, 2100)
            skill_box_height = 288
            skill_icon_size = 144
            ax_icon_size = 192
            ax_separator = skill_box_height
            mh_size = (600, 1260)
            sub_size = (576, 330)
            self.pasteImage(imgs, "assets/grid_bg.png", self.addTuple(offset, (-30, -30)), (mh_size[0]+(4 if self.sandbox else 3)*sub_size[0]+120, 2520+(480 if self.sandbox else 0)), transparency=True, start=0, end=1)
            if self.sandbox:
                self.pasteImage(imgs, "assets/grid_bg_extra.png", (offset[0]+mh_size[0]+60+sub_size[0]*3, offset[1]), (576, 2290), transparency=True, start=0, end=1)

            for i in range(0, len(export['w'])):
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
                    pos = (offset[0]+bsize[0]+60+size[0]*x, offset[1]+(size[1]+skill_box_height)*y)
                else: # others
                    x = (i-1) % 3
                    y = (i-1) // 3
                    size = sub_size
                    pos = (offset[0]+bsize[0]+60+size[0]*x, offset[1]+(size[1]+skill_box_height)*y)
                # dual blade class
                if i <= 1 and export['p'] in self.aux_class:
                    self.pasteImage(imgs, ("assets/mh_dual.png" if i == 0 else "assets/aux_dual.png"), self.addTuple(pos, (-5, -5)), self.addTuple(size, (10, 10+skill_box_height)), transparency=True, start=0, end=1)
                # portrait
                if export['w'][i] is None or export['wl'][i] is None:
                    if i >= 10:
                        self.pasteImage(imgs, "assets/arca_slot.png", pos, size, start=0, end=1)
                    else:
                        self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt), pos, size, start=0, end=1)
                    continue
                else:
                    # ax and awakening check
                    has_ax = len(export['waxt'][i]) > 0
                    has_awakening = (export['wakn'][i] is not None and export['wakn'][i]['is_arousal_weapon'])
                    pos_shift = - skill_icon_size if (has_ax and has_awakening) else 0  # vertical shift of the skill boxes (if both ax and awk are presents)
                    # portrait draw
                    print("[WPN] |--> Weapon #{}".format(i+1), str(export['w'][i])+"00", ", AX:", has_ax, ", Awakening:", has_awakening)
                    self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/{}00.jpg".format(wt, export['w'][i]), pos, size, start=0, end=1)
                # skin
                has_skin = False
                if i <= 1 and export['wsm'][i] is not None:
                    if i == 0 or (i == 1 and export['p'] in self.aux_class): # aux class check for 2nd weapon
                        self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/{}.jpg".format(wt, export['wsm'][i]), pos, size, start=1, end=2)
                        self.pasteImage(imgs, "assets/skin.png", self.addTuple(pos, (size[0]-153, 0)), (153, 171), transparency=True, start=1, end=2)
                        has_skin = True
                # skill box
                nbox = 1 # number of skill boxes to draw
                if has_ax: nbox += 1
                if has_awakening: nbox += 1
                for j in range(nbox):
                    if i != 0 and j == 0 and nbox == 3: # if 3 boxes and we aren't on the mainhand, we draw half of one for the first box
                        self.pasteImage(imgs, "assets/skill.png", (pos[0]+size[0]//2, pos[1]+size[1]+pos_shift+skill_icon_size*j), (size[0]//2, skill_icon_size), transparency=True, start=0, end=2 if (has_skin and j == 0) else 1)
                    else:
                        self.pasteImage(imgs, "assets/skill.png", (pos[0], pos[1]+size[1]+pos_shift+skill_icon_size*j), (size[0], skill_icon_size), transparency=True, start=0, end=2 if (has_skin and j == 0) else 1)
                # plus
                if export['wp'][i] > 0:
                    # calculate shift of the position if AX and awakening are present
                    if pos_shift != 0:
                        if i > 0: shift = (- size[0]//2, 0)
                        else: shift = (0, pos_shift)
                    else:
                        shift = (0, 0)
                    # draw plus text
                    self.text(imgs, (pos[0]+size[0]-210+shift[0], pos[1]+size[1]-120+shift[1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0), start=0, end=2 if has_skin else 1)
                # skill level
                if export['wl'][i] is not None and export['wl'][i] > 1:
                    self.text(imgs, (pos[0]+skill_icon_size*3-102, pos[1]+size[1]+pos_shift+30), "SL {}".format(export['wl'][i]), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=2 if has_skin else 1)
                if i == 0 or not has_ax or not has_awakening: # don't draw if ax and awakening and not mainhand
                    # skill icon
                    for j in range(3):
                        if export['wsn'][i][j] is not None:
                            self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (pos[0]+skill_icon_size*j, pos[1]+size[1]+pos_shift), (skill_icon_size, skill_icon_size), start=0, end=2 if has_skin else 1)
                pos_shift += skill_icon_size
                main_ax_icon_size  = int(ax_icon_size * (1.5 if i == 0 else 1) * (0.75 if (has_ax and has_awakening) else 1)) # size of the big AX/Awakening icon
                # ax skills
                if has_ax:
                    self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment_skill/{}.png".format(export['waxt'][i][0]), pos, (main_ax_icon_size, main_ax_icon_size), start=0, end=2 if has_skin else 1)
                    for j in range(len(export['waxi'][i])):
                        self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]), (pos[0]+ax_separator*j, pos[1]+size[1]+pos_shift), (skill_icon_size, skill_icon_size), start=0, end=1)
                        self.text(imgs, (pos[0]+ax_separator*j+skill_icon_size+12, pos[1]+size[1]+pos_shift+30), "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)
                    pos_shift += skill_icon_size
                # awakening
                if has_awakening:
                    shift = main_ax_icon_size//2 if has_ax else 0 # shift the icon right a bit if also has AX icon
                    self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']), self.addTuple(pos, (shift, 0)), (main_ax_icon_size, main_ax_icon_size), start=0, end=2 if has_skin else 1)
                    self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']), (pos[0]+skill_icon_size, pos[1]+size[1]+pos_shift), (skill_icon_size, skill_icon_size), start=0, end=1)
                    self.text(imgs, (pos[0]+skill_icon_size*3-102, pos[1]+size[1]+pos_shift+30), "LV {}".format(export['wakn'][i]['level']), fill=(255, 255, 255), font=self.fonts['small'], start=0, end=1)

            if self.sandbox:
                self.pasteImage(imgs, "assets/sandbox.png", (pos[0], offset[1]+(skill_box_height+sub_size[1])*3), (size[0], int(66*size[0]/159)), transparency=True, start=0, end=1)
            # stats
            pos = (offset[0], offset[1]+bsize[1]+300)
            self.pasteImage(imgs, "assets/skill.png", (pos[0], pos[1]), (bsize[0], 150), transparency=True, start=0, end=1)
            self.pasteImage(imgs, "assets/skill.png", (pos[0], pos[1]+150), (bsize[0], 150), transparency=True, start=0, end=1)
            self.pasteImage(imgs, "assets/atk.png", (pos[0]+18, pos[1]+30), (180, 78), transparency=True, start=0, end=1)
            self.pasteImage(imgs, "assets/hp.png", (pos[0]+18, pos[1]+60+150), (132, 78), transparency=True, start=0, end=1)
            self.text(imgs, (pos[0]+222, pos[1]+30), "{}".format(export['watk']), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
            self.text(imgs, (pos[0]+222, pos[1]+30+150), "{}".format(export['whp']), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)

            # estimated damage
            pos = (pos[0]+bsize[0]+30, pos[1]+330)
            if export['sps'] is not None and export['sps'] != '':
                # support summon
                if export['spsid'] is not None:
                    supp = export['spsid']
                else:
                    supp = self.get_support_summon(export['sps'])
                if supp is None:
                    print("[WPN] |--> Support summon is", export['sps'], "(Note: searching its ID on gbf.wiki failed)")
                    self.pasteImage(imgs, "assets/big_stat.png", (pos[0]-bsize[0]-30, 330), (bsize[0], 300), transparency=True, start=0, end=1)
                    self.text(imgs, (pos[0]-bsize[0]-30+30 , pos[1]+18*2), ("サポーター" if self.japanese else "Support"), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                    if len(export['sps']) > 10: supp = export['sps'][:10] + "..."
                    else: supp = export['sps']
                    self.text(imgs, (pos[0]-bsize[0]-30+30 , pos[1]+18*2+120), supp, fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                else:
                    print("[WPN] |--> Support summon ID is", supp)
                    self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(supp), (pos[0]-bsize[0]-30+18, pos[1]), (522, 300), start=0, end=1)
            # weapon grid stats
            est_width = ((size[0]*3)//2)
            for i in range(0, 2):
                self.pasteImage(imgs, "assets/big_stat.png", (pos[0]+est_width*i , pos[1]), (est_width-30, 300), transparency=True, start=0, end=1)
                self.text(imgs, (pos[0]+18+est_width*i, pos[1]+18), "{}".format(export['est'][i+1]), fill=self.colors[int(export['est'][0])], font=self.fonts['big'], stroke_width=12, stroke_fill=(0, 0, 0), start=0, end=1)
                if i == 0:
                    self.text(imgs, (pos[0]+est_width*i+30 , pos[1]+180), ("予測ダメ一ジ" if self.japanese else "Estimated"), fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                elif i == 1:
                    if int(export['est'][0]) <= 4: vs = (int(export['est'][0]) + 2) % 4 + 1
                    else: vs = (int(export['est'][0]) - 5 + 1) % 2 + 5
                    if self.japanese:
                        self.text(imgs, (pos[0]+est_width*i+30 , pos[1]+180), "対", fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                        self.text(imgs, (pos[0]+est_width*i+108 , pos[1]+180), "{}属性".format(self.color_strs_jp[vs]), fill=self.colors[vs], font=self.fonts['medium'], start=0, end=1)
                        self.text(imgs, (pos[0]+est_width*i+324 , pos[1]+180), "予測ダメ一ジ", fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                    else:
                        self.text(imgs, (pos[0]+est_width*i+30 , pos[1]+180), "vs", fill=(255, 255, 255), font=self.fonts['medium'], start=0, end=1)
                        self.text(imgs, (pos[0]+est_width*i+132 , pos[1]+180), "{}".format(self.color_strs[vs]), fill=self.colors[vs], font=self.fonts['medium'], start=0, end=1)
            return ('weapon', imgs)
        except Exception as e:
            imgs[0].close()
            imgs[1].close()
            return e

    def make_modifier(self, export):
        try:
            imgs = [self.make_canvas()]
            print("[MOD] * Drawing Modifiers...")
            if self.babyl:
                offset = (3120, 20)
                limit = (25, 20)
            else:
                offset = (3120, 830)
                limit = (21, 16)
            print("[MOD] |--> Found", len(export['mods']), "modifier(s)...")
            # weapon modifiers
            if len(export['mods']) > 0:
                mod_font = ['mini', 'small', 'medium']
                mod_off =[30, 54, 30]
                mod_bg_size = [(370, 228), (444, 228), (516, 228)]
                mod_size = [(300, 77), (348, 90), (462, 120)]
                mod_text_off = [(70, 132), (90, 168), (120, 210)]
                
                if len(export['mods']) >= limit[0]: idx = 0 # smallest size for more mods
                elif len(export['mods']) >= limit[1]: idx = 1
                else: idx = 2 # biggest size
                
                self.pasteImage(imgs, "assets/mod_bg.png", (offset[0]-mod_off[idx], offset[1]-mod_off[idx]//2), mod_bg_size[idx])
                self.pasteImage(imgs, "assets/mod_bg_supp.png", (offset[0]-mod_off[idx], offset[1]-mod_off[idx]+mod_bg_size[idx][1]), (mod_bg_size[idx][0], mod_text_off[idx][1] * (len(export['mods'])-1)))
                self.pasteImage(imgs, "assets/mod_bg_bot.png", (offset[0]-mod_off[idx], offset[1]+mod_off[idx]+mod_text_off[idx][1]*(len(export['mods'])-1)), mod_bg_size[idx])
                for m in export['mods']:
                    self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/weapon_skill_label/" + m['icon_img'], offset, mod_size[idx], transparency=True)
                    self.text(imgs, (offset[0], offset[1]+mod_text_off[idx][0]), str(m['value']), fill=((255, 168, 38, 255) if m['is_max'] else (255, 255, 255, 255)), font=self.fonts[mod_font[idx]])
                    offset = (offset[0], offset[1]+mod_text_off[idx][1])
            return ('modifier', imgs)
        except Exception as e:
            imgs[0].close()
            return e

    def loadEMP(self, id):
        try:
            with open("emp/{}.json".format(id), mode="r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    def make_emp(self, export):
        try:
            imgs = [self.make_canvas()]
            print("[EMP] * Drawing Extended Masteries...")
            offset = (30, 0)
            eoffset = (30, 20)
            ersize = (160, 160)
            roffset = (-20, -20)
            rsize = (180, 180)
            # check the number of character in the party
            ccount = 0
            if self.babyl:
                nchara = 12 # max number for babyl (mc included)
            else:
                nchara = 5 # max number of allies
            for i in range(0, nchara):
                if self.babyl and i == 0: continue # quirk of babyl party, mc is counted
                if i >= len(export['c']) or export['c'][i] is None: continue
                ccount += 1
            print("[EMP] *", ccount, "character(s) to draw")
            # set positions and offsets we'll need
            if ccount > 5:
                if ccount > 8: compact = 2
                else: compact = 1
                portrait_type = 's'
                csize = (392, 392)
                shift = 148 if compact == 1 else 0
                esizes = [(208, 208), (155, 155)]
                eroffset = (200, 50)
            else:
                compact = 0
                portrait_type = 'f'
                csize = (415, 864)
                shift = 0
                esizes = [(266, 266), (200, 200)]
                eroffset = (200, 30)
            bg_size = (imgs[0].size[0] - csize[0] - offset[0], csize[1]+shift)
            poffset = self.addTuple(csize, (-220, -100))
            pos = self.addTuple(offset, (0, offset[1]-csize[1]-shift))

            # allies
            for i in range(0, nchara):
                if self.babyl and i == 0: continue # quirk of babyl party, mc is counted
                if i < len(export['c']) and export['c'][i] is not None:
                    pos = self.addTuple(pos, (0, csize[1]+shift)) # set chara position
                    print("[EMP] |--> Ally #{}".format(i+1))
                    # portrait
                    if export['c'][i] in self.nullchar: 
                        cid = "{}_{}_0{}".format(export['c'][i], self.get_uncap_id(export['cs'][i]), export['ce'][i])
                    else:
                        cid = "{}_{}".format(export['c'][i], self.get_uncap_id(export['cs'][i]))
                    self.dlAndPasteImage(imgs, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/{}/{}.jpg".format(portrait_type, cid), pos, csize)
                    # rings
                    if export['cwr'][i] == True:
                        self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", self.addTuple(pos, roffset), rsize, transparency=True)
                    # plus
                    if export['cp'][i] > 0:
                        self.text(imgs, self.addTuple(pos, poffset), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.fonts['small'], stroke_width=12, stroke_fill=(0, 0, 0))
                    # background
                    self.pasteImage(imgs, "assets/bg_emp.png".format(cid), self.addTuple(pos, (csize[0], 0)), bg_size, transparency=True)
                    # load EMP file
                    data = self.loadEMP(export['c'][i])
                    if data is None or self.japanese != (data['lang'] == 'ja'): # skip if we can't find EMPs OR if the language doesn't match
                        print("[EMP] |----> {}.json can't be loaded".format(export['c'][i]))
                        self.text(imgs, self.addTuple(pos, (csize[0]+100, csize[1]//3)), "EMP not set", fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0))
                        continue
                    # main EMP
                    nemp = len(data['emp'])
                    print("[EMP] |----> {} EMPs".format(nemp))
                    if nemp > 15: # transcended eternal only (for now)
                        idx = 1
                        off = ((esizes[0][0] - esizes[1][0]) * 5) // 2
                    else:
                        idx = 0
                        off = 0
                    for j, emp in enumerate(data['emp']):
                        if compact:
                            epos = self.addTuple(pos, (csize[0]+30+esizes[idx][0]*j, 10))
                        elif j % 5 == 0: # new line
                            epos = self.addTuple(pos, (csize[0]+30+off, 15+esizes[idx][1]*j//5))
                        else:
                            epos = self.addTuple(epos, (esizes[idx][0], 0))
                        if emp.get('is_lock', False):
                            self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/zenith/assets/ability/lock.png", epos, esizes[idx])
                        else:
                            self.dlAndPasteImage(imgs, "http://game-a.granbluefantasy.jp/assets_en/img/sp/zenith/assets/ability/{}.png".format(emp['image']), epos, esizes[idx])
                            if str(emp['current_level']) != "0":
                                self.text(imgs, self.addTuple(epos, eoffset), str(emp['current_level']), fill=(235, 227, 250), font=self.fonts['medium'] if compact and nemp > 15 else self.fonts['big'], stroke_width=12, stroke_fill=(0, 0, 0))
                            else:
                                self.pasteImage(imgs, "assets/emp_unused.png", epos, esizes[idx], transparency=True)
                    # ring EMP
                    print("[EMP] |----> {} Ring EMPs".format(len(data['ring'])))
                    for j, ring in enumerate(data['ring']):
                        if compact:
                            epos = self.addTuple(pos, (csize[0]+30+(400+ersize[0])*j, csize[1]-ersize[1]-30))
                        else:
                            epos = self.addTuple(pos, (csize[0]+100+off*2+esizes[idx][0]*5, 30+ersize[1]*j))
                        self.pasteImage(imgs, "assets/{}.png".format(ring['type']['image']), epos, ersize, transparency=True)
                        if compact:
                            self.text(imgs, self.addTuple(epos, eroffset), ring['param']['disp_total_param'], fill=(255, 255, 95), font=self.fonts['small'], stroke_width=12, stroke_fill=(0, 0, 0))
                        else:
                            self.text(imgs, self.addTuple(epos, eroffset), ring['type']['name'] + " " + ring['param']['disp_total_param'], fill=(255, 255, 95), font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0))
                    if compact != 2:
                        # calc pos
                        if compact:
                            apos1 = (pos[0] + csize[0] + 50, pos[1] + csize[1])
                            apos2 = (pos[0] + csize[0] + 850, pos[1] + csize[1])
                        else:
                            apos1 = (imgs[0].size[0] - 800, pos[1]+40)
                            apos2 = (imgs[0].size[0] - 800, pos[1]+150)
                        # awakening
                        if data.get('awakening', None) is not None:
                            print("[EMP] |----> Awakening", data['awakening'].split('lv')[-1], data['awaktype'])
                            if self.japanese:
                                self.text(imgs, apos1, data['awaktype'] + "Lv" + data['awakening'].split('lv')[-1], fill=self.color_awakening_jp[data['awaktype']], font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0))
                            else:
                                self.text(imgs, apos1, data['awaktype'] + " Lv" + data['awakening'].split('lv')[-1], fill=self.color_awakening[data['awaktype']], font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0))
                        else:
                            print("[EMP] |----> Awakening not set! Consider updating.")
                        # domain
                        if data.get('domain', None) is not None:
                            if len(data['domain']) > 0:
                                dlv = 0
                                for d in data['domain']:
                                    if d[2] is not None: dlv += 1
                                if self.japanese:
                                    self.text(imgs, apos2,"至賢Lv" + str(dlv), fill=(100, 210, 255), font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0))
                                else:
                                    self.text(imgs, apos2,"Domain Lv" + str(dlv), fill=(100, 210, 255), font=self.fonts['medium'], stroke_width=12, stroke_fill=(0, 0, 0))
                        else:
                            print("[EMP] |----> Domain not set! Consider updating.")
            return ('emp', imgs)
        except Exception as e:
            imgs[0].close()
            return e

    def text(self, imgs, *args, **kwargs):
        start = kwargs.pop('start',0)
        end = kwargs.pop('end',9999999999)
        for i in range(start, min(len(imgs), end)):
            ImageDraw.Draw(imgs[i], 'RGBA').text(*args, **kwargs)

    def saveImage(self, img, filename, resize):
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
            return e

    def clipboardToJSON(self):
        return json.loads(pyperclip.paste())

    def make(self, fast=False): # main function
        try:
            if not fast:
                print("Instructions:")
                print("1) Go to the party or EMP screen you want to export")
                print("2) Click the corresponding bookmarklet")
                print("3) Come back here and press Return to continue")
                input()
            self.running = True
            export = self.clipboardToJSON() # get the data from clipboard
            if 'emp' in export: self.make_sub_emp(export)
            else: self.make_sub_party(export)
            self.running = False
            return True
        except Exception as e:
            print("An error occured")
            print("exception message:", e)
            print("Did you follow the instructions?")
            self.running = False
            return False

    def AlphaCompositeAndClose(self, base, paste):
        res = Image.alpha_composite(base, paste)
        base.close()
        return res

    def make_sub_party(self, export):
        do_emp = self.settings.get('emp', False)
        do_skin = self.settings.get('skin', True)
        if self.settings.get('caching', False):
            self.checkDiskCache()
        self.quality = {'720p':1/6, '1080p':1/4, '4k':1/2, '8k':1}.get(self.settings.get('quality', '8K').lower(), 1)
        self.definition = {'720p':(600, 720), '1080p':(900, 1080), '4k':(1800, 2160), '8k':(3600, 4320)}.get(self.settings.get('quality', '8K').lower(), (3600, 4320))
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
                self.fonts['big'] = ImageFont.truetype("assets/font_japanese.ttf", 144, encoding="unic")
                self.fonts['medium'] = ImageFont.truetype("assets/font_japanese.ttf", 72, encoding="unic")
                self.fonts['small'] = ImageFont.truetype("assets/font_japanese.ttf", 66, encoding="unic")
                self.fonts['mini'] = ImageFont.truetype("assets/font_japanese.ttf", 54, encoding="unic")
            else:
                self.fonts['big'] = ImageFont.truetype("assets/font_english.ttf", 180, encoding="unic")
                self.fonts['medium'] = ImageFont.truetype("assets/font_english.ttf", 96, encoding="unic")
                self.fonts['small'] = ImageFont.truetype("assets/font_english.ttf", 84, encoding="unic")
                self.fonts['mini'] = ImageFont.truetype("assets/font_english.ttf", 72, encoding="unic")
        self.prev_lang = self.japanese
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
            print("* Preparing Canvas...")
            imgs = {}
            print("* Starting Threads...")
            futures = []
            futures_save = []
            if do_emp: # only start if enabled
                futures.append(executor.submit(self.make_emp, export))
            futures.append(executor.submit(self.make_party, export))
            futures.append(executor.submit(self.make_summon, export))
            futures.append(executor.submit(self.make_weapon, export))
            futures.append(executor.submit(self.make_modifier, export))
            res = []
            for future in concurrent.futures.as_completed(futures):
                res.append(future.result())
            gen_done = False # flag to check if party and skin final image generation started
            for r in res:
                if isinstance(r, tuple):
                    imgs[r[0]] = r[1]
                else:
                    raise r
                # as soon as available, we start generating the final images while the EMP are being made
                if not gen_done and 'party' in imgs and 'summon' in imgs and 'weapon' in imgs and 'modifier' in imgs:
                    gen_done = True
                    # party - Merge the images and save the resulting image
                    imgs['party'][0] = self.AlphaCompositeAndClose(imgs['party'][0], imgs['summon'][0])
                    imgs['summon'][0].close()
                    imgs['party'][0] = self.AlphaCompositeAndClose(imgs['party'][0], imgs['weapon'][0])
                    imgs['weapon'][0].close()
                    imgs['party'][0] = self.AlphaCompositeAndClose(imgs['party'][0], imgs['modifier'][0])
                    imgs['modifier'][0].close()
                    futures_save.append(executor.submit(self.saveImage, imgs['party'][0], "party.png", resize))
                    # skin - Merge the images (if enabled) and save the resulting image
                    if do_skin:
                        tmp = imgs['party'][1]
                        imgs['party'][1] = Image.alpha_composite(imgs['party'][0], tmp) # we don't close imgs['party'][0] in case its save process isn't finished
                        tmp.close()
                        imgs['party'][1] = self.AlphaCompositeAndClose(imgs['party'][1], imgs['summon'][1])
                        imgs['party'][1] = self.AlphaCompositeAndClose(imgs['party'][1], imgs['weapon'][1])
                        futures_save.append(executor.submit(self.saveImage, imgs['party'][1], "skin.png", resize))
                    imgs['summon'][1].close()
                    imgs['weapon'][1].close()
            # emp - save the resulting image (if enabled)
            if do_emp:
                futures_save.append(executor.submit(self.saveImage, imgs['emp'][0], "emp.png", resize))
            res = []
            for future in concurrent.futures.as_completed(futures_save):
                res.append(future.result())
            for r in res:
                if r is not None: raise r

            for i in imgs['party']: i.close()
            for i in imgs.get('emp', []): i.close()

        print("* Task completed with success!")

    def make_sub_emp(self, export):
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
            print("* Domain Lvl", len(export['domain']))
        self.checkEMP()
        with open('emp/{}.json'.format(export['id']), mode='w', encoding="utf-8") as outfile:
            json.dump(export, outfile)
        print("* Task completed with success!")

    def settings_menu(self):
        while True:
            print("")
            print("Settings:")
            print("[0] Change quality ( Current:", self.settings.get('quality', '720p'),")")
            print("[1] Enable Disk Caching ( Current:", self.settings.get('caching', False),")")
            print("[2] Generate skin.png ( Current:", self.settings.get('skin', True),")")
            print("[3] Generate emp.png ( Current:", self.settings.get('emp', False),")")
            print("[4] Empty Cache")
            print("[5] Empty EMP")
            print("[Any] Back")
            s = input()
            if s == "0":
                v = ({'720p':0, '1080p':1, '4K':2, '8K':3}[self.settings.get('quality', '720p')] + 1) % 4
                self.settings['quality'] = {0:'720p', 1:'1080p', 2:'4K', 3:'8K'}.get(v, 0)
            elif s == "1":
                self.settings['caching'] = not self.settings.get('caching', False)
            elif s == "2":
                self.settings['skin'] = not self.settings.get('skin', False)
            elif s == "3":
                self.settings['emp'] = not self.settings.get('emp', False)
            elif s == "4":
                self.emptyCache()
            elif s == "5":
                self.emptyCache()
            else:
                return

    def checkEMP(self): # check if emp folder exists (and create it if needed)
        if not os.path.isdir('emp'):
            os.mkdir('emp')

    def emptyEMP(self): # delete the emp folder
        try:
            shutil.rmtree('emp')
            print("Deleted the emp folder")
        except:
            print("Failed to delete the emp folder")

    def checkDiskCache(self): # check if cache folder exists (and create it if needed)
        if not os.path.isdir('cache'):
            os.mkdir('cache')

    def emptyCache(self): # delete the cache folder
        try:
            shutil.rmtree('cache')
            print("Deleted the cache folder")
        except:
            print("Failed to delete the cache folder")

    def cpyBookmark(self):
        # check bookmarklet.txt for a more readable version
        # note: when updating it in this piece of code, you need to double the \
        pyperclip.copy("javascript:(function(){if(window.location.hash.startsWith(\"#party/index/\")||window.location.hash.startsWith(\"#party/expectancy_damage/index\")||window.location.hash.startsWith(\"#tower/party/index/\")||(window.location.hash.startsWith(\"#event/sequenceraid\")&&window.location.hash.indexOf(\"/party/index/\")>0)&&!window.location.hash.startsWith(\"#tower/party/expectancy_damage/index/\")){let obj={lang:window.Game.lang,p:parseInt(window.Game.view.deck_model.attributes.deck.pc.job.master.id,10),pcjs:window.Game.view.deck_model.attributes.deck.pc.param.image,ps:[],c:[],ce:[],ci:[],cn:[],cl:[],cs:[],cp:[],cwr:[],cpl:window.Game.view.deck_model.attributes.deck.pc.shield_id,s:[],sl:[],ss:[],se:[],sp:[],ssm:window.Game.view.deck_model.attributes.deck.pc.skin_summon_id,w:[],wsm:[window.Game.view.deck_model.attributes.deck.pc.skin_weapon_id, window.Game.view.deck_model.attributes.deck.pc.skin_weapon_id_2],wl:[],wsn:[],wll:[],wp:[],wakn:[],wax:[],waxi:[],waxt:[],watk:window.Game.view.deck_model.attributes.deck.pc.weapons_attack,whp:window.Game.view.deck_model.attributes.deck.pc.weapons_hp,satk:window.Game.view.deck_model.attributes.deck.pc.summons_attack,shp:window.Game.view.deck_model.attributes.deck.pc.summons_hp,est:[window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage_attribute,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_advantage_damage],mods:window.Game.view.deck_model.attributes.deck.pc.damage_info.effect_value_info,sps:(window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name?window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name:null),spsid:(Game.view.expectancyDamageData?(Game.view.expectancyDamageData.summonId?Game.view.expectancyDamageData.summonId:null):null)};try{for(let i=0;i<4-window.Game.view.deck_model.attributes.deck.pc.set_action.length;i++){obj.ps.push(null)}Object.values(window.Game.view.deck_model.attributes.deck.pc.set_action).forEach(e=>{obj.ps.push(e.name?e.name.trim():null)})}catch(error){obj.ps=[null,null,null,null]};if(window.location.hash.startsWith(\"#tower/party/index/\")){Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(x=>{Object.values(x).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.ce.push(e.master?parseInt(e.master.attribute,10):null);obj.ci.push(e.param?e.param.image_id_3:null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null);obj.cn.push(e.master?e.master.short_name:null)})})}else{Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.ce.push(e.master?parseInt(e.master.attribute,10):null);obj.ci.push(e.param?e.param.image_id_3:null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null);obj.cn.push(e.master?e.master.short_name:null)})}Object.values(window.Game.view.deck_model.attributes.deck.pc.summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.sub_summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.weapons).forEach(e=>{obj.w.push(e.master?parseInt(e.master.id.slice(0,-2),10):null);obj.wl.push(e.param?parseInt(e.param.skill_level,10):null);obj.wsn.push(e.param?[e.skill1?e.skill1.image:null,e.skill2?e.skill2.image:null,e.skill3?e.skill3.image:null]:null);obj.wll.push(e.param?parseInt(e.param.level,10):null);obj.wp.push(e.param?parseInt(e.param.quality,10):null);obj.wakn.push(e.param?e.param.arousal:null);obj.waxt.push(e.param?e.param.augment_image:null);obj.waxi.push(e.param?e.param.augment_skill_icon_image:null);obj.wax.push(e.param?e.param.augment_skill_info:null)});let copyListener=event=>{document.removeEventListener(\"copy\",copyListener,true);event.preventDefault();let clipboardData=event.clipboardData;clipboardData.clearData();clipboardData.setData(\"text/plain\",JSON.stringify(obj))};document.addEventListener(\"copy\",copyListener,true);document.execCommand(\"copy\");} else if(window.location.hash.startsWith(\"#zenith/npc\")||window.location.hash.startsWith(\"#tower/zenith/npc\")){let obj={lang:window.Game.lang,id:parseInt(window.Game.view.npcId,10),emp:window.Game.view.bonusListModel.attributes.bonus_list,ring:window.Game.view.npcaugmentData.param_data,awakening:null,awaktype:null,domain:[]};try{obj.awakening=document.getElementsByClassName(\"prt-current-awakening-lv\")[0].firstChild.className;obj.awaktype=document.getElementsByClassName(\"prt-arousal-form-info\")[0].children[1].textContent;domains = document.getElementById(\"prt-domain-evoker-list\").getElementsByClassName(\"prt-bonus-detail\");for(let i=0;i<domains.length;++i){obj.domain.push([domains[i].children[0].className, domains[i].children[1].textContent, domains[i].children[2]?domains[i].children[2].textContent:null]);}}catch(error){};let copyListener=event=>{document.removeEventListener(\"copy\",copyListener,true);event.preventDefault();let clipboardData=event.clipboardData;clipboardData.clearData();clipboardData.setData(\"text/plain\",JSON.stringify(obj))};document.addEventListener(\"copy\",copyListener,true);document.execCommand(\"copy\");}else{alert('Please go to a GBF Party or EMP screen');}}())")

    def run(self): # old command line menu
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
                    self.make()
                elif s == "1":
                    self.cpyBookmark()
                    print("Bookmarklet copied!")
                    print("To setup on chrome:")
                    print("1) Make a new bookmark (of GBF for example)")
                    print("2) Right-click and edit")
                    print("3) Change the name if you want")
                    print("4) Paste the code in the url field")
                elif s == "2":
                    self.settings_menu()
                    self.save()
                else:
                    self.save()
                    return
            except Exception as e:
                print(e)
                self.save()
                return

class Interface(Tk.Tk): # interface
    def __init__(self, pb, ver):
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.pb = pb
        self.apprunning = True
        self.iconbitmap('icon.ico')
        self.title("GBFPIB {}".format(ver))
        self.resizable(width=False, height=False) # not resizable
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.to_disable = []
        
        # run part
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=0, rowspan=2, sticky="we")
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Run")
        Tk.Button(tabcontent, text="Build Images", command=self.build).grid(row=0, column=0, sticky="we")
        Tk.Button(tabcontent, text="Add EMP", command=self.add_emp).grid(row=1, column=0, sticky="we")
        Tk.Button(tabcontent, text="Bookmark", command=self.bookmark).grid(row=2, column=0, sticky="we")
        
        # setting part
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=1, rowspan=2, sticky="we")
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Settings")
        self.qual_variable = Tk.StringVar(self)
        options = ['720p', '1080p', '4K', '8K']
        self.qual_variable.set(self.pb.settings.get('quality', options[0]))
        Tk.Label(tabcontent, text="Quality").grid(row=0, column=0)
        opt = Tk.OptionMenu(tabcontent, self.qual_variable, *options, command=self.qual_changed)
        opt.grid(row=0, column=1)
        self.to_disable.append(opt)
        
        self.cache_var = Tk.IntVar(value=self.pb.settings.get('caching', False))
        Tk.Label(tabcontent, text="Caching").grid(row=1, column=0)
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.cache_var, command=self.toggleCaching))
        self.to_disable[-1].grid(row=1, column=1)
        self.skin_var = Tk.IntVar(value=self.pb.settings.get('skin', True))
        Tk.Label(tabcontent, text="Do Skins").grid(row=2, column=0)
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.skin_var, command=self.toggleSkin))
        self.to_disable[-1].grid(row=2, column=1)
        self.emp_var = Tk.IntVar(value=self.pb.settings.get('emp', False))
        Tk.Label(tabcontent, text="Do EMP").grid(row=3, column=0)
        self.to_disable.append(Tk.Checkbutton(tabcontent, variable=self.emp_var, command=self.toggleEMP))
        self.to_disable[-1].grid(row=3, column=1)
        
        # other
        self.status = Tk.Label(self, text="Starting")
        self.status.grid(row=0, column=0, sticky="w")
        
        self.thread = None
        self.events = []

    def run(self):
        # main loop
        run_flag = False
        while self.apprunning:
            if len(self.events) > 0:
                ev = self.events.pop(0)
                if ev[0] == "Info": messagebox.showinfo(ev[0], ev[1])
                elif ev[0] == "Error": messagebox.showerror(ev[0], ev[1])
            if self.thread is None:
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
            time.sleep(0.02)

    def close(self): # called by the app when closed
        self.pb.save()
        self.apprunning = False
        self.destroy() # destroy the window

    def build(self):
        if self.thread is not None:
            messagebox.showinfo("Info", "Wait for the current processing to finish")
            return
        self.thread = threading.Thread(target=self.buildThread)
        self.thread.daemon = True
        self.thread.start()

    def buildThread(self):
        try:
            self.pb.make_sub_party(self.pb.clipboardToJSON())
            self.events.append(("Info", "Image(s) generated with success"))
        except:
            self.events.append(("Error", "An error occured, did you press the Party bookmark before starting?"))
        self.thread = None

    def add_emp(self):
        try:
            self.pb.make_sub_emp(self.pb.clipboardToJSON())
            self.events.append(("Info", "EMP saved with success"))
        except:
            self.events.append(("Error", "An error occured, did you press the EMP bookmark before starting?"))

    def bookmark(self):
        self.pb.cpyBookmark()
        messagebox.showinfo("Info", "Bookmarklet copied!\nTo setup on chrome:\n1) Make a new bookmark (of GBF for example)\n2) Right-click and edit\n3) Change the name if you want\n4) Paste the code in the url field")

    def qual_changed(self, *args):
        self.pb.settings['quality'] = args[0]

    def toggleCaching(self):
        self.pb.settings['caching'] = (self.cache_var.get() != 0)
        
    def toggleSkin(self):
        self.pb.settings['skin'] = (self.skin_var.get() != 0)

    def toggleEMP(self):
        self.pb.settings['emp'] = (self.emp_var.get() != 0)

# entry point
if __name__ == "__main__":
    ver = "v7.12"
    if '-fast' in sys.argv:
        print("Granblue Fantasy Party Image Builder", ver)
        pb = PartyBuilder(ver)
        pb.make(fast=True)
        if '-nowait' not in sys.argv:
            print("Closing in 10 seconds...")
            time.sleep(10)
    elif '-cmd' in sys.argv:
        print("Granblue Fantasy Party Image Builder", ver)
        pb = PartyBuilder(ver)
        pb.run()
    else:
        ui = Interface(PartyBuilder(ver), ver)
        ui.run()