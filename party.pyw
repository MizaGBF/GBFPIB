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
import shutil

class PartyBuilder():
    def __init__(self):
        self.japanese = False # True if the data is japanese, False if not
        self.big_font = None # font size 30
        self.font = None # font size 16
        self.small_font = None # font size 14
        self.cache = {} # image cache
        self.sumcache = {} # wiki summon cache
        self.nullchar = [3030182000, 3020072000] # null character id list (lyria, cat...)
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
        self.base = { # list of size/offset for a 720p image
            'font': [14, 16, 30], # font size
            'font_jp': [11, 12, 24], # font size (japanese)
            'stroke_width': 2, # text stroke width
            'base': (600, 720), # base image size
            'party_header': (10, 10), # party header position
            'summon_header': (10, 150), # summon header position
            'weapon_header': (10, 320), # wpn grid header position
            'header_size': (92, 25), # size of the above image headers
            'party_pos': (5, 20), # position of the party section
            'party_babyl_pos': (30, -18), # position of the party section (babyl mode)
            'summon_pos': (120, 180), # position of the summon section
            'weapon_pos': (10, 355), # position of the wpn grid section
            'chara_size': (66, 120), # size of a character portrait
            'chara_size_babyl': (56, 56), # size of a character portrait (babyl mode)
            'chara_plus_babyl_offset': (-35, -15), # offset of the plus mark text (babyl mode)
            'chara_pos_babyl_offset': 10, # offset of the character position (babyl mode)
            'skill_width': 140, # width of the MC subskill text box
            'bg_offset': -5, # offset used by the party background
            'bg_end_offset': (10, 40), # offset used for the bottom of the background (party)
            'bg_end_offset2': (10, 56), # offset used for the bottom of the background (summon)
            'bg_end_offset3': (20, 420), # offset used for the bottom of the background (wpn grid)
            'bg_end_offset4': (20, 500), # offset used for the bottom of the background ((wpn grid)
            'job_size': (24, 20), # size of the job icon
            'job_size_babyl': (18, 15), # size of the job icon (babyl mode)
            'ring_size': (30, 30), # size of the ring icon
            'ring_size_babyl': (20, 20), # size of the ring icon (babyl mode)
            'ring_offset': -2, # offset of the ring icon
            'chara_plus_offset': (-40, -20), # offset of the plus mark text
            'stat_height': 20, # height of the bg used for chara lvl text
            'text_offset': (4, 2), # lvl text offset
            'sub_skill_bg': (140, 49), # subskill background size
            'sub_skill_text_off': 1, # subskill text offset
            'sub_skill_text_space': 16, # subskill text space from one line to another
            'star_size': (22, 22), # size of summon star icon
            'summon_size': (60, 126), # size of summon portrait
            'summon_sub_size': (60, 34), # size of sub summon portrait
            'summon_plus_offset': (-35, -20), # summon plus mark text offset
            'sum_level_text_off': (2, 3), # summon lvl text offset
            'sum_atk_size': (30, 13), # summon atk icon size
            'sum_hp_size': (22, 13), # summon hp icon size
            'sum_stat_offsets': [3, 30, 40, 100], # offset for summon atk and hp icons
            'summon_off': 10, # summon offset
            'skill_box_height': 48, # height of a weapon skills
            'ax_box_height': 32, # height of an AX weapon skills
            'mh_size': (100, 210), # size of the mainhand image
            'sub_size': (96, 55), # size of the sub weapon images
            'wpn_separator': 5, # separation in pixel between weapons
            'weapon_plus_offset': (-35, -20), # offset of weapon plus mark text
            'skill_lvl_off': [-17, 5], # offset of weapon skill level text
            'ax_text_off': [2, 5], # offset of ax skill text
            'wpn_stat_off': 50, # offset of grid stat
            'wpn_stat_line': 25, # height of grid stat
            'wpn_atk_size': (30, 13), # size of grid atk icon
            'wpn_hp_size': (22, 13), # size of grid sum icon
            'wpn_stat_text_off': (3, 5), # offset of grid stat text
            'wpn_stat_text_off2': (37, 5), # offset of grid stat text (2nd one)
            'estimate_off': (5, 55), # estimate offset
            'big_stat': (-5, 50), # size of estimate background
            'est_text': 3, # estimate text offset
            'est_sub_text': (5, 30), # estimate text offset
            'est_sub_text_ele': 22, # estimate text offset (element)
            'est_sub_text_jp': (54, 30), # estimate text offset (japanese)
            'est_sub_text_ele_jp': 18, # estimate text offset (element) (japanese)
            'supp_summon': (87, 50), # support summon size
            'supp_summon_off': 6, # support summon offset
            'mod_off': 8, # wpn modifier offset
            'mod_bg_size': (74, 38), # wpn modifier background (top part) size
            'mod_bg_supp_size': 74, # wpn modifier background (main part) width
            'mod_size': (58, 15), # wpn modifieer icon size
            'mod_text_off': [15, 28], # wpn modifier text offset
            'mod_off_big': 5, # wpn modifier offset (bigger version)
            'mod_bg_size_big': (86, 38), # wpn modifier background (top part) size (bigger version)
            'mod_bg_supp_size_big': 86, # wpn modifier background (main part) width (bigger version)
            'mod_size_big': (80, 20), # wpn modifieer icon size (bigger version)
            'mod_text_off_big': [20, 35], # wpn modifier text offset (bigger version)
            'extra_sum_size': (60, 24), # extra summon size
            'extra_sum_off': 10 # extra summon offset
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
        self.qual = {'720p': 1, '1080p': 1.5, '4K': 3, '8K': 6} # quality modifier, self.base will be copied and multiplied by that
        self.supp_summon_re = [ # regex used for the wiki support summon id search
            re.compile('(20[0-9]{8})\\.'),
            re.compile('(20[0-9]{8}_02)\\.')
        ]
        self.last = "" # last used quality
        self.last_val = None # will contain the last modified copy of self.base
        self.data = {} # settings.json data
        self.load() # loading settings.json

    def load(self): # load settings.json
        try:
            with open('settings.json') as f:
                self.data = json.load(f)
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
                json.dump(self.data, outfile)
        except:
            pass

    def build_quality(self): # copy self.base and apply the quality modifier
        if self.data.get('quality', '720p') == self.last: return self.last_val # if it's the last used quality, do nothing
        print("Caching size for quality", self.data.get('quality', '720p'))
        val = {}
        mod = self.qual[self.data.get('quality', '720p')]
        if mod == 1: # no modification, just copy
            val = self.base.copy()
        else: # iterate and multiply
            for k in self.base:
                if isinstance(self.base[k], int): val[k] = int(self.base[k]*mod)
                elif isinstance(self.base[k], tuple):
                    tmp = []
                    for i in self.base[k]:
                        tmp.append(int(i*mod))
                    val[k] = tuple(tmp)
                elif isinstance(self.base[k], list):
                    tmp = []
                    for i in self.base[k]:
                        tmp.append(int(i*mod))
                    val[k] = tmp
                else: raise Exception("Internal error")
        # update last quality used
        self.last = self.data.get('quality', '720p')
        self.last_val = val
        return val

    def pasteImage(self, img, file, offset, resize=None): # paste an image onto another
        if self.japanese and isinstance(file, str):
            file = file.replace('_EN', '')
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize, Image.LANCZOS))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    def dlAndPasteImage(self, img, url, offset, resize=None): # dl an image and call pasteImage()
        if self.japanese: url = url.replace('assets_en', 'assets')
        if url not in self.cache:
            try: # get from disk cache if enabled
                if self.data.get('caching', False):
                    with open("cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "rb") as f:
                        self.cache[url] = f.read()
                else:
                    raise Exception()
            except: # else request it from gbf
                req = request.Request(url)
                url_handle = request.urlopen(req)
                self.cache[url] = url_handle.read()
                if self.data.get('caching', False):
                    try:
                        with open("cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "wb") as f:
                            f.write(self.cache[url])
                    except Exception as e:
                        print(e)
                        pass
                url_handle.close()
        with BytesIO(self.cache[url]) as file_jpgdata:
            self.pasteImage(img, file_jpgdata, offset, resize)

    def checkDiskCache(self): # check if cache folder exists (and create it if needed)
        if not os.path.isdir('cache'):
            os.mkdir('cache')

    def emptyCache(self): # delete the cache  folder
        try:
            shutil.rmtree('cache')
            print("Deleted the cache folder")
        except:
            print("Failed to delete the cache folder")

    def draw_rect(self, d, x, y, w, h): # unused, for debug/dev purpose
        d.rectangle([(x, y), (x+w-1, y+h-1)], fill=(0, 0, 0, 200))

    def fixCase(self, terms): # function to fix the case (for wiki search requests)
        terms = terms.split(' ')
        fixeds = []
        for term in terms:
            fixed = ""
            up = False
            if term.lower() == "and": # if it's just 'and', we don't don't fix anything and return a lowercase 'and'
                return "and"
            elif term.lower() == "of":
                return "of"
            elif term.lower() == "(sr)":
                return "(SR)"
            elif term.lower() == "(ssr)":
                return "(SSR)"
            elif term.lower() == "(r)":
                return "(R)"
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
            req = request.Request("https://gbf.wiki/" + self.fixCase(sps))
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
        except Exception as e:
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

    def make_party(self, val, export, img, d, offset): # draw the party
        print("Drawing Party...")
        if len(export['c']) > 5: # babyl mode (modifiers/positions are different)
            print("Babyl detected")
            babyl = True
            nchara = 12
            offset = (offset[0]+val['party_babyl_pos'][0], offset[1]+val['party_babyl_pos'][1])
            csize = val['chara_size_babyl']
            skill_width = val['skill_width']
            pos = (offset[0]+skill_width+val['chara_pos_babyl_offset'], offset[1])
            plus_key = "chara_plus_babyl_offset"
            # background
            self.pasteImage(img, "assets/bg.png", (pos[0]+val['bg_offset'], pos[1]+val['bg_offset']), (csize[0]*4+val['bg_end_offset'][0], csize[1]*3+val['bg_end_offset'][1]+val['bg_offset']*3))
            # mc
            self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/s/{}.jpg".format(self.get_mc_job_look(export['pcjs'], export['p'])), pos, csize)
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, val['job_size_babyl'])
        else: # normal mode
            babyl = False
            nchara = 5
            csize = val['chara_size']
            if len(export['mods']) > 19: skill_width = val['skill_width'] * 75 // 100
            else: skill_width = val['skill_width']
            pos = (offset[0]+skill_width, offset[1])
            plus_key = "chara_plus_offset"
            # background
            self.pasteImage(img, "assets/bg.png", (pos[0]+val['bg_offset'], pos[1]+val['bg_offset']), (csize[0]*6+val['bg_end_offset'][0], csize[1]+val['bg_end_offset'][1]))
            # mc
            self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/quest/{}.jpg".format(self.get_mc_job_look(export['pcjs'], export['p'])), pos, csize)
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, val['job_size'])
        print("MC: skin", export['pcjs'], ", job", export['p'])

        for i in range(0, nchara): # iterate through the party
            if babyl:
                pos = (offset[0]+csize[0]*(i%4)+skill_width+val['chara_pos_babyl_offset'], offset[1]+csize[1]*(i//4))
                if i == 0: continue
            else:
                pos = (offset[0]+skill_width+csize[0]*(i+1), offset[1])
            # portrait
            if i >= len(export['c']) or export['c'][i] is None:
                if babyl: self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/tower/assets_en/npc/s/3999999999.jpg", pos, csize)
                else: self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/deckcombination/base_empty_npc.jpg", pos, csize)
                continue
            else:
                print("Ally", i, ",", export['c'][i])
                if export['c'][i] in self.nullchar: 
                    self.pasteImage(img, ("assets/babyl_{}.jpg" if babyl else "assets/{}.jpg").format(export['c'][i]), pos, csize)
                else:
                    self.dlAndPasteImage(img, ("http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/s/{}_{}.jpg" if babyl else "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/quest/{}_{}.jpg").format(export['c'][i], self.get_uncap_id(export['cs'][i])), pos, csize)
            # rings
            if export['cwr'][i] == True:
                if babyl: self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", pos, val['ring_size_babyl'])
                else: self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (pos[0]+val['ring_offset'], pos[1]+val['ring_offset']), val['ring_size'])
            # plus
            if export['cp'][i] > 0:
                d.text((pos[0]+csize[0]+val[plus_key][0], pos[1]+csize[1]+val[plus_key][1]), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.small_font, stroke_width=val['stroke_width'], stroke_fill=(0, 0, 0))
            if not babyl:
                # level
                self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+csize[1]), (csize[0], val['stat_height']))
                d.text((pos[0]+val['text_offset'][0], pos[1]+csize[1]+val['text_offset'][1]), "Lv{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.font)
        # mc sub skills
        if babyl: pos = (offset[0], offset[1]+csize[1])
        else: pos = (offset[0], offset[1]+val['sub_skill_text_space']*5)
        self.pasteImage(img, "assets/subskills.png", pos, val['sub_skill_bg'])
        count = 0
        print("MC skills:", export['ps'])
        for i in range(len(export['ps'])):
            if export['ps'][i] is not None:
                d.text((pos[0]+val['sub_skill_text_off'], pos[1]+val['sub_skill_text_off']+val['sub_skill_text_space']*count), export['ps'][i], fill=(255, 255, 255), font=self.font)
                count += 1

    def make_extra_summon(self, val, export, img, d, offset): # extra sub summons (only called if detected)
        print("Drawing Extra Summons...")
        ssize = val['summon_sub_size']
        for i in range(0, 2):
            pos = (offset[0]+val['summon_size'][0]*5+val['summon_off']*2, val['extra_sum_size'][1]+val['extra_sum_off']+offset[1]+i*(ssize[1]+val['stat_height']))
            if i == 0: self.pasteImage(img, "assets/subsummon.png", (pos[0], pos[1]-val['extra_sum_size'][1]-val['extra_sum_off']), val['extra_sum_size'])
            if export['s'][i+5] is None:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/2999999999.jpg", pos, ssize)
                continue
            else:
                print("Summon", i+5, ",", export['ss'][i+5])
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(export['ss'][i+5]), pos, ssize)
            # star
            if export['se'][i+5] < 3: self.pasteImage(img, "assets/star_0.png", pos, val['star_size'])
            elif export['se'][i+5] == 3: self.pasteImage(img, "assets/star_1.png", pos, val['star_size'])
            elif export['se'][i+5] == 4: self.pasteImage(img, "assets/star_2.png", pos, val['star_size'])
            elif export['se'][i+5] >= 5: self.pasteImage(img, "assets/star_3.png", pos, val['star_size'])
            # level
            self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+ssize[1]), (ssize[0], val['stat_height']))
            d.text((pos[0]+val['sum_level_text_off'][0], pos[1]+ssize[1]+val['sum_level_text_off'][1]), "Lv{}".format(export['sl'][i+5]), fill=(255, 255, 255), font=self.small_font)

    def make_summons(self, val, export, img, d, offset): # draw the summons
        print("Drawing Summons...")
        ssize = val['summon_size']
        # background setup
        if len(export['ss']) > 5: # with sub summon
            self.pasteImage(img, "assets/bg.png", (offset[0]+val['bg_offset'], offset[1]+val['bg_offset']), (val['summon_off']*2+ssize[0]*6+val['bg_end_offset2'][0], ssize[1]+val['bg_end_offset2'][1]))
        else: # without
            self.pasteImage(img, "assets/bg.png", (offset[0]+val['bg_offset'], offset[1]+val['bg_offset']), (ssize[0]*5+val['bg_end_offset2'][0]*2, ssize[1]+val['bg_end_offset2'][1]))

        for i in range(0, 5): # iterate through first 5 summons)
            if i > 0: pos = (offset[0]+ssize[0]*i+val['summon_off'], offset[1]) # first one is a bit more on the left
            else: pos = (offset[0]+ssize[0]*i, offset[1])
            # portraits
            if export['s'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/2999999999.jpg", pos, ssize)
                continue
            else:
                print("Summon", i, ",", export['ss'][i])
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/{}.jpg".format(export['ss'][i]), pos, ssize)
            # star
            if export['se'][i] < 3: self.pasteImage(img, "assets/star_0.png", pos, val['star_size'])
            elif export['se'][i] == 3: self.pasteImage(img, "assets/star_1.png", pos, val['star_size'])
            elif export['se'][i] == 4: self.pasteImage(img, "assets/star_2.png", pos, val['star_size'])
            elif export['se'][i] >= 5: self.pasteImage(img, "assets/star_3.png", pos, val['star_size'])
            # plus
            if export['sp'][i] > 0:
                d.text((pos[0]+ssize[0]+val['summon_plus_offset'][0], pos[1]+ssize[1]+val['summon_plus_offset'][1]), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=val['stroke_width'], stroke_fill=(0, 0, 0))
            # level
            self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+ssize[1]), (ssize[0], val['stat_height']))
            d.text((pos[0]+val['sum_level_text_off'][0], pos[1]+ssize[1]+val['sum_level_text_off'][1]), "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.small_font)
        # extra sub summons
        if len(export['ss']) > 5:
            self.make_extra_summon(val, export, img, d, offset)
        # stats
        self.pasteImage(img, "assets/chara_stat.png", (offset[0], offset[1]+ssize[1]+val['stat_height']), (ssize[0]*3, val['stat_height']))
        self.pasteImage(img, "assets/atk.png", (offset[0]+val['sum_stat_offsets'][0], offset[1]+ssize[1]+val['stat_height']+val['sum_stat_offsets'][0]), val['sum_atk_size'])
        self.pasteImage(img, "assets/hp.png", (offset[0]+val['sum_stat_offsets'][0]+val['sum_stat_offsets'][3], offset[1]+ssize[1]+val['stat_height']+val['sum_stat_offsets'][0]), val['sum_hp_size'])
        d.text((offset[0]+val['sum_stat_offsets'][2], offset[1]+ssize[1]+val['stat_height']+val['sum_stat_offsets'][0]), "{}".format(export['satk']), fill=(255, 255, 255), font=self.small_font)
        d.text((offset[0]+val['sum_stat_offsets'][3]+val['sum_stat_offsets'][1], offset[1]+ssize[1]+val['stat_height']+val['sum_stat_offsets'][0]), "{}".format(export['shp']), fill=(255, 255, 255), font=self.small_font)

    def make_grid(self, val, export, img, d, base_offset): # draw the weapons (sandbox is supported)
        print("Drawing Weapons...")
        # calculate various offset and position
        skill_box_height = val['skill_box_height']
        skill_icon_size = skill_box_height // 2
        ax_icon_size = val['ax_box_height']
        ax_separator = skill_box_height
        mh_size = val['mh_size']
        sub_size = val['sub_size']
        if len(export['mods']) > 15: # if more than 15 weapon mods are to be displayed, it uses the smaller size
            mod_offset = (base_offset[0]+mh_size[0]+4*sub_size[0]+val['bg_end_offset4'][0]+val['mod_off'], val['base'][1]-(val['mod_off']//2)-val['mod_text_off'][1] * len(export['mods']))
        else:
            mod_offset = (base_offset[0]+mh_size[0]+4*sub_size[0]+val['bg_end_offset4'][0]+val['mod_off_big'], val['base'][1]-(val['mod_off_big']//2)-val['mod_text_off_big'][1] * len(export['mods']))
        # check if we are using 10 or 13 weapons
        is_not_sandbox = (len(export['w']) <= 10 or isinstance(export['est'][0], str)) # pg shows 13 weapons somehow but the estimate element is also a string, hence we check if it's a string
        if is_not_sandbox: 
            base_offset = (base_offset[0] + int(sub_size[0] / 1.5), base_offset[1])
        else:
            print("Sandbox detected")
        # put background
        if not is_not_sandbox:
            self.pasteImage(img, "assets/grid_bg.png", (base_offset[0]+val['bg_offset'], base_offset[1]+val['bg_offset']), (mh_size[0]+4*sub_size[0]+val['bg_end_offset4'][0], val['bg_end_offset4'][1]))
        else:
            self.pasteImage(img, "assets/grid_bg.png", (base_offset[0]+val['bg_offset'], base_offset[1]+val['bg_offset']), (mh_size[0]+3*sub_size[0]+val['bg_end_offset3'][0], val['bg_end_offset3'][1]))
        # iterate through weapons
        for i in range(0, len(export['w'])):
            wt = "ls" if i == 0 else "m"
            if i == 0: # mainhand
                offset = (base_offset[0], base_offset[1])
                size = mh_size
                bsize = size
            elif i >= 10: # sandbox
                if is_not_sandbox:
                    break
                x = 3
                y = (i-1) % 3
                size = sub_size
                offset = (base_offset[0]+bsize[0]+val['wpn_separator']+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
            else: # others
                x = (i-1) % 3
                y = (i-1) // 3
                size = sub_size
                offset = (base_offset[0]+bsize[0]+val['wpn_separator']+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
            # portrait
            if export['w'][i] is None or export['wl'][i] is None:
                if i >= 10:
                    self.pasteImage(img, "assets/arca_slot.png", offset, size)
                else:
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt), offset, size)
                continue
            else:
                print("Weapon", i, ",", str(export['w'][i])+"00")
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/{}00.jpg".format(wt, export['w'][i]), offset, size)
            # skill box
            self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]+size[1]), (size[0], skill_box_height//2))
            if len(export['waxi'][i]) > 0:
                self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]+size[1]+skill_box_height//2), (size[0], skill_box_height//2))
            # plus
            if export['wp'][i] > 0:
                if i == 0:
                    d.text((offset[0]+size[0]+val['weapon_plus_offset'][0], offset[1]+size[1]+val['weapon_plus_offset'][1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=val['stroke_width'], stroke_fill=(0, 0, 0))
                else:
                    d.text((offset[0]+size[0]+val['weapon_plus_offset'][0], offset[1]+size[1]+val['weapon_plus_offset'][1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=val['stroke_width'], stroke_fill=(0, 0, 0))
            # skill level
            if export['wl'][i] is not None and export['wl'][i] > 1:
                d.text((offset[0]+skill_icon_size*3+val['skill_lvl_off'][0], offset[1]+size[1]+val['skill_lvl_off'][1]), "SL {}".format(export['wl'][i]), fill=(255, 255, 255), font=self.small_font)
            # skill icon
            for j in range(3):
                if export['wsn'][i][j] is not None:
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (offset[0]+skill_icon_size*j, offset[1]+size[1]), (skill_icon_size, skill_icon_size))
            # ax skills
            if len(export['waxt'][i]) > 0:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment_skill/{}.png".format(export['waxt'][i][0]), (offset[0], offset[1]), (int(ax_icon_size * (1.5 if i == 0 else 1)), int(ax_icon_size * (1.5 if i == 0 else 1))))
                for j in range(len(export['waxi'][i])):
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]), (offset[0]+ax_separator*j, offset[1]+size[1]+skill_icon_size), (skill_icon_size, skill_icon_size))
                    d.text((offset[0]+ax_separator*j+skill_icon_size+val['ax_text_off'][0], offset[1]+size[1]+skill_icon_size+val['ax_text_off'][1]), "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''), fill=(255, 255, 255), font=self.small_font)
        # sandbox tag
        if not is_not_sandbox:
            sandbox = (size[0], int(66*size[0]/159))
            self.pasteImage(img, "assets/sandbox.png", (offset[0], base_offset[1]+(skill_box_height+sub_size[1])*3), sandbox)
        # stats
        offset = (base_offset[0], base_offset[1]+bsize[1]+val['wpn_stat_off'])
        self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]), (bsize[0], val['wpn_stat_line']))
        self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]+val['wpn_stat_line']), (bsize[0], val['wpn_stat_line']))
        self.pasteImage(img, "assets/atk.png", (offset[0]+val['wpn_stat_text_off'][0], offset[1]+val['wpn_stat_text_off'][1]), val['wpn_atk_size'])
        self.pasteImage(img, "assets/hp.png", (offset[0]+val['wpn_stat_text_off'][0], offset[1]+val['wpn_stat_text_off'][1]+val['wpn_stat_line']), val['wpn_hp_size'])
        d.text((offset[0]+val['wpn_stat_text_off2'][0], offset[1]+val['wpn_stat_text_off2'][1]), "{}".format(export['watk']), fill=(255, 255, 255), font=self.font)
        d.text((offset[0]+val['wpn_stat_text_off2'][0], offset[1]+val['wpn_stat_text_off2'][1]+val['wpn_stat_line']), "{}".format(export['whp']), fill=(255, 255, 255), font=self.font)
        # estimated damage
        offset = (offset[0]+bsize[0]+val['estimate_off'][0], offset[1]+val['estimate_off'][1])
        if export['sps'] is not None and export['sps'] != '':
            # support summon
            if export['spsid'] is not None:
                supp = export['spsid']
            else:
                print("Support summon is", export['sps'], ", searching its ID on gbf.wiki...")
                supp = self.get_support_summon(export['sps'])
            if supp is None:
                print("The support summon search failed")
                self.pasteImage(img, "assets/big_stat.png", (offset[0]-bsize[0]-val['estimate_off'][0], offset[1]), (bsize[0], val['big_stat'][1]))
                d.text((offset[0]-bsize[0]-val['estimate_off'][0]+val['est_sub_text'][0] , offset[1]+val['est_text']*2), ("サポーター" if self.japanese else "Support"), fill=(255, 255, 255), font=self.font)
                if len(export['sps']) > 10: supp = export['sps'][:10] + "..."
                else: supp = export['sps']
                d.text((offset[0]-bsize[0]-val['estimate_off'][0]+val['est_sub_text'][0] , offset[1]+val['est_text']*2+val['stat_height']), supp, fill=(255, 255, 255), font=self.font)
            else:
                print("Support summon ID is", supp)
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(supp), (offset[0]-bsize[0]-val['estimate_off'][0]+val['supp_summon_off'], offset[1]), val['supp_summon'])
        # weapon grid stats
        est_width = ((size[0]*3)//2)
        for i in range(0, 2):
            self.pasteImage(img, "assets/big_stat.png", (offset[0]+est_width*i , offset[1]), (est_width+val['big_stat'][0], val['big_stat'][1]))
            d.text((offset[0]+val['est_text']+est_width*i, offset[1]+val['est_text']), "{}".format(export['est'][i+1]), fill=self.colors[int(export['est'][0])], font=self.big_font, stroke_width=val['stroke_width'], stroke_fill=(0, 0, 0))
            if i == 0:
                d.text((offset[0]+est_width*i+val['est_sub_text'][0] , offset[1]+val['est_sub_text'][1]), ("予測ダメ一ジ" if self.japanese else "Estimated"), fill=(255, 255, 255), font=self.font)
            elif i == 1:
                if int(export['est'][0]) <= 4: vs = (int(export['est'][0]) + 2) % 4 + 1
                else: vs = (int(export['est'][0]) - 5 + 1) % 2 + 5
                if self.japanese:
                    d.text((offset[0]+est_width*i+val['est_sub_text'][0] , offset[1]+val['est_sub_text'][1]), "対", fill=(255, 255, 255), font=self.font)
                    d.text((offset[0]+est_width*i+val['est_sub_text_ele_jp'] , offset[1]+val['est_sub_text'][1]), "{}属性".format(self.color_strs_jp[vs]), fill=self.colors[vs], font=self.font)
                    d.text((offset[0]+est_width*i+val['est_sub_text_jp'][0] , offset[1]+val['est_sub_text'][1]), "予測ダメ一ジ", fill=(255, 255, 255), font=self.font)
                else:
                    d.text((offset[0]+est_width*i+val['est_sub_text'][0] , offset[1]+val['est_sub_text'][1]), "vs", fill=(255, 255, 255), font=self.font)
                    d.text((offset[0]+est_width*i+val['est_sub_text_ele'] , offset[1]+val['est_sub_text'][1]), "{}".format(self.color_strs[vs]), fill=self.colors[vs], font=self.font)
        # weapon modifiers
        print("Adding the", len(export['mods']), "modifier(s)")
        if len(export['mods']) > 15:
            suffix = ''
            mod_font = self.small_font
        else:
            suffix = '_big'
            mod_font = self.font
        self.pasteImage(img, "assets/mod_bg.png", (mod_offset[0]-val['mod_off'+suffix], mod_offset[1]-val['mod_off'+suffix]//2), val['mod_bg_size'+suffix])
        self.pasteImage(img, "assets/mod_bg_supp.png", (mod_offset[0]-val['mod_off'+suffix], mod_offset[1]-val['mod_off'+suffix]+val['mod_bg_size'+suffix][1]), (val['mod_bg_supp_size'+suffix], val['mod_text_off'+suffix][1] * len(export['mods'])))
        for m in export['mods']:
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/weapon_skill_label/" + m['icon_img'], mod_offset, val['mod_size'+suffix])
            d.text((mod_offset[0], mod_offset[1]+val['mod_text_off'+suffix][0]), str(m['value']), fill=((255, 168, 38, 255) if m['is_max'] else (255, 255, 255, 255)), font=mod_font)
            mod_offset = (mod_offset[0], mod_offset[1]+val['mod_text_off'+suffix][1])

    def make(self, fast=False): # main function
        try:
            if not fast:
                print("Instructions:")
                print("1) Go to the party screen you want to export")
                print("2) Click your bookmarklet")
                print("3) Come back here and press Return to continue")
                input()
            clipboard = pyperclip.paste() # get clipboard content
            export = json.loads(clipboard) # get the data from clipboard
            if self.data.get('caching', False):
                self.checkDiskCache()
            self.cache = {}
            val = self.build_quality()
            self.japanese = (export['lang'] == 'ja')
            if self.japanese: print("Japanese Detected")
            else: print("English Detected")
            # load fonts
            if self.japanese:
                self.big_font = ImageFont.truetype("assets/font_japanese.ttf", val['font_jp'][2], encoding="unic")
                self.font = ImageFont.truetype("assets/font_japanese.ttf", val['font_jp'][1], encoding="unic")
                self.small_font = ImageFont.truetype("assets/font_japanese.ttf", val['font_jp'][0], encoding="unic")
            else:
                self.big_font = ImageFont.truetype("assets/font_english.ttf", val['font'][2], encoding="unic")
                self.font = ImageFont.truetype("assets/font_english.ttf", val['font'][1], encoding="unic")
                self.small_font = ImageFont.truetype("assets/font_english.ttf", val['font'][0], encoding="unic")
            # make image
            img = Image.new('RGB', val['base'], "black")
            im_a = Image.new("L", img.size, "black")
            img.putalpha(im_a)
            im_a.close()
            d = ImageDraw.Draw(img, 'RGBA')

            # party
            self.pasteImage(img, "assets/characters.png", val['party_header'], val['header_size'])
            self.make_party(val, export, img, d, val['party_pos'])

            # summons
            self.pasteImage(img, "assets/summons.png", val['summon_header'], val['header_size'])
            self.make_summons(val, export, img, d, val['summon_pos'])

            # grid
            self.pasteImage(img, "assets/weapons.png", val['weapon_header'], val['header_size'])
            self.make_grid(val, export, img, d, val['weapon_pos'])
            
            # done
            img.save("party.png", "PNG")
            img.close()
            print("Success, party.png has been generated")
            return True
        except Exception as e:
            print("An error occured")
            print("exception message:", e)
            print("Did you follow the instructions?")
            return False

    def settings(self):
        while True:
            print("")
            print("Settings:")
            print("[0] Change quality ( Current:", self.data.get('quality', '720p'),")")
            print("[1] Enable Disk Caching ( Current:", self.data.get('caching', False),")")
            print("[2] Empty Cache")
            print("[Any] Back")
            s = input()
            if s == "0":
                v = ({'720p':0, '1080p':1, '4K':2, '8K':3}[self.data.get('quality', '720p')] + 1) % 4
                self.data['quality'] = {0:'720p', 1:'1080p', 2:'4K', 3:'8K'}.get(v, 0)
            elif s == "1":
                self.data['caching'] = not self.data.get('caching', False)
            elif s == "2":
                self.emptyCache()
            else:
                return

    def cpyBookmark(self):
        # check bookmarklet.txt for a more readable version
        # note: when updating it in this piece of code, you need to double the \
        pyperclip.copy("javascript:(function(){if(!window.location.hash.startsWith(\"#party/index/\")&&!window.location.hash.startsWith(\"#party/expectancy_damage/index\")&&!window.location.hash.startsWith(\"#tower/party/index/\")&&!(window.location.hash.startsWith(\"#event/sequenceraid\") && window.location.hash.indexOf(\"/party/index/\") > 0)&&!window.location.hash.startsWith(\"#tower/party/expectancy_damage/index/\")){alert('Please go to a GBF Party screen');return}let obj={lang:window.Game.lang,p:parseInt(window.Game.view.deck_model.attributes.deck.pc.job.master.id,10),pcjs:window.Game.view.deck_model.attributes.deck.pc.param.image,ps:[],c:[],cl:[],cs:[],cp:[],cwr:[],s:[],sl:[],ss:[],se:[],sp:[],w:[],wl:[],wsn:[],wll:[],wp:[],wax:[],waxi:[],waxt:[],watk:window.Game.view.deck_model.attributes.deck.pc.weapons_attack,whp:window.Game.view.deck_model.attributes.deck.pc.weapons_hp,satk:window.Game.view.deck_model.attributes.deck.pc.summons_attack,shp:window.Game.view.deck_model.attributes.deck.pc.summons_hp,est:[window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage_attribute,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_advantage_damage],mods:window.Game.view.deck_model.attributes.deck.pc.damage_info.effect_value_info,sps:(window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name?window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name:null),spsid:(Game.view.expectancyDamageData?(Game.view.expectancyDamageData.summonId?Game.view.expectancyDamageData.summonId:null):null)};try{for(let i=0;i<4-window.Game.view.deck_model.attributes.deck.pc.set_action.length;i++){obj.ps.push(null)}Object.values(window.Game.view.deck_model.attributes.deck.pc.set_action).forEach(e=>{obj.ps.push(e.name?e.name.trim():null)})}catch(error){obj.ps=[null,null,null,null]};if(window.location.hash.startsWith(\"#tower/party/index/\")){Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(x=>{console.log(x);Object.values(x).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null)})})}else{Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null)})}Object.values(window.Game.view.deck_model.attributes.deck.pc.summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.sub_summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.weapons).forEach(e=>{obj.w.push(e.master?parseInt(e.master.id.slice(0,-2),10):null);obj.wl.push(e.param?parseInt(e.param.skill_level,10):null);obj.wsn.push(e.param?[e.skill1?e.skill1.image:null,e.skill2?e.skill2.image:null,e.skill3?e.skill3.image:null]:null);obj.wll.push(e.param?parseInt(e.param.level,10):null);obj.wp.push(e.param?parseInt(e.param.quality,10):null);obj.waxt.push(e.param?e.param.augment_image:null);obj.waxi.push(e.param?e.param.augment_skill_icon_image:null);obj.wax.push(e.param?e.param.augment_skill_info:null)});let copyListener=event=>{document.removeEventListener(\"copy\",copyListener,true);event.preventDefault();let clipboardData=event.clipboardData;clipboardData.clearData();clipboardData.setData(\"text/plain\",JSON.stringify(obj))};document.addEventListener(\"copy\",copyListener,true);document.execCommand(\"copy\");}())")

    def run(self): # old command line menu
        while True:
            try:
                print("")
                print("Main Menu:")
                print("[0] Generate Image")
                print("[1] Get Bookmarklet")
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
                    self.settings()
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
        
        # run part
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=0, rowspan=2, sticky="we")
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Run")
        self.button = Tk.Button(tabcontent, text="Build Image", command=self.build)
        self.button.grid(row=0, column=0, sticky="we")
        Tk.Button(tabcontent, text="Get Bookmarklet", command=self.bookmark).grid(row=1, column=0, sticky="we")
        
        # setting part
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=1, rowspan=2, sticky="we")
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Settings")
        self.qual_variable = Tk.StringVar(self)
        options = list(self.pb.qual.keys())
        self.qual_variable.set(self.pb.data.get('quality', options[0]))
        Tk.Label(tabcontent, text="Quality").grid(row=0, column=0)
        opt = Tk.OptionMenu(tabcontent, self.qual_variable, *options, command=self.qual_changed)
        opt.grid(row=0, column=1)
        
        self.cache_var = Tk.IntVar(value=self.pb.data.get('caching', False))
        Tk.Label(tabcontent, text="Caching").grid(row=1, column=0)
        Tk.Checkbutton(tabcontent, variable=self.cache_var, command=self.toggleCaching).grid(row=1, column=1)
        
        # other
        self.status = Tk.Label(self, text="Starting")
        self.status.grid(row=0, column=0, sticky="w")
        
        self.thread = None
        self.events = []

    def run(self):
        # main loop
        while self.apprunning:
            if len(self.events) > 0:
                ev = self.events.pop(0)
                if ev[0] == "Info": messagebox.showinfo(ev[0], ev[1])
                elif ev[0] == "Error": messagebox.showerror(ev[0], ev[1])
            if self.thread is None: self.status.config(text="Idle", background='#c7edcd')
            else: self.status.config(text="Running", background='#edc7c7')
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
        self.thread.setDaemon(True)
        self.thread.start()

    def buildThread(self):
        if self.pb.make(fast=True):
            self.events.append(("Info", "Process completed with success"))
        else:
            self.events.append(("Error", "An error occured, did you press the bookmark before starting?"))
        self.thread = None

    def bookmark(self):
        self.pb.cpyBookmark()
        messagebox.showinfo("Info", "Bookmarklet copied!\nTo setup on chrome:\n1) Make a new bookmark (of GBF for example)\n2) Right-click and edit\n3) Change the name if you want\n4) Paste the code in the url field")

    def qual_changed(self, *args):
        self.pb.data['quality'] = args[0]

    def toggleCaching(self):
        self.pb.data['caching'] = (self.cache_var.get() != 0)

# entry point
if __name__ == "__main__":
    ver = "v3.0"
    if '-fast' in sys.argv:
        print("Granblue Fantasy Party Image Builder", ver)
        pb = PartyBuilder()
        pb.make(fast=True)
        if '-nowait' not in sys.argv:
            print("Closing in 10 seconds...")
            time.sleep(10)
    elif '-cmd' in sys.argv:
        print("Granblue Fantasy Party Image Builder", ver)
        pb = PartyBuilder()
        pb.run()
    else:
        ui = Interface(PartyBuilder(), ver)
        ui.run()