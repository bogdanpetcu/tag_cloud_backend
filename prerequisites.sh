#!/bin/bash

sudo pip install tweepy
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
cd ..
sudo redis-server &
sudo git clone https://github.com/andymccurdy/redis-py.git
cd redis-py
sudo python setup.py install
