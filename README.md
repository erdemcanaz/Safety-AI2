# Safety-AI2

sudo docker run --runtime nvidia --privileged -v safety_AI_volume:/home/safety_AI_volume -v /etc/localtime:/etc/localtime:ro -it --rm --network=host -e DISPLAY -e QT_X11_NO_MITSHM=1 dustynv/l4t-pytorch:safety_AI



docker volume local_ssd_data_folder

-v local_ssd_data_folder:/home/local_ssd_data_folder

external ssd
v- /media/safety/T7 Shield:/home/external_ssd_data_folder
