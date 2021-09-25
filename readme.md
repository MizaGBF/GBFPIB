# Granblue Fantasy Party Image Builder  
* Tool to generate an image from one of your in-game party, to use for Videos or anything else.  
### Requirements  
* Tested on Python 3.9.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* `pip install -r requirements.txt` to install all the modules.  
### Setup  
1. Install the requirements with the command above.  
2. Double click on `party.py`.  
3. Type `1` and valid to select the `Get Bookmarklet` option. A javascript code will be copied to your clipboard.  
4. On the Chrome (or equivalent) browser you are using, make a new bookmark.  
5. Right click that bookmark, select `edit`.  
6. Paste the javascript code into the url field.  
7. Change the bookmark name if you want to.  
  
You are done.  
### How-to  
1. Go on the party screen you want to export.  
2. Click the bookmarklet. If nothing happens, everything went well.  
3. Open `party.py` again.  
4. This time, type `0` and valid to select the `Generate Image` option.  
5. The script will repeat those instructions again. Press return again.  
6. If everything went well, the image should appear beside `party.py` under the name `party.png`.  
7. If it didn't, something went wrong, probably around the step 2.  
### Settings  
1. `Quality`: let you control the output size (default is 720p, up to 8K).  
2. `Disk Caching`: if enabled, downloaded images will be saved on disk (in the cache folder) for later uses. Delete the folder to reset its content.  
### Command Line  
1. `-fast`: Automatically start the image building process. Be sure to have the party data ready in your clipboard.  
2. `-nowait`: Skip the 10 seconds waiting time at the end when using `-fast`.  
### Result  
![Example](https://cdn.discordapp.com/attachments/614716155646705676/878646321110712320/party.png)