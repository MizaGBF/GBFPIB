# Granblue Fantasy Party Image Builder  
* Tool to generate an image from one of your in-game party in just a few clicks, to use for Videos or anything else.  
### Requirements  
* Tested on Python 3.13.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* [aiohttp](https://docs.aiohttp.org/en/stable/) for asset downloads.  
* `pip install -r requirements.txt` to install all the modules.  
  
### What's new?  
Version 11.0 is a cleaned up version of 10.0, tested on Python 3.13.  
It might still work on older Python versions but consider those unsupported.  
  
Older versions can be found [here](https://github.com/MizaGBF/GBFPIB/releases).  
  
### Setup  
1. Install the requirements with the command above.  
2. Double click on `gbfpib.pyw`.  
3. Click on the `Bookmark` button. A javascript code will be copied to your clipboard.  
4. On the Chrome (or equivalent) browser you are using, make a new bookmark.  
5. Right click that bookmark, select `edit`.  
6. Paste the javascript code into the url field.  
7. Change the bookmark name if you want to.  
  
You are done.  
  
> [!NOTE]  
> If requirements haven't been installed properly, the script will automatically attempt to install them.  
> On Windows, it might ask for administrator rights, if required.  
  
### How-to  
1. Go on the party screen you want to export.  
2. Click the bookmarklet. If nothing happens, everything went well.  
3. Open `gbfpib.pyw` again.  
4. This time, click on the `Build Images` button.  
5. If everything went well, the image should appear beside `gbfpib.pyw` under the name `party.png`. Note: if you enabled the corresponding settings, it will also generate `skin.png` and/or `emp.png`.  
6. If it didn't, something went wrong, probably at the step 2.  
  
### Settings  
1. `Quality`: Let you control the output size (maximum and default recommended setting is 4K, minimum is 720p).  
2. `Caching`: If enabled, downloaded images will be saved on disk (in the cache folder) for later uses. Delete the folder to reset its content.  
3. `Do Skins`: If enabled, it will also generate `skin.png`.  
4. `Do EMP`: If enabled, it will also generate `emp.png`.  
5. `Auto Update`: If enabled, will check if an update is available on app startup.  
  
### Advanced Settings  
1. `Cache Assets`: If enabled, assets will be cached in the `cache` folder to increase speed of future processings.  
2. `HP Bar on skin.png`: If enabled, your Estimate Damage HP setting will be displayed on `skin.png`. `Do Skins` setting must be enabled for it to work.  
3. `Guess Opus/Ultima Key`: If enabled, it will attempt to guess your Dark Opus and Ultima third skill to display the key image instead of the generic skill icon. Not 100% accurate.  
  
### Command Line  
For advanced users:  
```
usage: gbfpib2.pyw [-h] [-c] [-f] [-w]

Granblue Fantasy Party Image Builder v11.0 https://github.com/MizaGBF/GBFPIB

options:
  -h, --help  show this help message and exit

settings:
  commands to alter the update behavior.

  -c, --cli   invoke the CLI.
  -f, --fast  directly call the generate function. The party or EMP data must be in your clipboard beforehand.
  -w, --wait  wait 10 seconds after the generation using -f/--fast
```  
  
### Cache  
Images from the GBF asset servers can be saved for later uses.  
You only need to enable the option to make it work.  
If some of those images are updated in game, all you need is to delete the cache folder so they are redownloaded later.  
You can also delete the folder if it gets too big.  
  
### EMP  
No additional setup is required, it uses the same bookmark.  
1. Go to character EMP page.  
2. Click the bookmarklet. If nothing happens, everything went well.  
3. In `gbfpib.pyw`, click on the `Add EMP` button.  
  
This Character's EMP will be saved in the `emp` folder, as a `.json` file.  
To update it, simply repeat the process.  
  
Keep in mind:
1. The `Do EMP` setting must be enabled or `emp.png` won't be generated when clicking `Build Images`.  
2. If game language differ at the time you saved the EMP and when generating a Party image, EMPs will display in the original language.  
  
### Current HP setting  
(Only if the `HP Bar on skin.png` setting is enabled)  
If you click the Bookmarklet with the Estimated Damage calculator open, it will grab the current HP percentage and display it on `skin.png`, instead of the off-element estimated damage.  
If you don't open the calculator, it will assume your current HP is set to 100%.  
  
### Support Summon  
By default, the game doesn't provide you the ID of the support summon set in your damage calculator.  
There are a few ways to go around this issue:  
1. If you open the damage calculator BEFORE clicking the bookmarklet, the ID will be fetched properly. You need to open it again if you change the party without reloading the page or the last loaded one will stay.  
2. Alternatively, the bookmarklet will fetch the name of the support summon and search its ID on [gbf.wiki](https://gbf.wiki/). However, be warned this method isn't perfect, especially if you are playing in japanese or if you switch between parties.  
3. If the above two methods don't work, the name of the support summon will simply be written instead.  
  
### Bookmarklet  
You can retrieve the Bookmarklet to export your party/EMP data from the built-in interface or CLI.  
Alternatively, you can copy it from the `bookmarklet.txt` file.  
  
> [!IMPORTANT]  
> Do **NOT** delete `bookmarklet.txt`, as the script retrieves the Bookmarklet from here.  
  
### GBFTMR  
[GBFTMR](https://github.com/MizaGBF/GBFTM) can be imported to also generate a thumbnail.  
Simply click `Set Path` and select the folder where GBFTMR is located.  
GBFTMR must have been set beforehand or it might not work properly.  
It's currently compatible with version 2.0 and higher (Ideally, always use the latest version to have the latest bugfixes).  
  
### Updating  
The script has a built-in auto updater.  
I recommend using it, for ease of use.  
If you can't or don't want to use it, simply download the latest version and redo the Setup steps.  
  
### Using it in your videos  
Like the licence specifies, you are free to use this software as you want, free of charge.  
Do note:  
1. If you want to credit me, you can link this page or name me (Mizako or Miza).  
2. If you want to report a bug, open an issue or contact me on [X](https://x.com/mizak0), as long as I continue to develop and improve it.  
3. I DON'T take feature requests. This tool is developped for my own use first and foremost. This is why I don't advertise it.  
  
### Inner Workings  
Some insights on how the image processing works:
1. Upon starting, it reads your clipboard and check if there is any valid data exported with the bookmark.  
2. Because Python multithreading is terribly slow, it relies on multiprocessing instead: Up to 6 new proccesses are created. One purely for the party, one for the summons, one for the weapon grid, one for the weapon modifiers and one for EMPs. Each process returns the images, which are then assembled in another process as simple layers, by putting them one on top of each other.  
3. For memory usage and speed reasons, `skin.png` is also composed of some simple layers, which are added on top of a copy of `party.png`. This way, we don't "redraw" `party.png` twice. Do note, however, the `skin.png` processing takes place even when the setting is disabled.  
  
### Known Issues  
The app will crash when using some alternate portrait from some skins, such as Cidala's. A workaround is applied in the function `get_character_look()`.  
I'll add more if I find more but you can add it yourself here or report them to me.  
  