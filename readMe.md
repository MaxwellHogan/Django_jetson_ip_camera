This project demonstrates a simple example of streaming both cameras to a Django webserver on a Jetson Nano - although I haven't tested it I am not aware of any reason that it will not work on a rpi with minimal effort.

To modify the camera feeds you can open up base/views.py and change the strings gstreamer_config0 (line 57) and gstreamer_config1 (line 63).
Alternatively you can make changes directly to the VideoCamera object.

I use a post-processing function - also defined in base/view.py - to convert the raw frame format and flip it (as my cameras were mounted upside down), you can make changes to the iamges prior to display in here. 

Example video showing the interface on iphone in safari: https://www.youtube.com/shorts/bUfKUCbns8c

I have set up SSH so I can work on the project remotely. If you want to start the webhost from the SSH session and keep it alive after you leave, use the following:

```
screen
python3 manage.py runserver 0.0.0.0:8000
```

Ctrl-A then Ctrl-D, This will detach your screen session but leave your processes running. 

You may now log out of the remote box.

If you want to go back later, log on and use the following to return to the session:
```
screen -r
```
If you want to see the screen outside your home - I suggest using the following service
https://tailscale.com/
