<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/115161827/234905634-c8b14987-c6d3-49b7-8e16-e91f9077bf69.png" />
  
# Transfer Images betweeen Instances

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/pips)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/dev-assets-transfer)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/dev-assets-transfer)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/dev-assets-transfer)](https://supervise.ly)

</div>

# Overview

This app transfers images between instances of Supervisely, while also keeping the original path structure: team -> workspace - > projects -> datasets. 

The app also has functionality of filtering the images you want to transfer by annotation type and/or tag name, and normalizing the metadata, which usually comes in handy when you download the images from Flickr or Pexels, but could also be applied to other scenarios.
You could configure the original and target teams, compare them, and then transfer the images between the instances.

This app is supposed to be one of the stages of working with datasets after uploading it through Flickr or Pexels downloaders.


# Preparation
To use this app, you need to obtain a Supervisely API key from the account you want to transfer data to. To do this, you need to log into your account and head to your account settings page. Then you'll need to go to "API Token" tab, and copy it from there. Remember, do not share your API Token to anyone. 

You have two options to use your API key: you can use team files to store a `.env` file with the API key or you can enter the API key directly in the app GUI. Using team files is recommended as it is more convenient and faster, but you can choose the option that is more suitable for you.<br>

## Using team files
1. Create a .env file with the following content:<br>
```TARGET_SERVER_ADDRESS="URL-TO-TARGET-INSTANCE"``` <br>
```TARGET_API_TOKEN="........"```
2. Upload the .env file to the team files.<br>
3. Right-click on the .env file, select "Run app" and choose the "Transfer Images between Instances" app.<br>
The app will be launched with the API key from the .env file and you won't need to enter it manually.<br>

## Entering the API key manually
1. Launch the app.<br>
2. You will notice that all cards of the app are locked except the "Instance" card. Enter your API key in the field, select the instance you want to transfer to and press the "Check connection button".<br>
3. If the connection is successful, all cards will be unlocked and you can proceed with the app. Otherwise, you will see an error message and you will need to enter the API key again.<br>
Now you can use the app. Note that in this case, you will need to enter the API key every time you launch the app.<br>

# How to Run

0. Run the application

1. If you haven't launched the app from the `.env` file, enter the API Token manually and select the Instance you need (See <a href="#Preparation">Preparation</a> section)
<img src="https://user-images.githubusercontent.com/115161827/234904969-74a93aad-4dac-4815-a57e-aae55081b7ab.png" />

2. If you want to transfer images to Assets instance, then leave the `Use default settings` box checked. Otherwise, uncheck it and configure the app to your needs
<img src="https://user-images.githubusercontent.com/115161827/234905067-b9a9f555-e2da-4b79-9190-bc55190630be.png" />

3. Select the team you want to upload images from, enter the name of the target team and click `Compare data`
<img src="https://user-images.githubusercontent.com/115161827/234905257-d42e13b3-7a7e-4438-9fa1-016f26b5fd18.png" />
Keep in mind that the name of a destination team should be unique, otherwise an application would not work

4. Finally, click `Update data`
<img src="https://user-images.githubusercontent.com/115161827/234905363-54478677-8f84-423b-a4c0-e50498abbb23.png" />
