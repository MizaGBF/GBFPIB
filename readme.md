# Granblue Fantasy Party Image Builder  
Script to generate an image from one of your in-game party in just a few clicks, to use for Videos or anything else.  
It support standard, extended and Tower of Babyl parties, extra grids and more.  
  
### Requirements  
* Tested on Python 3.13.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* [aiohttp](https://docs.aiohttp.org/en/stable/) for asset downloads.  
* `pip install -r requirements.txt` to install all the modules.  
  
### What's new?  
Version 12.0 is a revamp for maintainability purpose.  
The core should be more readable and maintainable.  
It now works purely in command lines.  
Unused features have been removed.  
  
Older versions can be found [here](https://github.com/MizaGBF/GBFPIB/releases).  
  
### Setup  
1. Install the requirements with the command above.  
2. Make a new bookmark in your browser.  
3. Open `bookmarklet.txt`, copy the content and past it into the bookmark field.  
  
You are done.  
  
### How-to  
1. Go on the party screen you want to export.  
2. (Optional but recommended) Click the `i` near the Estimate Damage. The game will load your support summon and HP setting in memory.
3. Click the bookmarklet you made during the setup.  
4. Run `python gbfpib.py` to generate a party from the data in your clipboard.  
5. If everything went well, party images should have been generated in the folder.  
  
### Usage  
```console
usage: gbfpib.py [-h] [-q {1080p,720p,4k}] [-nd] [-nps] [-npe] [-npa] [-ep [URL]] [-hp] [-sk]
                 [-tm [GBFTMR]] [-w]

Granblue Fantasy Party Image Builder v12.5 https://github.com/MizaGBF/GBFPIB

options:
  -h, --help            show this help message and exit

settings:
  commands to alter the script behavior.

  -q, --quality {1080p,720p,4k}
                        set the image size. Default is 4k
  -nd, --nodiskcache    disable the use of the disk cache.
  -nps, --nopartyskin   disable the generation of skin.png.
  -npe, --nopartyemp    disable the generation of emp.png.
  -npa, --nopartyartifact
                        disable the generation of artifact.png.
  -ep, --endpoint [URL]
                        set the GBF CDN endpoint.
  -hp, --showhp         draw the HP slider on skin.png.
  -tm, --gbftmr [GBFTMR]
                        set the GBFMTR path.
  -w, --wait            add a 10 seconds wait after the generation.
```
  
### Cache  
Images from the GBF asset servers are saved for later uses in the `cache` folder.  
You can also delete the folder if it gets too big.  
  
### EMP and Artifact  
No additional setup is required, it uses the same bookmarklet.  
1. Go to character EMP (for EMPs) or character detail (for Artifacts) page.  
2. Click the bookmarklet. If nothing happens, everything went well.  
3. Simply run `python gbfpib.py` and the data in your clipboard will be saved.  
  
This Character's EMP will be saved in the `emp` folder, as a `.json` file.  
In the same way, this Character's Artifact will be saved in the `artifact` folder, as a `.json` file.  
To update it, simply repeat the process.  
  
Keep in mind:
If game language differ at the time you saved the EMP/Artifact and when generating a Party image, it will display in the original language.  
  
### 
  
### Current HP setting  
If you used the `-hp/--showhp` argument and your Estimated Damage calculator was opened when using the bookmarklet, your HP percentage will be displayed on `skin.png`, instead of the off-element estimated damage.  
If the calculator wasn't opened, it will assume your current HP is set to 100%.  
  
### Support Summon  
By default, the game doesn't provide you the ID of the support summon set in your Estimated Damage calculator.  
There are a few ways to go around this issue:  
1. Open the Estimated Damage calculator before clicking the bookmarklet, the ID will be then loaded properly. You need to open it again if you change the party without reloading the page or the last loaded one will stay.  
2. Alternatively, the bookmarklet will fetch the name of the support summon and search its ID on the [gbf.wiki](https://gbf.wiki/). However, be warned this method isn't perfect, especially if you are playing in japanese or if you switch between parties.  
3. If the above two methods don't work, the name of the support summon will simply be written instead.  
  
### Bookmarklet  
Simply copy the content of the `bookmarklet.txt` file.  
If you wish to look at the non-minified code, the whole thing is available in `assets/bookmarklet.js`.  
  
### GBFTMR  
[GBFTMR](https://github.com/MizaGBF/GBFTMR) can be imported to also generate a thumbnail.  
Simply add the folder path with the argument. Example: `python gbfpib.py -tm ../GBFTMR`.  
The path can be relative or absolute and supports symlinks.
It's currently compatible with version 2.0 and higher (Ideally, always use the latest version to have the latest bugfixes).  
  
After generation, a prompt will ask you if you wish to generate a thumbnail.
  
### Updating  
Simply redownload the project.  
Make sure to keep your `emp` and `artifact` folders.  
If needed, update the requirements and the bookmarklet.  
  
### Inner Workings  
Some insights on how the image processing works:
1. Upon starting, it reads your clipboard and check if there is any valid data exported with the bookmark.  
2. For memory usage and speed reasons, `skin.png` is also composed of some simple layers, which are added on top of a copy of `party.png`. This way, we don't "redraw" `party.png` twice. Do note, however, the `skin.png` processing takes place even when the setting is disabled.  
  
### Known Issues  
The app will crash when using some alternate portrait from some skins, such as Cidala's. A workaround is applied in the function `get_character_look()`.  
I'll add more if I find more but you can add it yourself here or report them to me.  
  
### Others  
Like the licence specifies, you are free to use this software as you want, free of charge.  
You aren't forced to do anything else.
If you wish to thank/support me:  
1. If you want to credit me, you can link this page or name me (Mizako or Miza).  
2. If you want to report a bug, open an issue or contact me on [X](https://x.com/mizak0), as long as I continue to develop and improve it.  
  
I DON'T take feature requests. This tool is developped for my own use first and foremost.  
  
### Example  
<img src="./assets/github_demo.png">  