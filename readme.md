# Granblue Fantasy Party Image Builder  
* Tool to generate an image from one of your in-game party in just a few clicks, to use for Videos or anything else.  
### Requirements  
* Tested on Python 3.10.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* [httpx](https://www.python-httpx.org/) for faster asset downloads.  
* `pip install -r requirements.txt` to install all the modules.  
### Setup  
1. Install the requirements with the command above.  
2. Double click on `gbfpib.pyw`.  
3. Click on the `Bookmark` button. A javascript code will be copied to your clipboard.  
4. On the Chrome (or equivalent) browser you are using, make a new bookmark.  
5. Right click that bookmark, select `edit`.  
6. Paste the javascript code into the url field.  
7. Change the bookmark name if you want to.  
  
You are done.  
Do note, if requirements haven't been installed properly, the script will automatically try to install them. It might ask for administrator rights, if required.  
### How-to  
1. Go on the party screen you want to export.  
2. Click the bookmarklet. If nothing happens, everything went well.  
3. Open `gbfpib.pyw` again.  
4. This time, click on the `Build Images` button.  
5. If everything went well, the image should appear beside `gbfpib.pyw` under the name `party.png`. Note: if you enabled the corresponding settings, it will also generate `skin.png` and/or `emp.png`.  
6. If it didn't, something went wrong, probably at the step 2.  
  
The process take around 1 GB of memory and can take up to one minute (if your computer is slow and the script needs to download assets).  
### Settings  
1. `Quality`: let you control the output size (default is 8K, minimum is 720p).  
2. `Caching`: if enabled, downloaded images will be saved on disk (in the cache folder) for later uses. Delete the folder to reset its content.  
3. `Do Skins`: if enabled, it will also generate `skin.png`.  
4. `Do EMP`: if enabled, it will also generate `emp.png`.  
5. `Use HTTPS`: if enabled, it will use HTTPS when downloading assets. Do note you can change the used asset server with the button on the left (in case they change the address again in the future).  
### Command Line  
For advanced users:  
1. `-fast`: Automatically start the image building process. Be sure to have the party data ready in your clipboard. If EMP datas are found instead, it will be saved in the `emp` folder.  
2. `-nowait`: Skip the 10 seconds waiting time at the end when using `-fast`.  
3. `-cmd`: Let you access the command line menu. Can't be used with `-fast`.  
4. `-debug`: For debugging purpose.  
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
2. Your game language must be the same at the time you saved the EMP and when generating a Party image. EMP saved as japanese won't work for an english party image and vice versa.  
### Estimate Damage settings  
If you click the bookmarklet with the Estimated Damage calculator open, it will grab the current HP percentage and display it on `skin.png`, instead of the off-element estimated damage.  
### Critical Estimate Damage  
If your weapon grid has a critical modifier inferior to 100%, it will display the critical estimated damage on `skin.png`, instead of the on-element estimated damage.  
Do note the calcul isn't perfect: It won't account for cap up or craft skills (or other critical supplementals).  
### Support Summon  
By default, the game doesn't provide you the ID of the support summon set in your damage calculator.  
There are a few ways to go around this issue:  
1. If you open the damage calculator BEFORE clicking the bookmarklet, the ID will be fetched properly. You need to open it again if you change the party without reloading the page or the last loaded one will stay.  
2. Alternatively, the bookmarklet will fetch the name of the support summon and search its ID on [gbf.wiki](https://gbf.wiki/). However, be warned this method isn't perfect, especially if you are playing in japanese.  
3. If the above two methods don't work, the name of the support summon will simply be written instead.  
### GBFTM  
My other project [GBFTM](https://github.com/MizaGBF/GBFTM) can be imported to also generate a thumbnail.  
Simply click `Set Path` and select the folder where GBFTM is located.  
GBFTM must has been set beforehand (Twitter credentials included) or it might not work properly.  
It's also currently compatible only with version 1.16 and higher (Ideally, always use the latest version to have the latest bugfixes).  
### Updating  
The script has a built-in auto updater.  
I recommend using it, for ease of use.  
If you can't or don't want to use it, simply download the latest version and redo the Setup steps.  
### Using it in your videos  
Like the licence specifies, you are free to use this software as you want, free of charge.  
Do note:  
1. If you want to credit me, you can link this page or name me (Mizako or Miza).  
2. If you want to report a bug, open an issue or contact me on [Twitter](https://twitter.com/mizak0), as long as I continue to develop and improve it.  
3. I DON'T take feature requests. This tool is developped for my own use first and foremost. This is why I don't advertise it.  
### Inner Workings  
Some insights on how the image processing works:
1. Upon starting, it reads your clipboard and check if there is any valid data exported with the bookmark.  
2. Because Python multithreading is terribly slow, it relies on multiprocessing instead: Up to 6 new proccesses are created. One purely for the party, one for the summons, one for the weapon grid, one for the weapon modifiers and one for EMPs. Each process returns the images, which are then assembled in another process as simple layers, by putting them one on top of each other.  
3. For memory usage and speed reasons, `skin.png` is also composed of some simple layers, which are added on top of a copy of `party.png`. This way, we don't "redraw" `party.png` twice. Do note, however, the `skin.png` processing takes place even when the setting is disabled.  
### Result  
Here's what the resulting images look like:  
(Screenshots taken on version 8.3)  
![Party and Skin Example](https://cdn.discordapp.com/attachments/614716155646705676/1010681871425880074/result.gif)  
![EMP Example](https://cdn.discordapp.com/attachments/614716155646705676/1010681871732068444/emp.png)  