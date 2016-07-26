# -*- coding: utf-8 -*-
import sys
import time
import telepot
import redis
import os
import json
import time
import logging
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide


r_server = redis.Redis(host=os.getenv("IP", "0.0.0.0"), port=6379)


def on_chat_message(msg):
    content_type, chat_type, chat_id, date, message_id = telepot.glance(msg, long=True)
    print msg

    # if take location, then store location for 60s
    r_key = "user_location_{}".format(chat_id)
    if content_type == 'location':
        wait_time = 60
        r_server.setex(r_key, json.dumps(msg['location']), wait_time)
        bot.sendMessage(chat_id, 'Stored location', reply_markup=ReplyKeyboardHide())
        
    # check if user location is stored in DB
    user_location_saved = r_server.get(r_key)
    location = None
    
    # load location if it exists
    if user_location_saved:
        location = json.loads(user_location_saved)
        print("Stored location: ", location)
    else:
        # send Button for getting location
        bot.sendMessage(chat_id, 'Give your location, please.',
                        reply_markup=ReplyKeyboardMarkup(keyboard=[[
                        KeyboardButton(text='Location',request_location=True
                        )]])
        )

    if content_type == 'text':
        r_key_user_msgs = 'user_msgs_{}'.format(chat_id)
        # if location is set, store message
        if location:
            r_server.rpush(r_key_user_msgs, json.dumps({
                'user_id': chat_id,
                'message': msg['text'],
                'location': location,
                'time': int(time.time())
            }))
            
        # display last 10 user messages
        if msg['text'] == '/show_msgs':
            msgs = r_server.lrange(r_key_user_msgs, 0, 10)
            bot.sendMessage(chat_id, str(msgs))
            
        # display last 20 links to photos
        if msg['text'] == '/photos':
            r_key_user_photos = 'user_photos_{}'.format(chat_id)
            number_photos = r_server.llen(r_key_user_photos)
            msgs = ["Number of photos: {}".format(number_photos)]
            for number in range(number_photos, 0, -1)[:20]:
                msgs.append("/photo{}".format(number))
            bot.sendMessage(chat_id, "\n".join(msgs))
            
        # display photo by number
        if msg['text'].startswith('/photo'):
            number_photo = msg['text'].replace('/photo', '')
            if number_photo.isdigit():
                number = int(number_photo)-1
                r_key_user_photos = 'user_photos_{}'.format(chat_id)
                photo_json = r_server.lrange(r_key_user_photos, number, number+1)[0]
                photo = json.loads(photo_json)[-1]['file_id']
                bot.sendPhoto(chat_id, photo)
                
    # save photo id
    elif content_type == "photo":
        r_key_user_photos = 'user_photos_{}'.format(chat_id)
        photo = msg['photo']
        r_server.rpush(r_key_user_photos, json.dumps(photo))


TOKEN = '269068132:AAHW8iuwodWNuH645YOFFvPrLqRPNVHyJN4'
bot = telepot.Bot(TOKEN)
print('Listening ...')
bot.message_loop({'chat': on_chat_message}, run_forever=True)
