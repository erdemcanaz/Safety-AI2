# Safety-AI2

sudo docker run --privileged -v safety_AI_volume:/home/safety_AI_volume --runtime nvidia -it --rm --network=host -e DISPLAY -e QT_X11_NO_MITSHM=1 dustynv/l4t-pytorch:r35.4.1
