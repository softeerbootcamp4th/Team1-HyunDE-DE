FROM amazon/aws-lambda-python:3.12

RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm jq unzip
    
COPY ./chrome-installer.sh ./chrome-installer.sh
RUN chmod +x ./chrome-installer.sh
RUN ./chrome-installer.sh
RUN rm ./chrome-installer.sh

RUN pip install selenium pyperclip pandas boto3 python-dotenv webdriver_manager

COPY main.py ./

COPY login_info.env ./

CMD [ "main.lambda_handler" ]

