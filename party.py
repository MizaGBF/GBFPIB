from urllib import request, parse
from urllib.parse import unquote
import json
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import pyperclip
import json

class PartyBuilder():
    def __init__(self):
        self.big_font = None
        self.font = None
        self.small_font = None
        self.cache = {}
        self.colors = {
            1:(243, 48, 33),
            2:(50, 159, 222),
            3:(186, 108, 39),
            4:(40, 172, 45),
            5:(253, 216, 67),
            6:(130, 75, 177),
        }
        self.color_strs = {
            1:"Fire",
            2:"Water",
            3:"Earth",
            4:"Wind",
            5:"Light",
            6:"Dark",
        }
        self.v = {
            '720p' : {
                'font': [14, 16, 30],
                'stroke_width': 1,
                'base': (547, 720),
                'party_header': (10, 10),
                'summon_header': (10, 150),
                'weapon_header': (10, 320),
                'header_size': (92, 25),
                'party_pos': (10, 45),
                'summon_pos': (150, 185),
                'weapon_pos': (10, 355),
                'chara_size': (55, 100),
                'chara_size_babyl': (39, 71),
                'chara_babyl_off': 5,
                'chara_plus_babyl_offset': (-30, -20),
                'skill_width': 140,
                'bg_offset': -5,
                'bg_end_offset': (10, 40),
                'bg_end_offset2': (10, 56),
                'bg_end_offset3': (20, 400),
                'bg_end_offset4': (20, 500),
                'job_size': (24, 20),
                'ring_size': (30, 30),
                'ring_offset': -2,
                'chara_plus_offset': (-48, -22),
                'stat_height': 20,
                'text_offset': (4, 2),
                'sub_skill_bg': (140, 49),
                'sub_skill_text_off': 1,
                'sub_skill_text_space': 16,
                'summon_size': (50, 105),
                'summon_plus_offset': (-35, -20),
                'sum_level_text_off': (2, 3),
                'sum_atk_size': (30, 13),
                'sum_hp_size': (22, 13),
                'sum_stat_offsets': [3, 30, 40, 100],
                'skill_box_height': 48,
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
                'est_sub_text_ele': 22
            },
            '1080p' : {
                'font': [21, 24, 45],
                'stroke_width': 2,
                'base': (820, 1080),
                'party_header': (15, 15),
                'summon_header': (15, 225),
                'weapon_header': (15, 480),
                'header_size': (138, 37),
                'party_pos': (15, 67),
                'summon_pos': (225, 277),
                'weapon_pos': (15, 532),
                'chara_size': (82, 150),
                'chara_size_babyl': (58, 106),
                'chara_babyl_off': 7,
                'chara_plus_babyl_offset': (-45, -30),
                'skill_width': 210,
                'bg_offset': -8,
                'bg_end_offset': (15, 60),
                'bg_end_offset2': (15, 84),
                'bg_end_offset3': (30, 600),
                'bg_end_offset4': (30, 750),
                'job_size': (36, 30),
                'ring_size': (45, 45),
                'ring_offset': -3,
                'chara_plus_offset': (-72, -33),
                'stat_height': 30,
                'text_offset': (6, 3),
                'sub_skill_bg': (210, 72),
                'sub_skill_text_off': 2,
                'sub_skill_text_space': 24,
                'summon_size': (75, 157),
                'summon_plus_offset': (-47, -30),
                'sum_level_text_off': (3, 5),
                'sum_atk_size': (45, 20),
                'sum_hp_size': (33, 20),
                'sum_stat_offsets': [5, 45, 60, 150],
                'skill_box_height': 72,
                'mh_size': (150, 315),
                'sub_size': (144, 82),
                'wpn_separator': 7,
                'weapon_plus_offset': (-52, -30),
                'skill_lvl_off': [-25, 7],
                'ax_text_off': [3, 7],
                'wpn_stat_off': 75,
                'wpn_stat_line': 37,
                'wpn_atk_size': (45, 20),
                'wpn_hp_size': (33, 20),
                'wpn_stat_text_off': (5, 7),
                'wpn_stat_text_off2': (55, 7),
                'estimate_off': (7, 82),
                'big_stat': (-7, 75),
                'est_text': 5,
                'est_sub_text': (7, 45),
                'est_sub_text_ele': 33
            },
            '4K' : {
                'font': [42, 48, 90],
                'stroke_width': 3,
                'base': (1641, 2160),
                'party_header': (30, 30),
                'summon_header': (30, 450),
                'weapon_header': (30, 960),
                'header_size': (276, 75),
                'party_pos': (30, 135),
                'summon_pos': (450, 555),
                'weapon_pos': (30, 1065),
                'chara_size': (165, 300),
                'chara_size_babyl': (117, 213),
                'chara_babyl_off': 15,
                'chara_plus_babyl_offset': (-150, -60),
                'skill_width': 420,
                'bg_offset': -15,
                'bg_end_offset': (30, 120),
                'bg_end_offset2': (30, 168),
                'bg_end_offset3': (60, 1200),
                'bg_end_offset4': (60, 1500),
                'job_size': (72, 60),
                'ring_size': (90, 90),
                'ring_offset': -6,
                'chara_plus_offset': (-144, -66),
                'stat_height': 60,
                'text_offset': (12, 6),
                'sub_skill_bg': (420, 147),
                'sub_skill_text_off': 3,
                'sub_skill_text_space': 48,
                'summon_size': (150, 315),
                'summon_plus_offset': (-105, -60),
                'sum_level_text_off': (6, 9),
                'sum_atk_size': (90, 39),
                'sum_hp_size': (66, 39),
                'sum_stat_offsets': [9, 90, 120, 300],
                'skill_box_height': 144,
                'mh_size': (300, 630),
                'sub_size': (288, 165),
                'wpn_separator': 15,
                'weapon_plus_offset': (-105, -65),
                'skill_lvl_off': [-51, 15],
                'ax_text_off': [6, 15],
                'wpn_stat_off': 150,
                'wpn_stat_line': 75,
                'wpn_atk_size': (90, 39),
                'wpn_hp_size': (66, 39),
                'wpn_stat_text_off': (9, 15),
                'wpn_stat_text_off2': (111, 15),
                'estimate_off': (15, 165),
                'big_stat': (-15, 150),
                'est_text': 9,
                'est_sub_text': (15, 90),
                'est_sub_text_ele': 66
            }
        }
        self.data = {}
        self.load()

    def load(self):
        try:
            with open('settings.json') as f:
                self.data = json.load(f)
        except Exception as e:
            print("Failed to load settings.json")
            while True:
                print("An empty config.json file will be created, continue? (y/n)")
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

    def pasteImage(self, img, file, offset, resize=None): # paste and image onto another
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize, Image.LANCZOS))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    def dlAndPasteImage(self, img, url, offset, resize=None): # dl an image and call pasteImage()
        if url not in self.cache:
            req = request.Request(url)
            url_handle = request.urlopen(req)
            self.cache[url] = url_handle.read()
            url_handle.close()
        with BytesIO(self.cache[url]) as file_jpgdata:
            self.pasteImage(img, file_jpgdata, offset, resize)

    def draw_rect(self, d, x, y, w, h): # to draw placholders
        d.rectangle([(x, y), (x+w-1, y+h-1)], fill=(0, 0, 0, 200))

    def get_uncap_id(self, cs): # to get character portraits based on uncap levels
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def make_party_babyl(self, export, img, d, offset): # draw the tower of babyl parties
        Q = self.data.get('quality', '720p')
        csize = self.v[Q]['chara_size_babyl']
        # background
        for i in range(0, 3):
            self.pasteImage(img, "assets/bg.png", (offset[0]+self.v[Q]['bg_offset']+i*(self.v[Q]['chara_babyl_off']+4*csize[0]), offset[1]+self.v[Q]['bg_offset']), (csize[0]*4+self.v[Q]['bg_end_offset'][0], csize[1]+self.v[Q]['bg_end_offset'][1]+self.v[Q]['bg_offset']))
        # mc
        self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/quest/{}.jpg".format(export['pcjs']), (offset[0], offset[1]), csize)
        self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), (offset[0], offset[1]), self.v[Q]['job_size'])
        for i in range(0, 11): # npcs
            pos = (offset[0]+csize[0]*(i+1)+((i+1)//4)*self.v[Q]['chara_babyl_off'], offset[1])
            # portrait
            if i >= len(export['c']) or export['c'][i] is None:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/deckcombination/base_empty_npc.jpg", pos, csize)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/quest/{}000_{}.jpg".format(export['c'][i], self.get_uncap_id(export['cs'][i])), pos, csize)
            # rings
            if export['cwr'][i] == True:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (pos[0]+self.v[Q]['ring_offset'], pos[1]+self.v[Q]['ring_offset']), self.v[Q]['ring_size'])
            # plus
            if export['cp'][i] > 0:
                d.text((pos[0]+csize[0]+self.v[Q]['chara_plus_babyl_offset'][0], pos[1]+csize[1]+self.v[Q]['chara_plus_babyl_offset'][1]), "{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.small_font, stroke_width=self.v[Q]['stroke_width'], stroke_fill=(0, 0, 0))
            # level
            self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+csize[1]), (csize[0], self.v[Q]['stat_height']))
            d.text((pos[0]+self.v[Q]['text_offset'][0], pos[1]+csize[1]+self.v[Q]['text_offset'][1]), "{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.small_font)

    def make_party(self, export, img, d, offset): # draw the party
        Q = self.data.get('quality', '720p')
        csize = self.v[Q]['chara_size']
        skill_width = self.v[Q]['skill_width']
        # background
        self.pasteImage(img, "assets/bg.png", (offset[0]+skill_width+self.v[Q]['bg_offset'], offset[1]+self.v[Q]['bg_offset']), (csize[0]*6+self.v[Q]['bg_end_offset'][0], csize[1]+self.v[Q]['bg_end_offset'][1]))
        # mc
        self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/quest/{}.jpg".format(export['pcjs']), (offset[0]+skill_width, offset[1]), csize)
        self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), (offset[0]+skill_width, offset[1]), self.v[Q]['job_size'])
        for i in range(0, 5): # npcs
            pos = (offset[0]+skill_width+csize[0]*(i+1), offset[1])
            # portrait
            if export['c'][i] is None:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/deckcombination/base_empty_npc.jpg", pos, csize)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/quest/{}000_{}.jpg".format(export['c'][i], self.get_uncap_id(export['cs'][i])), pos, csize)
            # rings
            if export['cwr'][i] == True:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (pos[0]+self.v[Q]['ring_offset'], pos[1]+self.v[Q]['ring_offset']), self.v[Q]['ring_size'])
            # plus
            if export['cp'][i] > 0:
                d.text((pos[0]+csize[0]+self.v[Q]['chara_plus_offset'][0], pos[1]+csize[1]+self.v[Q]['chara_plus_offset'][1]), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=self.v[Q]['stroke_width'], stroke_fill=(0, 0, 0))
            # level
            self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+csize[1]), (csize[0], self.v[Q]['stat_height']))
            d.text((pos[0]+self.v[Q]['text_offset'][0], pos[1]+csize[1]+self.v[Q]['text_offset'][1]), "Lv{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.font)
        # mc sub skills
        self.pasteImage(img, "assets/subskills.png", (offset[0], offset[1]), self.v[Q]['sub_skill_bg'])
        count = 0
        for i in range(len(export['ps'])):
            if export['ps'][i] is not None:
                d.text((offset[0]+self.v[Q]['sub_skill_text_off'], offset[1]+self.v[Q]['sub_skill_text_off']+self.v[Q]['sub_skill_text_space']*count), export['ps'][i], fill=(255, 255, 255), font=self.font)
                count += 1

    def make_summons(self, export, img, d, offset): # draw the summons
        Q = self.data.get('quality', '720p')
        ssize = self.v[Q]['summon_size']
        # background
        self.pasteImage(img, "assets/bg.png", (offset[0]+self.v[Q]['bg_offset'], offset[1]+self.v[Q]['bg_offset']), (ssize[0]*5+self.v[Q]['bg_end_offset2'][0], ssize[1]+self.v[Q]['bg_end_offset2'][1]))
        for i in range(0, 5):
            pos = (offset[0]+ssize[0]*i, offset[1])
            # portraits
            if export['s'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/2999999999.jpg", pos, ssize)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/{}.jpg".format(export['ss'][i]), pos, ssize)
            # plus
            if export['sp'][i] > 0:
                d.text((pos[0]+ssize[0]+self.v[Q]['summon_plus_offset'][0], pos[1]+ssize[1]+self.v[Q]['summon_plus_offset'][1]), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=self.v[Q]['stroke_width'], stroke_fill=(0, 0, 0))
            # level
            self.pasteImage(img, "assets/chara_stat.png", (pos[0], pos[1]+ssize[1]), (ssize[0], self.v[Q]['stat_height']))
            d.text((pos[0]+self.v[Q]['sum_level_text_off'][0], pos[1]+ssize[1]+self.v[Q]['sum_level_text_off'][1]), "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.small_font)
        # stats
        self.pasteImage(img, "assets/chara_stat.png", (offset[0], offset[1]+ssize[1]+self.v[Q]['stat_height']), (ssize[0]*2, self.v[Q]['stat_height']))
        self.pasteImage(img, "assets/chara_stat.png", (offset[0]+ssize[0]*2, offset[1]+ssize[1]+self.v[Q]['stat_height']), (ssize[0]*2, self.v[Q]['stat_height']))
        self.pasteImage(img, "assets/atk.png", (offset[0]+self.v[Q]['sum_stat_offsets'][0], offset[1]+ssize[1]+self.v[Q]['stat_height']+self.v[Q]['sum_stat_offsets'][0]), self.v[Q]['sum_atk_size'])
        self.pasteImage(img, "assets/hp.png", (offset[0]+self.v[Q]['sum_stat_offsets'][0]+self.v[Q]['sum_stat_offsets'][3], offset[1]+ssize[1]+self.v[Q]['stat_height']+self.v[Q]['sum_stat_offsets'][0]), self.v[Q]['sum_hp_size'])
        d.text((offset[0]+self.v[Q]['sum_stat_offsets'][2], offset[1]+ssize[1]+self.v[Q]['stat_height']+self.v[Q]['sum_stat_offsets'][0]), "{}".format(export['satk']), fill=(255, 255, 255), font=self.small_font)
        d.text((offset[0]+self.v[Q]['sum_stat_offsets'][3]+self.v[Q]['sum_stat_offsets'][1], offset[1]+ssize[1]+self.v[Q]['stat_height']+self.v[Q]['sum_stat_offsets'][0]), "{}".format(export['shp']), fill=(255, 255, 255), font=self.small_font)

    def make_grid(self, export, img, d, base_offset): # draw the weapons (sandbox is supported)
        Q = self.data.get('quality', '720p')
        skill_box_height = self.v[Q]['skill_box_height']
        skill_icon_size = skill_box_height // 2
        ax_separator = skill_box_height
        mh_size = self.v[Q]['mh_size']
        sub_size = self.v[Q]['sub_size']
        if len(export['w']) <= 10:
            base_offset = (base_offset[0] + sub_size[0], base_offset[1])
        # background
        if len(export['w']) > 10:
            self.pasteImage(img, "assets/grid_bg.png", (base_offset[0]+self.v[Q]['bg_offset'], base_offset[1]+self.v[Q]['bg_offset']), (mh_size[0]+4*sub_size[0]+self.v[Q]['bg_end_offset4'][0], self.v[Q]['bg_end_offset4'][1]))
        else:
            self.pasteImage(img, "assets/grid_bg.png", (base_offset[0]+self.v[Q]['bg_offset'], base_offset[1]+self.v[Q]['bg_offset']), (mh_size[0]+3*sub_size[0]+self.v[Q]['bg_end_offset3'][0], self.v[Q]['bg_end_offset3'][1]))
        # weapons
        for i in range(0, len(export['w'])):
            wt = "ls" if i == 0 else "m"
            if i == 0: # mainhand
                offset = (base_offset[0], base_offset[1])
                size = mh_size
                bsize = size
            elif i >= 10: # sandbox
                x = 3
                y = (i-1) % 3
                size = sub_size
                offset = (base_offset[0]+bsize[0]+self.v[Q]['wpn_separator']+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
            else: # others
                x = (i-1) % 3
                y = (i-1) // 3
                size = sub_size
                offset = (base_offset[0]+bsize[0]+self.v[Q]['wpn_separator']+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
            if export['w'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt), offset, size)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/{}00.jpg".format(wt, export['w'][i]), offset, size)
            # skill box
            self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]+size[1]), (size[0], skill_box_height//2))
            if len(export['waxi'][i]) > 0:
                self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]+size[1]+skill_box_height//2), (size[0], skill_box_height//2))
            # plus
            if export['wp'][i] > 0:
                if i == 0:
                    d.text((offset[0]+size[0]+self.v[Q]['weapon_plus_offset'][0], offset[1]+size[1]+self.v[Q]['weapon_plus_offset'][1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=self.v[Q]['stroke_width'], stroke_fill=(0, 0, 0))
                else:
                    d.text((offset[0]+size[0]+self.v[Q]['weapon_plus_offset'][0], offset[1]+size[1]+self.v[Q]['weapon_plus_offset'][1]), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=self.v[Q]['stroke_width'], stroke_fill=(0, 0, 0))
            # skill level
            if export['wl'][i] is not None and export['wl'][i] > 1:
                d.text((offset[0]+skill_icon_size*3+self.v[Q]['skill_lvl_off'][0], offset[1]+size[1]+self.v[Q]['skill_lvl_off'][1]), "SL {}".format(export['wl'][i]), fill=(255, 255, 255), font=self.small_font)
            # skill icon
            for j in range(3):
                if export['wsn'][i][j] is not None:
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (offset[0]+skill_icon_size*j, offset[1]+size[1]), (skill_icon_size, skill_icon_size))
            # ax skills
            if len(export['waxt'][i]) > 0:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment_skill/{}.png".format(export['waxt'][i][0]), (offset[0], offset[1]), (skill_icon_size, skill_icon_size))
                for j in range(len(export['waxi'][i])):
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]), (offset[0]+ax_separator*j, offset[1]+size[1]+skill_icon_size), (skill_icon_size, skill_icon_size))
                    d.text((offset[0]+ax_separator*j+skill_icon_size+self.v[Q]['ax_text_off'][0], offset[1]+size[1]+skill_icon_size+self.v[Q]['ax_text_off'][1]), "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''), fill=(255, 255, 255), font=self.small_font)
        # sandbox tag
        if len(export['w']) > 10:
            sandbox = (size[0], int(66*size[0]/159))
            self.pasteImage(img, "assets/sandbox.png", (offset[0], base_offset[1]-sandbox[1]), sandbox)
        # stats
        offset = (base_offset[0], base_offset[1]+bsize[1]+self.v[Q]['wpn_stat_off'])
        self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]), (bsize[0], self.v[Q]['wpn_stat_line']))
        self.pasteImage(img, "assets/skill.png", (offset[0], offset[1]+self.v[Q]['wpn_stat_line']), (bsize[0], self.v[Q]['wpn_stat_line']))
        self.pasteImage(img, "assets/atk.png", (offset[0]+self.v[Q]['wpn_stat_text_off'][0], offset[1]+self.v[Q]['wpn_stat_text_off'][1]), self.v[Q]['wpn_atk_size'])
        self.pasteImage(img, "assets/hp.png", (offset[0]+self.v[Q]['wpn_stat_text_off'][0], offset[1]+self.v[Q]['wpn_stat_text_off'][1]+self.v[Q]['wpn_stat_line']), self.v[Q]['wpn_hp_size'])
        d.text((offset[0]+self.v[Q]['wpn_stat_text_off2'][0], offset[1]+self.v[Q]['wpn_stat_text_off2'][1]), "{}".format(export['watk']), fill=(255, 255, 255), font=self.font)
        d.text((offset[0]+self.v[Q]['wpn_stat_text_off2'][0], offset[1]+self.v[Q]['wpn_stat_text_off2'][1]+self.v[Q]['wpn_stat_line']), "{}".format(export['whp']), fill=(255, 255, 255), font=self.font)
        # estimated
        offset = (offset[0]+bsize[0]+self.v[Q]['estimate_off'][0], offset[1]+self.v[Q]['estimate_off'][1])
        est_width = ((size[0]*3)//2)
        for i in range(0, 2):
            self.pasteImage(img, "assets/big_stat.png", (offset[0]+est_width*i , offset[1]), (est_width+self.v[Q]['big_stat'][0], self.v[Q]['big_stat'][1]))
            d.text((offset[0]+self.v[Q]['est_text']+est_width*i, offset[1]+self.v[Q]['est_text']), "{}".format(export['est'][i+1]), fill=self.colors[export['est'][0]], font=self.big_font, stroke_width=self.v[Q]['stroke_width'], stroke_fill=(0, 0, 0))
            if i == 0:
                d.text((offset[0]+est_width*i+self.v[Q]['est_sub_text'][0] , offset[1]+self.v[Q]['est_sub_text'][1]), "Estimated", fill=(255, 255, 255), font=self.font)
            elif i == 1:
                if export['est'][0] <= 4: vs = (export['est'][0] + 2) % 4 + 1
                else: vs = (export['est'][0] - 5 + 1) % 2 + 5
                d.text((offset[0]+est_width*i+self.v[Q]['est_sub_text'][0] , offset[1]+self.v[Q]['est_sub_text'][1]), "vs", fill=(255, 255, 255), font=self.font)
                d.text((offset[0]+est_width*i+self.v[Q]['est_sub_text_ele'] , offset[1]+self.v[Q]['est_sub_text'][1]), "{}".format(self.color_strs[vs]), fill=self.colors[vs], font=self.font)
                

    def make(self):
        print("Instructions:")
        print("1) Go to the party screen you want to export")
        print("2) Click your bookmarklet")
        print("3) Come back here and press Return to continue")
        try:
            input()
            clipboard = pyperclip.paste()
            export = json.loads(clipboard)
            self.cache = {}
            Q = self.data.get('quality', '720p')
            self.big_font = ImageFont.truetype("assets/basic.ttf", self.v[Q]['font'][2])
            self.font = ImageFont.truetype("assets/basic.ttf", self.v[Q]['font'][1])
            self.small_font = ImageFont.truetype("assets/basic.ttf", self.v[Q]['font'][0])
            
            img = Image.new('RGB', self.v[Q]['base'], "black")
            im_a = Image.new("L", img.size, "black")
            img.putalpha(im_a)
            im_a.close()
            d = ImageDraw.Draw(img, 'RGBA')
            # party
            self.pasteImage(img, "assets/characters.png", self.v[Q]['party_header'], self.v[Q]['header_size'])
            if len(export['c']) > 5:
                self.make_party_babyl(export, img, d, self.v[Q]['party_pos'])
            else:
                self.make_party(export, img, d, self.v[Q]['party_pos'])

            # summons
            self.pasteImage(img, "assets/summons.png", self.v[Q]['summon_header'], self.v[Q]['header_size'])
            self.make_summons(export, img, d, self.v[Q]['summon_pos'])

            # grid
            self.pasteImage(img, "assets/weapons.png", self.v[Q]['weapon_header'], self.v[Q]['header_size'])
            self.make_grid(export, img, d, self.v[Q]['weapon_pos'])

            img.save("party.png", "PNG")
            img.close()
            print("Success, party.png has been generated")
        except Exception as e:
            print("An error occured")
            print("exception message:", e)
            print("Did you follow the instructions?")

    def settings(self):
        while True:
            print("")
            print("Settings:")
            print("[0] Change quality (Current:", self.data.get('quality', '720p'),")")
            print("[Any] Back")
            s = input()
            if s == "0":
                v = ({'720p':0, '1080p':1, '4K':2}[self.data.get('quality', '720p')] + 1) % 3
                self.data['quality'] = {0:'720p', 1:'1080p', 2:'4K'}.get(v, 0)
            else:
                return

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
                    pyperclip.copy("javascript:(function(){if(!window.location.hash.startsWith(\"#party/index/\")){alert('Please go to a GBF Party screen');return}let obj={p:parseInt(window.Game.view.deck_model.attributes.deck.pc.job.master.id,10),pcjs:window.Game.view.deck_model.attributes.deck.pc.param.image,ps:[],c:[],cl:[],cs:[],cp:[],cwr:[],s:[],sl:[],ss:[],sp:[],w:[],wl:[],wsn:[],wll:[],wp:[],wax:[],waxi:[],waxt:[],watk:window.Game.view.deck_model.attributes.deck.pc.weapons_attack,whp:window.Game.view.deck_model.attributes.deck.pc.weapons_hp,satk:window.Game.view.deck_model.attributes.deck.pc.summons_attack,shp:window.Game.view.deck_model.attributes.deck.pc.summons_attack,est:[window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage_attribute, window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage, window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_advantage_damage]};try {for(let i=0;i<4-window.Game.view.deck_model.attributes.deck.pc.set_action.length;i++){obj.ps.push(null)}Object.values(window.Game.view.deck_model.attributes.deck.pc.set_action).forEach(e=>{obj.ps.push(e.name?e.name.trim():null)});} catch (error) {obj.ps = [null, null, null, null]};Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.weapons).forEach(e=>{obj.w.push(e.master?parseInt(e.master.id.slice(0,-2),10):null);obj.wl.push(e.param?parseInt(e.param.skill_level,10):null);obj.wsn.push(e.param?[e.skill1?e.skill1.image:null,e.skill2?e.skill2.image:null,e.skill3?e.skill3.image:null]:null);obj.wll.push(e.param?parseInt(e.param.level,10):null);obj.wp.push(e.param?parseInt(e.param.quality,10):null);obj.waxt.push(e.param?e.param.augment_image:null);obj.waxi.push(e.param?e.param.augment_skill_icon_image:null);obj.wax.push(e.param?e.param.augment_skill_info:null)});let copyListener = event => { document.removeEventListener(\"copy\", copyListener, true); event.preventDefault(); let clipboardData = event.clipboardData; clipboardData.clearData(); clipboardData.setData(\"text/plain\", JSON.stringify(obj)); }; document.addEventListener(\"copy\", copyListener, true); document.execCommand(\"copy\");}())")
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

if __name__ == "__main__":
    print("Granblue Fantasy Party Image Builder v1.7")
    PartyBuilder().run()