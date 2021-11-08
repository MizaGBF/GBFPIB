from urllib import request, parse
from urllib.parse import unquote
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

class PartyBuilder():
    def __init__(self):
        self.big_font = None
        self.font = None
        self.small_font = None
        self.cache = {}
        self.sumcache = {}
        self.nullchar = [3030182000, 3020072000]
        self.colors = {
            1:(243, 48, 33),
            2:(85, 176, 250),
            3:(227, 124, 32),
            4:(55, 232, 16),
            5:(253, 216, 67),
            6:(176, 84, 251),
        }
        self.color_strs = {
            1:"Fire",
            2:"Water",
            3:"Earth",
            4:"Wind",
            5:"Light",
            6:"Dark",
        }
        self.base = {
            'font': [14, 16, 30],
            'stroke_width': 2,
            'base': (600, 720),
            'party_header': (10, 10),
            'summon_header': (10, 150),
            'weapon_header': (10, 320),
            'header_size': (92, 25),
            'party_pos': (5, 20),
            'party_babyl_pos': (30, -18),
            'summon_pos': (120, 180),
            'weapon_pos': (10, 355),
            'chara_size': (66, 120),
            'chara_size_babyl': (56, 56),
            'chara_plus_babyl_offset': (-35, -15),
            'chara_pos_babyl_offset': 10,
            'skill_width': 140,
            'bg_offset': -5,
            'bg_end_offset': (10, 40),
            'bg_end_offset2': (10, 56),
            'bg_end_offset3': (20, 420),
            'bg_end_offset4': (20, 500),
            'job_size': (24, 20),
            'job_size_babyl': (18, 15),
            'ring_size': (30, 30),
            'ring_size_babyl': (20, 20),
            'ring_offset': -2,
            'chara_plus_offset': (-48, -22),
            'stat_height': 20,
            'text_offset': (4, 2),
            'sub_skill_bg': (140, 49),
            'sub_skill_text_off': 1,
            'sub_skill_text_space': 16,
            'star_size': (22, 22),
            'summon_size': (60, 126),
            'summon_sub_size': (60, 34),
            'summon_plus_offset': (-35, -20),
            'sum_level_text_off': (2, 3),
            'sum_atk_size': (30, 13),
            'sum_hp_size': (22, 13),
            'sum_stat_offsets': [3, 30, 40, 100],
            'skill_box_height': 48,
            'ax_box_height': 32,
            'mh_size': (100, 210),
            'sub_size': (96, 55),
            'wpn_separator': 5,
            'weapon_plus_offset': (-35, -20),
            'skill_lvl_off': [-17, 5],
            'ax_text_off': [2, 5],
            'wpn_stat_off': 50,
            'wpn_stat_line': 25,
            'wpn_atk_size': (30, 13),
            'wpn_hp_size': (22, 13),
            'wpn_stat_text_off': (3, 5),
            'wpn_stat_text_off2': (37, 5),
            'estimate_off': (5, 55),
            'big_stat': (-5, 50),
            'est_text': 3,
            'est_sub_text': (5, 30),
            'est_sub_text_ele': 22,
            'supp_summon': (87, 50),
            'mod_off': 8,
            'mod_bg_size': (74, 38),
            'mod_bg_supp_size': 74,
            'mod_size': (58, 15),
            'mod_text_off': [15, 28],
            'supp_summon_off': 6,
            'summon_off': 10,
            'extra_sum_size': (60, 24),
            'extra_sum_off': 10
        }
        self.classes = {
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
        self.qual = {'720p': 1, '1080p': 1.5, '4K': 3, '8K': 6}
        self.supp_summon_re = [
            re.compile('(20[0-9]{8})\\.'),
            re.compile('(20[0-9]{8}_02)\\.')
        ]
        self.v = None
        self.last = ""
        self.data = {}
        self.load()

    def load(self):
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

    def save(self):
        try:
            with open('settings.json', 'w') as outfile:
                json.dump(self.data, outfile)
        except:
            pass

    def build_quality(self):
        if self.data.get('quality', '720p') == self.last: return
        print("Caching size for quality", self.data.get('quality', '720p'))
        self.v = {}
        mod = self.qual[self.data.get('quality', '720p')]
        for k in self.base:
            if isinstance(self.base[k], int): self.v[k] = int(self.base[k]*mod)
            elif isinstance(self.base[k], tuple):
                tmp = []
                for i in self.base[k]:
                    tmp.append(int(i*mod))
                self.v[k] = tuple(tmp)
            elif isinstance(self.base[k], list):
                tmp = []
                for i in self.base[k]:
                    tmp.append(int(i*mod))
                self.v[k] = tmp
            else: raise Exception("Internal error")
        self.big_font = ImageFont.truetype("assets/basic.ttf", self.v['font'][2])
        self.font = ImageFont.truetype("assets/basic.ttf", self.v['font'][1])
        self.small_font = ImageFont.truetype("assets/basic.ttf", self.v['font'][0])
        self.last = self.data.get('quality', '720p')

    def pasteImage(self, img, file, offset, resize=None): # paste and image onto another
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize, Image.LANCZOS))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    def dlAndPasteImage(self, img, url, offset, resize=None): # dl an image and call pasteImage()
        if url not in self.cache:
            try: # get from disk cache if enabled
                if self.data.get('caching', False):
                    with open("cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "rb") as f:
                        self.cache[url] = f.read()
                else:
                    raise Exception()
            except:
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

    def checkDiskCache(self):
        if not os.path.isdir('cache'):
            os.mkdir('cache')

    def draw_rect(self, d, x, y, w, h): # to draw placholders
        d.rectangle([(x, y), (x+w-1, y+h-1)], fill=(0, 0, 0, 200))

    def fixCase(self, terms): # function to fix the case (for wiki requests)
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

    def get_support_summon(self, sps): # search the wiki to match a summon name to its id
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
            return None

    def get_uncap_id(self, cs): # to get character portraits based on uncap levels
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def get_mc_job_look(self, skin, job):
        jid = job // 10000
        if jid not in self.classes: return skin
        return "{}_{}_{}".format(job, self.classes[jid], '_'.join(skin.split('_')[2:]))

    def make_party(self, export, img, d, offset): # draw the party
        print("Drawing Party...")
        if len(export['c']) > 5: # babyl mode
            print("Babyl detected")
            babyl = True
            nchara = 12
            offset = (offset[0]+self.v['party_babyl_pos'][0], offset[1]+self.v['party_babyl_pos'][1])
            csize = self.v['chara_size_babyl']
            skill_width = self.v['skill_width']
            pos = (offset[0]+skill_width+self.v['chara_pos_babyl_offset'], offset[1])
            plus_key = "chara_plus_babyl_offset"
            # background
            self.pasteImage(img, "assets/bg.png", (pos[0]+self.v['bg_offset'], pos[1]+self.v['bg_offset']), (csize[0]*4+self.v['bg_end_offset'][0], csize[1]*3+self.v['bg_end_offset'][1]+self.v['bg_offset']*3))
            # mc
            self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/s/{}.jpg".format(self.get_mc_job_look(export['pcjs'], export['p'])), pos, csize)
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, self.v['job_size_babyl'])
        else: # normal mode
            babyl = False
            nchara = 5
            csize = self.v['chara_size']
            if len(export['mods']) > 19: skill_width = self.v['skill_width'] * 75 // 100
            else: skill_width = self.v['skill_width']
            pos = (offset[0]+skill_width, offset[1])
            plus_key = "chara_plus_offset"
            # background
            self.pasteImage(img, "assets/bg.png", (pos[0]+self.v['bg_offset'], pos[1]+self.v['bg_offset']), (csize[0]*6+self.v['bg_end_offset'][0], csize[1]+self.v['bg_end_offset'][1]))
            # mc
            self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/quest/{}.jpg".format(self.get_mc_job_look(export['pcjs'], export['p'])), pos, csize)
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), pos, self.v['job_size'])
        print("MC: skin", export['pcjs'], ", job", export['p'])

        for i in range(0, nchara): # npcs
            if babyl:
                pos = (offset[0]+csize[0]*(i%4)+skill_width+self.v['chara_pos_babyl_offset'], offset[1]+csize[1]*(i//4))
                if i == 0: continue
            else:
                pos = (offset[0]+skill_width+csize[0]*(i+1), offset[1])
            # portrait
            if i >= len(export['c']) or export['c'][i] is None:
                if babyl: self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/tower/assets/npc/s/3999999999.jpg", pos, csize)
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
                if babyl: self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", pos, self.v['ring_size_babyl'])
                else: self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (pos[0]+self.v['ring_offset'], pos[1]+self.v['ring_offset']), self.v['ring_size'])
            # plus
            if export['cp'][i] > 0:
                d.text((pos[0]+csize[0]+self.v[plus_key][0], pos[1]+csize[1]+self.v[plus_key][1]), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.small_font, stroke_width=self.v['stroke_width'], stroke_fill=(0, 0, 0))
            if not babyl:
                # level
                self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+csize[1]), (csize[0], self.v['stat_height']))
                d.text((pos[0]+self.v['text_offset'][0], pos[1]+csize[1]+self.v['text_offset'][1]), "Lv{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.font)
        # mc sub skills
        if babyl: pos = (offset[0], offset[1]+csize[1])
        else: pos = (offset[0], offset[1]+self.v['sub_skill_text_space']*5)
        self.pasteImage(img, "assets/subskills.png", pos, self.v['sub_skill_bg'])
        count = 0
        print("MC skills:", export['ps'])
        for i in range(len(export['ps'])):
            if export['ps'][i] is not None:
                d.text((pos[0]+self.v['sub_skill_text_off'], pos[1]+self.v['sub_skill_text_off']+self.v['sub_skill_text_space']*count), export['ps'][i], fill=(255, 255, 255), font=self.font)
                count += 1

    def make_extra_summon(self, export, img, d, offset):
        print("Drawing Extra Summons...")
        ssize = self.v['summon_sub_size']
        for i in range(0, 2):
            pos = (offset[0]+self.v['summon_size'][0]*5+self.v['summon_off']*2, self.v['extra_sum_size'][1]+self.v['extra_sum_off']+offset[1]+i*(ssize[1]+self.v['stat_height']))
            if i == 0: self.pasteImage(img, "assets/subsummon.png", (pos[0], pos[1]-self.v['extra_sum_size'][1]-self.v['extra_sum_off']), self.v['extra_sum_size'])
            if export['s'][i+5] is None:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/2999999999.jpg", pos, ssize)
                continue
            else:
                print("Summon", i+5, ",", export['ss'][i+5])
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(export['ss'][i+5]), pos, ssize)
            # star
            if export['se'][i+5] < 3: self.pasteImage(img, "assets/star_0.png", pos, self.v['star_size'])
            elif export['se'][i+5] == 3: self.pasteImage(img, "assets/star_1.png", pos, self.v['star_size'])
            elif export['se'][i+5] == 4: self.pasteImage(img, "assets/star_2.png", pos, self.v['star_size'])
            elif export['se'][i+5] >= 5: self.pasteImage(img, "assets/star_3.png", pos, self.v['star_size'])
            # level
            self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+ssize[1]), (ssize[0], self.v['stat_height']))
            d.text((pos[0]+self.v['sum_level_text_off'][0], pos[1]+ssize[1]+self.v['sum_level_text_off'][1]), "Lv{}".format(export['sl'][i+5]), fill=(255, 255, 255), font=self.small_font)

    def make_summons(self, export, img, d, offset): # draw the summons
        print("Drawing Summons...")
        ssize = self.v['summon_size']
        # background
        if len(export['ss']) > 5:
            self.pasteImage(img, "assets/bg.png", (offset[0]+self.v['bg_offset'], offset[1]+self.v['bg_offset']), (self.v['summon_off']*2+ssize[0]*6+self.v['bg_end_offset2'][0], ssize[1]+self.v['bg_end_offset2'][1]))
        else:
            self.pasteImage(img, "assets/bg.png", (offset[0]+self.v['bg_offset'], offset[1]+self.v['bg_offset']), (ssize[0]*5+self.v['bg_end_offset2'][0]*2, ssize[1]+self.v['bg_end_offset2'][1]))
        for i in range(0, 5):
            if i > 0: pos = (offset[0]+ssize[0]*i+self.v['summon_off'], offset[1])
            else: pos = (offset[0]+ssize[0]*i, offset[1])
            # portraits
            if export['s'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/2999999999.jpg", pos, ssize)
                continue
            else:
                print("Summon", i, ",", export['ss'][i])
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/{}.jpg".format(export['ss'][i]), pos, ssize)
            # star
            if export['se'][i] < 3: self.pasteImage(img, "assets/star_0.png", pos, self.v['star_size'])
            elif export['se'][i] == 3: self.pasteImage(img, "assets/star_1.png", pos, self.v['star_size'])
            elif export['se'][i] == 4: self.pasteImage(img, "assets/star_2.png", pos, self.v['star_size'])
            elif export['se'][i] >= 5: self.pasteImage(img, "assets/star_3.png", pos, self.v['star_size'])
            # plus
            if export['sp'][i] > 0:
                d.text((pos[0]+ssize[0]+self.v['summon_plus_offset'][0], pos[1]+ssize[1]+self.v['summon_plus_offset'][1]), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=self.v['stroke_width'], stroke_fill=(0, 0, 0))
            # level
            self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+ssize[1]), (ssize[0], self.v['stat_height']))
            d.text((pos[0]+self.v['sum_level_text_off'][0], pos[1]+ssize[1]+self.v['sum_level_text_off'][1]), "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.small_font)
        # extra sub summons
        if len(export['ss']) > 5:
            self.make_extra_summon(export, img, d, offset)
        # stats
        self.pasteImage(img, "assets/chara_stat.png", (offset[0], offset[1]+ssize[1]+self.v['stat_height']), (ssize[0]*3, self.v['stat_height']))
        self.pasteImage(img, "assets/atk.png", (offset[0]+self.v['sum_stat_offsets'][0], offset[1]+ssize[1]+self.v['stat_height']+self.v['sum_stat_offsets'][0]), self.v['sum_atk_size'])
        self.pasteImage(img, "assets/hp.png", (offset[0]+self.v['sum_stat_offsets'][0]+self.v['sum_stat_offsets'][3], offset[1]+ssize[1]+self.v['stat_height']+self.v['sum_stat_offsets'][0]), self.v['sum_hp_size'])
        d.text((offset[0]+self.v['sum_stat_offsets'][2], offset[1]+ssize[1]+self.v['stat_height']+self.v['sum_stat_offsets'][0]), "{}".format(export['satk']), fill=(255, 255, 255), font=self.small_font)
        d.text((offset[0]+self.v['sum_stat_offsets'][3]+self.v['sum_stat_offsets'][1], offset[1]+ssize[1]+self.v['stat_height']+self.v['sum_stat_offsets'][0]), "{}".format(export['shp']), fill=(255, 255, 255), font=self.small_font)

    def make_grid(self, export, img, d, base_offset): # draw the weapons (sandbox is supported)
        print("Drawing Weapons...")
        skill_box_height = self.v['skill_box_height']
        skill_icon_size = skill_box_height // 2
        ax_icon_size = self.v['ax_box_height']
        ax_separator = skill_box_height
        mh_size = self.v['mh_size']
        sub_size = self.v['sub_size']
        mod_offset = (base_offset[0]+mh_size[0]+4*sub_size[0]+self.v['bg_end_offset4'][0]+self.v['mod_off'], self.v['base'][1]-(self.v['mod_off']//2)-self.v['mod_text_off'][1] * len(export['mods']))
        is_not_sandbox = (len(export['w']) <= 10 or isinstance(export['est'][0], str)) # pg shows 13 weapons somehow but the estimate element is also a string
        if is_not_sandbox: 
            base_offset = (base_offset[0] + int(sub_size[0] / 1.5), base_offset[1])
        else:
            print("Sandbox detected")
        # background
        if not is_not_sandbox:
            self.pasteImage(img, "assets/grid_bg.png", (base_offset[0]+self.v['bg_offset'], base_offset[1]+self.v['bg_offset']), (mh_size[0]+4*sub_size[0]+self.v['bg_end_offset4'][0], self.v['bg_end_offset4'][1]))
        else:
            self.pasteImage(img, "assets/grid_bg.png", (base_offset[0]+self.v['bg_offset'], base_offset[1]+self.v['bg_offset']), (mh_size[0]+3*sub_size[0]+self.v['bg_end_offset3'][0], self.v['bg_end_offset3'][1]))
        # weapons
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
                offset = (base_offset[0]+bsize[0]+self.v['wpn_separator']+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
            else: # others
                x = (i-1) % 3
                y = (i-1) // 3
                size = sub_size
                offset = (base_offset[0]+bsize[0]+self.v['wpn_separator']+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
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
                    d.text((offset[0]+size[0]+self.v['weapon_plus_offset'][0], offset[1]+size[1]+self.v['weapon_plus_offset'][1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=self.v['stroke_width'], stroke_fill=(0, 0, 0))
                else:
                    d.text((offset[0]+size[0]+self.v['weapon_plus_offset'][0], offset[1]+size[1]+self.v['weapon_plus_offset'][1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=self.v['stroke_width'], stroke_fill=(0, 0, 0))
            # skill level
            if export['wl'][i] is not None and export['wl'][i] > 1:
                d.text((offset[0]+skill_icon_size*3+self.v['skill_lvl_off'][0], offset[1]+size[1]+self.v['skill_lvl_off'][1]), "SL {}".format(export['wl'][i]), fill=(255, 255, 255), font=self.small_font)
            # skill icon
            for j in range(3):
                if export['wsn'][i][j] is not None:
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (offset[0]+skill_icon_size*j, offset[1]+size[1]), (skill_icon_size, skill_icon_size))
            # ax skills
            if len(export['waxt'][i]) > 0:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment_skill/{}.png".format(export['waxt'][i][0]), (offset[0], offset[1]), (int(ax_icon_size * (1.5 if i == 0 else 1)), int(ax_icon_size * (1.5 if i == 0 else 1))))
                for j in range(len(export['waxi'][i])):
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]), (offset[0]+ax_separator*j, offset[1]+size[1]+skill_icon_size), (skill_icon_size, skill_icon_size))
                    d.text((offset[0]+ax_separator*j+skill_icon_size+self.v['ax_text_off'][0], offset[1]+size[1]+skill_icon_size+self.v['ax_text_off'][1]), "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''), fill=(255, 255, 255), font=self.small_font)
        # sandbox tag
        if not is_not_sandbox:
            sandbox = (size[0], int(66*size[0]/159))
            self.pasteImage(img, "assets/sandbox.png", (offset[0], base_offset[1]+(skill_box_height+sub_size[1])*3), sandbox)
        # stats
        offset = (base_offset[0], base_offset[1]+bsize[1]+self.v['wpn_stat_off'])
        self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]), (bsize[0], self.v['wpn_stat_line']))
        self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]+self.v['wpn_stat_line']), (bsize[0], self.v['wpn_stat_line']))
        self.pasteImage(img, "assets/atk.png", (offset[0]+self.v['wpn_stat_text_off'][0], offset[1]+self.v['wpn_stat_text_off'][1]), self.v['wpn_atk_size'])
        self.pasteImage(img, "assets/hp.png", (offset[0]+self.v['wpn_stat_text_off'][0], offset[1]+self.v['wpn_stat_text_off'][1]+self.v['wpn_stat_line']), self.v['wpn_hp_size'])
        d.text((offset[0]+self.v['wpn_stat_text_off2'][0], offset[1]+self.v['wpn_stat_text_off2'][1]), "{}".format(export['watk']), fill=(255, 255, 255), font=self.font)
        d.text((offset[0]+self.v['wpn_stat_text_off2'][0], offset[1]+self.v['wpn_stat_text_off2'][1]+self.v['wpn_stat_line']), "{}".format(export['whp']), fill=(255, 255, 255), font=self.font)
        # estimated dama
        offset = (offset[0]+bsize[0]+self.v['estimate_off'][0], offset[1]+self.v['estimate_off'][1])
        if export['sps'] is not None and export['sps'] != '':
            # support summon
            print("Support summon is", export['sps'], ", searching its ID on the wiki...")
            supp = self.get_support_summon(export['sps'])
            if supp is None:
                print("No matches found")
                self.pasteImage(img, "assets/big_stat.png", (offset[0]-bsize[0]-self.v['estimate_off'][0], offset[1]), (bsize[0], self.v['big_stat'][1]))
                d.text((offset[0]-bsize[0]-self.v['estimate_off'][0]+self.v['est_sub_text'][0] , offset[1]+self.v['est_text']*2), "Support", fill=(255, 255, 255), font=self.font)
                if len(export['sps']) > 10: supp = export['sps'][:10] + "..."
                else: supp = export['sps']
                d.text((offset[0]-bsize[0]-self.v['estimate_off'][0]+self.v['est_sub_text'][0] , offset[1]+self.v['est_text']*2+self.v['stat_height']), supp, fill=(255, 255, 255), font=self.font)
            else:
                print("ID is", supp)
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(supp), (offset[0]-bsize[0]-self.v['estimate_off'][0]+self.v['supp_summon_off'], offset[1]), self.v['supp_summon'])
        est_width = ((size[0]*3)//2)
        for i in range(0, 2):
            self.pasteImage(img, "assets/big_stat.png", (offset[0]+est_width*i , offset[1]), (est_width+self.v['big_stat'][0], self.v['big_stat'][1]))
            d.text((offset[0]+self.v['est_text']+est_width*i, offset[1]+self.v['est_text']), "{}".format(export['est'][i+1]), fill=self.colors[int(export['est'][0])], font=self.big_font, stroke_width=self.v['stroke_width'], stroke_fill=(0, 0, 0))
            if i == 0:
                d.text((offset[0]+est_width*i+self.v['est_sub_text'][0] , offset[1]+self.v['est_sub_text'][1]), "Estimated", fill=(255, 255, 255), font=self.font)
            elif i == 1:
                if int(export['est'][0]) <= 4: vs = (int(export['est'][0]) + 2) % 4 + 1
                else: vs = (int(export['est'][0]) - 5 + 1) % 2 + 5
                d.text((offset[0]+est_width*i+self.v['est_sub_text'][0] , offset[1]+self.v['est_sub_text'][1]), "vs", fill=(255, 255, 255), font=self.font)
                d.text((offset[0]+est_width*i+self.v['est_sub_text_ele'] , offset[1]+self.v['est_sub_text'][1]), "{}".format(self.color_strs[vs]), fill=self.colors[vs], font=self.font)
        # modifiers
        print("Adding the", len(export['mods']), "modifier(s)")
        self.pasteImage(img, "assets/mod_bg.png", (mod_offset[0]-self.v['mod_off'], mod_offset[1]-self.v['mod_off']//2), self.v['mod_bg_size'])
        self.pasteImage(img, "assets/mod_bg_supp.png", (mod_offset[0]-self.v['mod_off'], mod_offset[1]-self.v['mod_off']+self.v['mod_bg_size'][1]), (self.v['mod_bg_supp_size'], self.v['mod_text_off'][1] * len(export['mods'])))
        for m in export['mods']:
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/weapon_skill_label/" + m['icon_img'], mod_offset, self.v['mod_size'])
            d.text((mod_offset[0], mod_offset[1]+self.v['mod_text_off'][0]), str(m['value']), fill=((255, 168, 38, 255) if m['is_max'] else (255, 255, 255, 255)), font=self.small_font)
            mod_offset = (mod_offset[0], mod_offset[1]+self.v['mod_text_off'][1])

    def make(self, fast=False):
        try:
            if not fast:
                print("Instructions:")
                print("1) Go to the party screen you want to export")
                print("2) Click your bookmarklet")
                print("3) Come back here and press Return to continue")
                input()
            clipboard = pyperclip.paste()
            export = json.loads(clipboard)
            if self.data.get('caching', False):
                self.checkDiskCache()
            self.cache = {}
            self.build_quality()
            
            img = Image.new('RGB', self.v['base'], "black")
            im_a = Image.new("L", img.size, "black")
            img.putalpha(im_a)
            im_a.close()
            d = ImageDraw.Draw(img, 'RGBA')

            # party
            self.pasteImage(img, "assets/characters.png", self.v['party_header'], self.v['header_size'])
            self.make_party(export, img, d, self.v['party_pos'])

            # summons
            self.pasteImage(img, "assets/summons.png", self.v['summon_header'], self.v['header_size'])
            self.make_summons(export, img, d, self.v['summon_pos'])

            # grid
            self.pasteImage(img, "assets/weapons.png", self.v['weapon_header'], self.v['header_size'])
            self.make_grid(export, img, d, self.v['weapon_pos'])
            
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
            print("[Any] Back")
            s = input()
            if s == "0":
                v = ({'720p':0, '1080p':1, '4K':2, '8K':3}[self.data.get('quality', '720p')] + 1) % 4
                self.data['quality'] = {0:'720p', 1:'1080p', 2:'4K', 3:'8K'}.get(v, 0)
            elif s == "1":
                v = ({'720p':0, '1080p':1, '4K':2, '8K':3}[self.data.get('quality', '720p')] + 1) % 4
                self.data['caching'] = not self.data.get('caching', False)
            else:
                return

    def cpyBookmark(self):
        pyperclip.copy("javascript:(function(){if(!window.location.hash.startsWith(\"#party/index/\")&&!window.location.hash.startsWith(\"#party/expectancy_damage/index\")&&!window.location.hash.startsWith(\"#tower/party/index/\")&&!(window.location.hash.startsWith(\"#event/sequenceraid\") && window.location.hash.indexOf(\"/party/index/\") > 0)&&!window.location.hash.startsWith(\"#tower/party/expectancy_damage/index/\")){alert('Please go to a GBF Party screen');return}let obj={p:parseInt(window.Game.view.deck_model.attributes.deck.pc.job.master.id,10),pcjs:window.Game.view.deck_model.attributes.deck.pc.param.image,ps:[],c:[],cl:[],cs:[],cp:[],cwr:[],s:[],sl:[],ss:[],se:[],sp:[],w:[],wl:[],wsn:[],wll:[],wp:[],wax:[],waxi:[],waxt:[],watk:window.Game.view.deck_model.attributes.deck.pc.weapons_attack,whp:window.Game.view.deck_model.attributes.deck.pc.weapons_hp,satk:window.Game.view.deck_model.attributes.deck.pc.summons_attack,shp:window.Game.view.deck_model.attributes.deck.pc.summons_hp,est:[window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage_attribute,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage,window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_advantage_damage],mods:window.Game.view.deck_model.attributes.deck.pc.damage_info.effect_value_info,sps:(window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name?window.Game.view.deck_model.attributes.deck.pc.damage_info.summon_name:null)};try{for(let i=0;i<4-window.Game.view.deck_model.attributes.deck.pc.set_action.length;i++){obj.ps.push(null)}Object.values(window.Game.view.deck_model.attributes.deck.pc.set_action).forEach(e=>{obj.ps.push(e.name?e.name.trim():null)})}catch(error){obj.ps=[null,null,null,null]};if(window.location.hash.startsWith(\"#tower/party/index/\")){Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(x=>{console.log(x);Object.values(x).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null)})})}else{Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id,10):null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null)})}Object.values(window.Game.view.deck_model.attributes.deck.pc.summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.sub_summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.se.push(e.param?parseInt(e.param.evolution,10):null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.weapons).forEach(e=>{obj.w.push(e.master?parseInt(e.master.id.slice(0,-2),10):null);obj.wl.push(e.param?parseInt(e.param.skill_level,10):null);obj.wsn.push(e.param?[e.skill1?e.skill1.image:null,e.skill2?e.skill2.image:null,e.skill3?e.skill3.image:null]:null);obj.wll.push(e.param?parseInt(e.param.level,10):null);obj.wp.push(e.param?parseInt(e.param.quality,10):null);obj.waxt.push(e.param?e.param.augment_image:null);obj.waxi.push(e.param?e.param.augment_skill_icon_image:null);obj.wax.push(e.param?e.param.augment_skill_info:null)});let copyListener=event=>{document.removeEventListener(\"copy\",copyListener,true);event.preventDefault();let clipboardData=event.clipboardData;clipboardData.clearData();clipboardData.setData(\"text/plain\",JSON.stringify(obj))};document.addEventListener(\"copy\",copyListener,true);document.execCommand(\"copy\");}())")

    def run(self):
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

class Interface(Tk.Tk):
    def __init__(self, pb, ver):
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.pb = pb
        self.apprunning = True
        self.iconbitmap('icon.ico')
        self.title("GBFPIB {}".format(ver))
        #self.minsize(200, 80)
        self.resizable(width=False, height=False) # not resizable
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        
        # run
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=0, sticky="we")
        tabcontent = Tk.Frame(tabs)
        tabs.add(tabcontent, text="Run")
        self.button = Tk.Button(tabcontent, text="Build Image", command=self.build)
        self.button.grid(row=0, column=0, sticky="we")
        Tk.Button(tabcontent, text="Get Bookmarklet", command=self.bookmark).grid(row=1, column=0, sticky="we")
        
        # setting
        tabs = ttk.Notebook(self)
        tabs.grid(row=1, column=1, sticky="we")
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

if __name__ == "__main__":
    ver = "v2.5"
    if '-fast' in sys.argv:
        print("Granblue Fantasy Party Image Builder", ver)
        pb = PartyBuilder()
        pb.make(fast=True)
        if '-nowait' not in sys.argv:
            print("Closing in 10 seconds...")
            time.sleep(10)
    else:
        ui = Interface(PartyBuilder(), ver)
        ui.run()