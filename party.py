from urllib import request, parse
from urllib.parse import unquote
import json
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import pyperclip

class PartyBuilder():
    def __init__(self):
        self.big_font = ImageFont.truetype("assets/basic.ttf", 30)
        self.font = ImageFont.truetype("assets/basic.ttf", 16)
        self.small_font = ImageFont.truetype("assets/basic.ttf", 14)
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

    def pasteImage(self, img, file, offset, resize=None):
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize, Image.LANCZOS))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    def dlAndPasteImage(self, img, url, offset, resize=None):
        if url not in self.cache:
            req = request.Request(url)
            url_handle = request.urlopen(req)
            self.cache[url] = url_handle.read()
            url_handle.close()
        with BytesIO(self.cache[url]) as file_jpgdata:
            self.pasteImage(img, file_jpgdata, offset, resize)

    def draw_rect(self, d, x, y, w, h):
        d.rectangle([(x, y), (x+w-1, y+h-1)], fill=(0, 0, 0, 200))

    def get_uncap_id(self, cs):
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def make_party(self, export, img, d, offset):
        csize = (55, 100)
        skill_width = 140
        # mc
        self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/quest/{}.jpg".format(export['pcjs']), (offset[0]+skill_width, offset[1]), csize)
        self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), (offset[0]+skill_width, offset[1]), (24, 20))
        for i in range(0, 5): # npcs
            # portrait
            if export['c'][i] is None:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/deckcombination/base_empty_npc.jpg", (offset[0]+skill_width+78*(i+1), offset[1]), csize)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/quest/{}000_{}.jpg".format(export['c'][i], self.get_uncap_id(export['cs'][i])), (offset[0]+skill_width+csize[0]*(i+1), offset[1]), csize)
            # rings
            if export['cwr'][i] == True:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (offset[0]+skill_width+csize[0]*(i+1)-2, offset[1]-2), (30, 30))
            # plus
            if export['cp'][i] > 0:
                d.text((offset[0]+skill_width+csize[0]*(i+2)-48, offset[1]+csize[1]-22), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
            # level
            self.draw_rect(d, offset[0]+skill_width+csize[0]*(i+1), offset[1]+csize[1], csize[0], 20)
            d.text((offset[0]+skill_width+4+csize[0]*(i+1), offset[1]+csize[1]+2), "Lv{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.font)
        # mc sub skills
        for i in range(len(export['ps'])):
            self.draw_rect(d, offset[0], offset[1]+20*i, skill_width, 20)
            d.text((offset[0]+1, offset[1]+2+20*i), export['ps'][i], fill=(255, 255, 255), font=self.font)

    def make_summons(self, export, img, d, offset):
        ssize = (50, 105)
        for i in range(0, 5):
            # portraits
            if export['s'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/2999999999.jpg", (offset[0]+50*i, offset[1]), ssize)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/{}.jpg".format(export['ss'][i]), (offset[0]+50*i, offset[1]), ssize)
            # plus
            if export['sp'][i] > 0:
                d.text((offset[0]+ssize[0]*(i+1)-35, offset[1]+ssize[1]-20), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
            # level
            self.draw_rect(d, offset[0]+ssize[0]*i, offset[1]+ssize[1], ssize[0], 20)
            d.text((offset[0]+2+ssize[0]*i, offset[1]+ssize[1]+3), "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.small_font)
        # stats
        self.draw_rect(d, offset[0], offset[1]+ssize[1]+20, ssize[0]*4, 20)
        self.pasteImage(img, "assets/atk.png", (offset[0]+3, offset[1]+ssize[1]+20+3), (30, 13))
        self.pasteImage(img, "assets/hp.png", (offset[0]+3+100, offset[1]+ssize[1]+20+3), (22, 13))
        d.text((offset[0]+40, offset[1]+ssize[1]+20+3), "{}".format(export['satk']), fill=(255, 255, 255), font=self.small_font)
        d.text((offset[0]+100+30, offset[1]+ssize[1]+20+3), "{}".format(export['shp']), fill=(255, 255, 255), font=self.small_font)

    def make_grid(self, export, img, d, base_offset):
        skill_box_height = 48
        skill_icon_size = skill_box_height // 2
        ax_separator = 48
        # weapons
        for i in range(0, len(export['w'])):
            wt = "ls" if i == 0 else "m"
            if i == 0: # mainhand
                offset = (base_offset[0], base_offset[1])
                size = (100, 210)
                bsize = size
            elif i >= 10: # sandbox
                x = 3
                y = (i-1) % 3
                size = (96, 55)
                offset = (base_offset[0]+bsize[0]+5+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
            else: # others
                x = (i-1) % 3
                y = (i-1) // 3
                size = (96, 55)
                offset = (base_offset[0]+bsize[0]+5+size[0]*x, base_offset[1]+(size[1]+skill_box_height)*y)
            if export['w'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt), offset, size)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/{}00.jpg".format(wt, export['w'][i]), offset, size)
            # skill box
            if len(export['waxi'][i]) > 0:
                self.draw_rect(d, offset[0], offset[1]+size[1], size[0], skill_box_height)
            else:
                self.draw_rect(d, offset[0], offset[1]+size[1], size[0], skill_box_height // 2)
            # plus
            if export['wp'][i] > 0:
                if i == 0:
                    d.text((offset[0]+size[0]-30, offset[1]+size[1]-20), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
                else:
                    d.text((offset[0]+size[0]-30, offset[1]+size[1]-20), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
            # skill level
            if export['wl'][i] is not None and export['wl'][i] > 1:
                d.text((offset[0]+skill_icon_size*3-17, offset[1]+size[1]+5), "SL {}".format(export['wl'][i]), fill=(255, 255, 255), font=self.small_font)
            # skill icon
            for j in range(3):
                if export['wsn'][i][j] is not None:
                    self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (offset[0]+skill_icon_size*j, offset[1]+size[1]), (skill_icon_size, skill_icon_size))
            # ax skills
            for j in range(len(export['waxi'][i])):
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]), (offset[0]+ax_separator*j, offset[1]+size[1]+skill_icon_size), (skill_icon_size, skill_icon_size))
                d.text((offset[0]+ax_separator*j+skill_icon_size+2, offset[1]+size[1]+skill_icon_size+5), "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''), fill=(255, 255, 255), font=self.small_font)
        # sandbox tag
        if len(export['w']) > 10:
            sandbox = (size[0], int(66*size[0]/159))
            self.pasteImage(img, "assets/sandbox.png", (offset[0], base_offset[1]-sandbox[1]), sandbox) # 159 66
        # stats
        offset = (base_offset[0], base_offset[1]+bsize[1]+50)
        self.draw_rect(d, offset[0], offset[1], bsize[0], 49)
        self.pasteImage(img, "assets/atk.png", offset, (30, 13))
        self.pasteImage(img, "assets/hp.png", (offset[0], offset[1]+25), (22, 13))
        d.text((offset[0]+35, offset[1]+5), "{}".format(export['watk']), fill=(255, 255, 255), font=self.font)
        d.text((offset[0]+35, offset[1]+5+25), "{}".format(export['whp']), fill=(255, 255, 255), font=self.font)
        # estimated
        offset = (offset[0]+bsize[0]+5, offset[1]+55)
        est_width = ((size[0]*3)//2)
        for i in range(0, 2):
            self.draw_rect(d, offset[0]+est_width*i , offset[1], est_width-5, 50)
            d.text((offset[0]+3+est_width*i+1, offset[1]+3), "{}".format(export['est'][i+1]), fill=(0, 0, 0), font=self.big_font)
            d.text((offset[0]+3+est_width*i, offset[1]+3), "{}".format(export['est'][i+1]), fill=self.colors[export['est'][0]], font=self.big_font)
            if i == 0:
                d.text((offset[0]+est_width*i+5 , offset[1]+30), "Estimated", fill=(255, 255, 255), font=self.font)
            elif i == 1:
                if export['est'][0] <= 4: vs = (export['est'][0] + 2) % 4 + 1
                else: vs = (export['est'][0] - 5 + 1) % 2 + 5
                d.text((offset[0]+est_width*i+5 , offset[1]+30), "vs", fill=(255, 255, 255), font=self.font)
                d.text((offset[0]+est_width*i+22 , offset[1]+30), "{}".format(self.color_strs[vs]), fill=self.colors[vs], font=self.font)

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
            
            img = Image.new('RGB', (547, 720), "black")
            im_a = Image.new("L", img.size, "black")
            img.putalpha(im_a)
            im_a.close()
            d = ImageDraw.Draw(img, 'RGBA')
            # party
            self.pasteImage(img, "assets/characters.png", (10, 10), (92, 25))
            self.make_party(export, img, d, (10, 45))

            # summons
            self.pasteImage(img, "assets/summons.png", (10, 150), (92, 25))
            self.make_summons(export, img, d, (150, 185))

            # grid
            self.pasteImage(img, "assets/weapons.png", (10, 320), (92, 25))
            self.make_grid(export, img, d, (10, 355))


            img.save("party.png", "PNG")
            img.close()
            print("Success, party.png has been generated")
        except Exception as e:
            print("An error occured")
            print("exception message:", e)
            print("Did you follow the instructions?")

    def run(self):
        while True:
            print("")
            print("Main Menu:")
            print("[0] Generate Image")
            print("[1] Get Bookmarklet")
            print("[Any] Exit")
            s = input()
            if s == "0":
                self.make()
            elif s == "1":
                pyperclip.copy("javascript:(function(){if(!window.location.hash.startsWith(\"#party/index/\")){alert('Please go to a GBF Party screen');return}let obj={p:parseInt(window.Game.view.deck_model.attributes.deck.pc.job.master.id,10),pcjs:window.Game.view.deck_model.attributes.deck.pc.param.image,ps:[],c:[],cl:[],cs:[],cp:[],cwr:[],s:[],sl:[],ss:[],sp:[],w:[],wl:[],wsn:[],wll:[],wp:[],wax:[],waxi:[],watk:window.Game.view.deck_model.attributes.deck.pc.weapons_attack,whp:window.Game.view.deck_model.attributes.deck.pc.weapons_hp,satk:window.Game.view.deck_model.attributes.deck.pc.summons_attack,shp:window.Game.view.deck_model.attributes.deck.pc.summons_attack,est:[window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage_attribute, window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_normal_damage, window.Game.view.deck_model.attributes.deck.pc.damage_info.assumed_advantage_damage]};for(let i=0;i<4-window.Game.view.deck_model.attributes.deck.pc.set_action.length;i++){}Object.values(window.Game.view.deck_model.attributes.deck.pc.set_action).forEach(e=>{obj.ps.push(e.name?e.name.trim():null)});Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.weapons).forEach(e=>{obj.w.push(e.master?parseInt(e.master.id.slice(0,-2),10):null);obj.wl.push(e.param?parseInt(e.param.skill_level,10):null);obj.wsn.push(e.param?[e.skill1?e.skill1.image:null,e.skill2?e.skill2.image:null,e.skill3?e.skill3.image:null]:null);obj.wll.push(e.param?parseInt(e.param.level,10):null);obj.wp.push(e.param?parseInt(e.param.quality,10):null);obj.waxi.push(e.param?e.param.augment_skill_icon_image:null);obj.wax.push(e.param?e.param.augment_skill_info:null)});let copyListener = event => { document.removeEventListener(\"copy\", copyListener, true); event.preventDefault(); let clipboardData = event.clipboardData; clipboardData.clearData(); clipboardData.setData(\"text/plain\", JSON.stringify(obj)); }; document.addEventListener(\"copy\", copyListener, true); document.execCommand(\"copy\");}())")
                print("Bookmarklet copied!")
                print("To setup on chrome:")
                print("1) Make a new bookmark (of GBF for example)")
                print("2) Right-click and edit")
                print("3) Change the name if you want")
                print("4) Paste the code in the url field")
            else:
                return

if __name__ == "__main__":
    print("Granblue Fantasy Party Image Builder v1.2")
    PartyBuilder().run()