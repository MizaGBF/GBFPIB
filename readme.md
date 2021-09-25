# Granblue Fantasy Party Image Builder  
* Tool to generate an image from one of your in-game party, to use for Videos or anything else.  
### Requirements  
* Tested on Python 3.9.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* `pip install -r requirements.txt` to install all the modules.  
### Setup  
1. Install the requirements with the command above.  
2. Double click on `party.pyw`.  
3. Click on the `Get Bookmarklet` button. A javascript code will be copied to your clipboard.  
4. On the Chrome (or equivalent) browser you are using, make a new bookmark.  
5. Right click that bookmark, select `edit`.  
6. Paste the javascript code into the url field.  
7. Change the bookmark name if you want to.  
  
You are done.  
### How-to  
1. Go on the party screen you want to export.  
2. Click the bookmarklet. If nothing happens, everything went well.  
3. Open `party.pyw` again.  
4. This time, click on the `Build Image` button.  
5. If everything went well, the image should appear beside `party.pyw` under the name `party.png`.  
6. If it didn't, something went wrong, probably at the step 2.  
### Settings  
1. `Quality`: let you control the output size (default is 720p, up to 8K).  
2. `Disk Caching`: if enabled, downloaded images will be saved on disk (in the cache folder) for later uses. Delete the folder to reset its content.  
### Command Line  
1. `-fast`: Automatically start the image building process. Be sure to have the party data ready in your clipboard.  
2. `-nowait`: Skip the 10 seconds waiting time at the end when using `-fast`.  
### Result  
![Example](https://cdn.discordapp.com/attachments/614716155646705676/891340472671404052/party.png)