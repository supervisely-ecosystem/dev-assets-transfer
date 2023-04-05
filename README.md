<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/119248312/227563661-e47a3d56-e13f-441e-a46a-9bf818ac086b.jpg"/>

# Download images from Flickr

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/flickr-downloader)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/flickr-downloader)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/flickr-downloader.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/flickr-downloader.png)](https://supervise.ly)

</div>

## Overview
This app allows the download of thousands of images from Flickr straight to a Supervisely dataset. After specifying a search query and some additional parameters (such as a license type, number of images, etc.) with only one click you can download images from Flickr and add them to a Supervisely dataset including meta information from Flickr (such as title, description, etc.).<br>
For example, you enter a search query "dog" and set the number of images to 1000. You can check the available licenses and meta information to download along with the images. After it, you can specify the project and the dataset to add the images (otherwise a new project and dataset will be created automatically). And now you only need to click "Download" and wait for the app to finish the job. After that, you will have a Supervisely dataset with up to 1000 images of dogs and all the meta information from Flickr that you have selected. For more details, see the [How To Run](#How-To-Run) section.<br>
**Note:** Flickr API may not return some images, which you can find in the search results for the same search query on the website for unknown reasons. It's rare, but it may happen.<br><br>

## Preparation
To use this app, you need to obtain a Flickr API key. To do this, you need to register a Flickr account and then follow the instructions from the [Flickr API Keys](https://www.flickr.com/services/apps/create/apply/) page. You have two options to use your API key: you can use team files to store a .env file with the API key or you can enter the API key directly in the app GUI. Using team files is recommended as it is more convenient and faster, but you can choose the option that is more suitable for you.<br>

### Using team files
1. Create a .env file with the following content:<br>
```FLICKR_API_KEY=your_api_key```<br>
2. Upload the .env file to the team files.<br>
3. Right-click on the .env file, select "Run app" and choose the "Flickr Download" app.<br>
The app will be launched with the API key from the .env file and you won't need to enter it manually.<br>

### Entering the API key manually
1. Launch the app.<br>
2. You will notice that all cards of the app are locked except the "Flickr API Key" card. Enter your API key in the field and press the "Check connection button".<br>
3. If the connection is successful, all cards will be unlocked and you can proceed with the app. Otherwise, you will see an error message and you will need to enter the API key again.<br>
Now you can use the app. Note that in this case, you will need to enter the API key every time you launch the app.<br>

## How To Run
Note: in this section, we consider that you have already obtained the API key, and use it to run the app. If you haven't done it yet, see the [Preparation](#Preparation) section.<br>
So, here are the steps to download images from Flickr:<br>

**Step 1:** Select the `Search type` (by tags or by text). Enter the search query in the `Search query` field. You can use complex queries, for example, "dog cat" or "blue car city". We recommend to enter the search query without articles (a, an, the) and prepositions (in, on, at, etc.) because they may significantly reduce the number of results. Also you should understand that the more complex the search query is, the fewer results you will get.<br>       
Note: it's two options available for the tag search method: either images in the result will have **ALL** tags from the query or **ANY** tag from the query.<br><br>
**Step 2:** Specify the license types of the images to download in the `License types` field. You can select one or more license types, but _at least one license type should be selected._ Note that number of results depends on the license types. So more license types you select, the more results you will get.<br><br>
**Step 3:** After completing the previous steps, we recommend checking the available number of results with the `Check number of images` button. It will show you the total number of images with the specific search query and license types. If the number is smaller than you expected, you can change the search query or license types. **Note:** due to the Flickr API search algorithms, you will receive a different number of results for the same search query and license types, this shouldn't confuse you.<br><br>![search_method](https://user-images.githubusercontent.com/119248312/228228738-d3c1b339-eedd-4bec-8ed6-b8e5bc0ac14c.png)<br><br>
**Step 4:** Now you need to enter the `Number of images` to download. **Note:** the number of images you will get may be smaller than the number you have entered, because Flickr returns duplicates in the search results, and additionally, some of the images may be unavailable for download. So, we recommend entering a number of images that is slightly larger than you need.<br><br>
**Step 5:** You can also specify the `Starting image number to search`. It is useful if you want to continue downloading images to the existing dataset where you have already downloaded some images for the same (or similar) search query. So, this option allows you to skip a specified amount of images in the search results. For example, if you have already downloaded 100 images for the search query "dog" and you want to continue downloading images, you can enter 100 in the "Starting image number" field and the app will skip the first 100 images in the search results.<br><br>
**Step 7:** Now you need to choose an `Upload method`. There are two options available: upload images as links or as files. The first option won't download the image files to the dataset, it will just use the source file links. So, if the source file will be unavailable, _it may cause data loss_. This option is faster than the second one, but it is not recommended to use this method for long-term storage, because the source files may be unavailable in the future. The second option will download the image files to the dataset, _it's safer but slower_. You can choose the option that is more suitable for you.<br><br>![search_settings](https://user-images.githubusercontent.com/119248312/228228900-e1d897a3-65dd-4af2-9caf-66832bae2847.png)<br><br>
**Step 8:** The next option is to change the `Upload settings`. It is disabled by default, which means that you don't need to change those settings in most cases. But if you want to change it, you can do it by unchecking the "Use default settings" checkbox and changing the values. The batch size value is the number of images to upload to the dataset in one batch. The second value is the number of workers to download images in parallel. **Note:** unoptimized settings may cause the app to work slower, so _we recommend using the default settings_ unless you have a specific reason to change them.<br><br>
**Step 9:** In the `Destination` section, you can specify the project and the dataset to add the images. If you don't specify the project or the dataset, a new project or dataset will be created automatically using the search query and the current date for generating names. You can also specify the name of the project or the dataset manually if you want to create them with custom names. **Note:** if you are adding images to the existing dataset, where you have already downloaded some images for the same (or similar) search query, you should use the `Starting image number` from `Step 5` to skip the already downloaded images or the app will ignore the duplicates and the result number of images will be smaller than you expected.<br><br>
**Step 10:** After completing all the previous steps, you can click the `Start Upload` button to start downloading images from Flickr and uploading them to the dataset. The app will show you the progress of the upload, and you can also cancel the upload at any time by pressing the "Cancel upload" button.
<br><br>![destination](https://user-images.githubusercontent.com/119248312/228228956-00faeee5-00de-4203-803a-d65cec812203.png)
<br><br>
After the upload is finished, you will see a message with the number of images that have been successfully uploaded to the dataset. The app will also show the number of duplicates that were skipped during the upload and the number of images that were unavailable for download. The app will also show the project and the dataset to which the images were uploaded. You can click on the links to open the project or the dataset.<br><br>

**Note:** the app will also add information about the search query and the license types to the custom data of the project. The entries will be grouped by the `Flickr downloader` app name and the search query. The entries will also contain the date and time of the upload, the number of images, starting image number, license types, and the upload method. This information will be useful if you want to continue downloading images for the same (or similar) search query in this project or dataset.
