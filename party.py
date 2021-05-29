from urllib import request, parse
from urllib.parse import unquote
import json
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import pyperclip

class PartyBuilder():
    def __init__(self):
        self.font = ImageFont.truetype("assets/basic.ttf", 16)
        self.small_font = ImageFont.truetype("assets/basic.ttf", 14)

    def pasteImage(self, img, file, offset, resize=None):
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    def dlAndPasteImage(self, img, url, offset, resize=None):
        req = request.Request(url)
        url_handle = request.urlopen(req)
        with BytesIO(url_handle.read()) as file_jpgdata:
            self.pasteImage(img, file_jpgdata, offset, resize)

    def get_uncap_id(self, cs):
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def make_party(self, export, img, d, offset):
        # mc
        self.dlAndPasteImage(img,  "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/quest/{}.jpg".format(export['pcjs']), (offset[0], offset[1]), (78, 142))
        self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/job/{}.png".format(export['p']), (offset[0], offset[1]))
        for i in range(0, 5): # npcs
            # portrait
            if export['c'][i] is None:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/deckcombination/base_empty_npc.jpg", (offset[0]+78*(i+1), offset[1]), (78, 142))
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/quest/{}000_{}.jpg".format(export['c'][i], self.get_uncap_id(export['cs'][i])), (offset[0]+78*(i+1), offset[1]), (78, 142))
            # rings
            if export['cwr'][i] == True:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (offset[0]+78*(i+1), offset[1]), (30, 30))
            # plus
            if export['cp'][i] > 0:
                d.text((offset[0]+30+78*(i+1), offset[1]+118), "+{}".format(export['cp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
            # level
            d.rectangle([(offset[0]+78*(i+1), offset[1]+142), (offset[0]+78*(i+2), offset[1]+162)], fill=(0, 0, 0, 200), width=1)
            d.text((offset[0]+6+78*(i+1), offset[1]+145), "Lv{}".format(export['cl'][i]), fill=(255, 255, 255), font=self.font)

    def make_summons(self, export, img, d, offset):
        for i in range(0, 5):
            # portraits
            if export['s'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/2999999999.jpg", (offset[0]+67*i, offset[1]), (67, 142))
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/{}.jpg".format(export['ss'][i]), (offset[0]+67*i, offset[1]), (67, 142))
            # plus
            if export['sp'][i] > 0:
                d.text((offset[0]+35+67*i, offset[1]+118), "+{}".format(export['sp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
            # level
            d.rectangle([(offset[0]+67*i, offset[1]+142), (offset[0]+67*(i+1), offset[1]+162)], fill=(0, 0, 0, 200), width=1)
            d.text((offset[0]+6+67*i, offset[1]+145), "Lv{}".format(export['sl'][i]), fill=(255, 255, 255), font=self.font)
        # stats
        d.rectangle([(offset[0], offset[1]+162), (offset[0]+67*3, offset[1]+182)], fill=(0, 0, 0, 200), width=1)
        self.pasteImage(img, "assets/atk.png", (offset[0], offset[1]+167), (30, 13))
        self.pasteImage(img, "assets/hp.png", (offset[0]+100, offset[1]+167), (22, 13))
        d.text((offset[0]+40, offset[1]+167), "{}".format(export['satk']), fill=(255, 255, 255), font=self.small_font)
        d.text((offset[0]+100+30, offset[1]+167), "{}".format(export['shp']), fill=(255, 255, 255), font=self.small_font)

    def make_grid(self, export, img, d, base_offset):
        # sandbox tag
        if len(export['w']) > 10:
            self.pasteImage(img, "assets/sandbox.png", (base_offset[0]+88+70*3, base_offset[1]-29), (70, 29))
        
        # weapons
        for i in range(0, len(export['w'])):
            wt = "ls" if i == 0 else "m"
            if i == 0: # mainhand
                offset = (base_offset[0], base_offset[1])
                size = (78, 142)
            elif i >= 10: # sandbox
                x = 3
                y = (i-1) % 3
                offset = (base_offset[0]+88+70*x, base_offset[1]+80*y)
                size = (70, 40)
            else: # others
                x = (i-1) % 3
                y = (i-1) // 3
                offset = (base_offset[0]+88+70*x, base_offset[1]+80*y)
                size = (70, 40)
            if export['w'][i] is None:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt), offset, size)
                continue
            else:
                self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/{}/{}00.jpg".format(wt, export['w'][i]), offset, size)
            # skill box
            if i == 0:
                d.rectangle([(offset[0], offset[1]+size[1]), (offset[0]+size[0], offset[1]+size[1]+40)], fill=(0, 0, 0, 200), width=1)
            else:
                d.rectangle([(offset[0], offset[1]+40), (offset[0]+size[0], offset[1]+80)], fill=(0, 0, 0, 200), width=1)
            # plus
            if export['wp'][i] > 0:
                if i == 0:
                    d.text((offset[0]+size[0]-30, offset[1]+size[1]-20), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
                else:
                    d.text((offset[0]+size[0]-30, offset[1]+size[1]-20), "+{}".format(export['wp'][i]), fill=(255, 255, 95), font=self.font, stroke_width=1, stroke_fill=(0, 0, 0))
            # skill icon
            for j in range(3):
                if export['wsn'][i][j] is not None:
                    if i == 0:
                        self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (offset[0]+1+23*j, offset[1]+size[1]+1), (20, 20))
                    else:
                        self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]), (offset[0]+1+23*j, offset[1]+41), (20, 20))
            # skill level
            if export['wl'][i] is not None:
                if i == 0:
                    d.text((offset[0]+1, offset[1]+size[1]+24), "skill Lv{}".format(export['wl'][i]), fill=(255, 255, 255), font=self.font)
                else:
                    d.text((offset[0]+1, offset[1]+64), "skill Lv{}".format(export['wl'][i]), fill=(255, 255, 255), font=self.font)
        # stats
        offset = (base_offset[0], base_offset[1]+190)
        d.rectangle([(offset[0], offset[1]), (offset[0]+78, offset[1]+50)], fill=(0, 0, 0, 200), width=1)
        self.pasteImage(img, "assets/atk.png", offset, (30, 13))
        self.pasteImage(img, "assets/hp.png", (offset[0], offset[1]+25), (22, 13))
        d.text((offset[0]+35, offset[1]+12), "{}".format(export['watk']), fill=(255, 255, 255), font=self.small_font)
        d.text((offset[0]+35, offset[1]+12+25), "{}".format(export['whp']), fill=(255, 255, 255), font=self.small_font)

    def make(self):
        print("Instructions:")
        print("1) Go to the party screen you want to export")
        print("2) Click your bookmarklet")
        print("3) Come back here and press Return to continue")
        try:
            input()
            clipboard = pyperclip.paste()
            export = json.loads(clipboard)
            
            
            img = Image.new('RGB', (547, 720), "black")
            im_a = Image.new("L", img.size, "black")
            img.putalpha(im_a)
            im_a.close()
            d = ImageDraw.Draw(img, 'RGBA')
            # party
            self.pasteImage(img, "assets/characters.png", (10, 10), (92, 25))
            self.make_party(export, img, d, (40, 45))

            # summons
            self.pasteImage(img, "assets/summons.png", (10, 210), (92, 25))
            self.make_summons(export, img, d, (106, 245))

            # grid
            self.pasteImage(img, "assets/weapons.png", (10, 430), (92, 25))
            self.make_grid(export, img, d, (89, 465))


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
                pyperclip.copy("javascript:(function(){if(!window.location.hash.startsWith(\"#party/index/\")){alert('Please go to a GBF Party screen');return}let obj={p:parseInt(window.Game.view.deck_model.attributes.deck.pc.job.master.id,10),pcjs:window.Game.view.deck_model.attributes.deck.pc.param.image,ps:[],c:[],cl:[],cs:[],cp:[],cwr:[],s:[],sl:[],ss:[],sp:[],w:[],wl:[],wsn:[],wll:[],wp:[],watk:window.Game.view.deck_model.attributes.deck.pc.weapons_attack,whp:window.Game.view.deck_model.attributes.deck.pc.weapons_hp,satk:window.Game.view.deck_model.attributes.deck.pc.summons_attack,shp:window.Game.view.deck_model.attributes.deck.pc.summons_attack};for(let i=0;i<4-window.Game.view.deck_model.attributes.deck.pc.set_action.length;i++){obj.ps.push(null)}Object.values(window.Game.view.deck_model.attributes.deck.pc.set_action).forEach(e=>{obj.ps.push(e.name?e.name.trim():null)});Object.values(window.Game.view.deck_model.attributes.deck.npc).forEach(e=>{obj.c.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.cl.push(e.param?parseInt(e.param.level,10):null);obj.cs.push(e.param?parseInt(e.param.evolution,10):null);obj.cp.push(e.param?parseInt(e.param.quality,10):null);obj.cwr.push(e.param?e.param.has_npcaugment_constant:null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.summons).forEach(e=>{obj.s.push(e.master?parseInt(e.master.id.slice(0,-3),10):null);obj.sl.push(e.param?parseInt(e.param.level,10):null);obj.ss.push(e.param?e.param.image_id:null);obj.sp.push(e.param?parseInt(e.param.quality,10):null)});Object.values(window.Game.view.deck_model.attributes.deck.pc.weapons).forEach(e=>{obj.w.push(e.master?parseInt(e.master.id.slice(0,-2),10):null);obj.wl.push(e.param?parseInt(e.param.skill_level,10):null);obj.wsn.push(e.param?[e.skill1?e.skill1.image:null,e.skill2?e.skill2.image:null,e.skill3?e.skill3.image:null]:null);obj.wll.push(e.param?parseInt(e.param.level,10):null);obj.wp.push(e.param?parseInt(e.param.quality,10):null)});let copyListener = event => { document.removeEventListener(\"copy\", copyListener, true); event.preventDefault(); let clipboardData = event.clipboardData; clipboardData.clearData(); clipboardData.setData(\"text/plain\", JSON.stringify(obj)); }; document.addEventListener(\"copy\", copyListener, true); document.execCommand(\"copy\");}())")
                print("Bookmarklet copied!")
                print("To setup on chrome:")
                print("1) Make a new bookmark (of GBF for example)")
                print("2) Right-click and edit")
                print("3) Change the name if you want")
                print("4) Paste the code in the url field")
            else:
                return

if __name__ == "__main__":
    print("Granblue Fantasy Party Image Builder v1.0")
    PartyBuilder().run()