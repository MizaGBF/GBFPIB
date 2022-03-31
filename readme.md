# Granblue Fantasy Party Image Builder  
* Tool to generate an image from one of your in-game party in just a few clicks, to use for Videos or anything else.  
### Requirements  
* Tested on Python 3.10.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* `pip install -r requirements.txt` to install all the modules.  
### Setup  
1. Install the requirements with the command above.  
2. Double click on `gbfpib.pyw`.  
3. Click on the `Party Bookmark` button. A javascript code will be copied to your clipboard.  
4. On the Chrome (or equivalent) browser you are using, make a new bookmark.  
5. Right click that bookmark, select `edit`.  
6. Paste the javascript code into the url field.  
7. Change the bookmark name if you want to.  
  
You are done.  
### How-to  
1. Go on the party screen you want to export.  
2. Click the bookmarklet. If nothing happens, everything went well.  
3. Open `gbfpib.pyw` again.  
4. This time, click on the `Build Images` button.  
5. If everything went well, the image should appear beside `gbfpib.pyw` under the name `party.png`. Note: if the `Skin` setting is enabled, it will also generate a second image called `skin.png`, where your selected skins will appear instead.  
6. If it didn't, something went wrong, probably at the step 2.  
### Settings  
1. `Quality`: let you control the output size (default is 8K, minimum is 720p).  
2. `Disk Caching`: if enabled, downloaded images will be saved on disk (in the cache folder) for later uses. Delete the folder to reset its content.  
3. `Do Skins`: if enabled, it will also generate `skin.png`.  
4. `Do EMP`: if enabled, it will also generate `emp.png`.  
### Command Line  
1. `-fast`: Automatically start the image building process. Be sure to have the party data ready in your clipboard. If EMP data is found instead, it will be saved.  
2. `-nowait`: Skip the 10 seconds waiting time at the end when using `-fast`.  
2. `-cmd`: Let you access the old command line menu. Can't be used with `-fast`.  
### Cache  
Images from the GBF asset servers can be saved for later uses.  
You only need to enable the option to make it work.  
If some of those images are updated in game, all you need is to delete the cache folder so they are redownloaded later.  
You can also delete it if it gets too big.  
### EMP  
The setup for Characters Extended Mastery Perks is similar to the initial one:
1. Double click on `gbfpib.pyw`.  
2. Click on the `EMP Bookmark` button. A javascript code will be copied to your clipboard.  
3. On the Chrome (or equivalent) browser you are using, make a new bookmark.  
4. Right click that bookmark, select `edit`.  
5. Paste the javascript code into the url field.  
6. Change the bookmark name if you want to.  
  
Then, to set a Character, go to its EMP page, click the bookmark and then, in `gbfpib.pyw`, click `Add EMP`.  
The details will be saved in a .json file, in the `emp` folder.  
If you change this Character EMP setup, just repeat the process to update it.  
Also,make sure:
1. The `Do EMP` setting is enabled or `emp.png` won't be generated.  
2. Your game language setting is set to the one you usually use. EMP saved as japanese won't work for an english party image and vice versa.  
  
### Support Summon  
By default, the game doesn't provide you the ID of the support summon set in your damage calculator.  
There are a few ways to go around this issue:  
1. If you open the damage calculator BEFORE clicking the bookmarklet, the ID will be fetched properly. You need to open it again if you change the party without reloading the page or the last loaded one will stay.  
2. Alternatively, the bookmarklet will fetch the name of the support summon and search its ID on [gbf.wiki](https://gbf.wiki/). However, be warned this method isn't perfect, especially if you are playing in japanese.  
3. If the above two methods don't work, the name of the support summon will simply be written instead.  
### Updating  
When updating this script with a new version, be sure to update your bookmarklet, or issues might occur.  
You might also want to rerun the `pip install -r requirements.txt` command if the required modules got updated.  
### Result  
Here's what a resulting image looks like:  
(Screenshot taken on version 5.0)  
![Example](https://cdn.discordapp.com/attachments/614716155646705676/950385974322528346/party.png)  