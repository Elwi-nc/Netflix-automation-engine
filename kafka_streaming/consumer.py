from confluent_kafka import Consumer
import json
import ccloud_lib
import time
import pandas as pd
import os
import pickle

# Kafka config
CONF = ccloud_lib.read_ccloud_config("python.config")
TOPIC = "netflix_recommandation" 
consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(CONF)
consumer_conf['group.id'] = 'netflix_reco'
consumer_conf['auto.offset.reset'] = 'latest'
consumer = Consumer(consumer_conf)
consumer.subscribe([TOPIC])

# Get title-id mapping for all movies
df_title = pd.read_csv('movie_titles.csv', encoding = "ISO-8859-1", header = None, names = ['Movie_Id', 'Year', 'Name'], on_bad_lines='skip')
df_title.set_index('Movie_Id', inplace = True)

# load recommendation model
svd = pickle.load(open('model_p.sav', 'rb'))

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            print("Waiting for message or event/error in poll()")
            continue
        elif msg.error():
            print('error: {}'.format(msg.error()))
        else:
            record_key = msg.key()
            record_value = msg.value()
            model_input = json.loads(record_value) # input to feed to model : a user ID
            # Display the 10 most recommended movies for user :
            user_pred = df_title.copy() 
            user_pred = user_pred.reset_index()
            user_pred['Estimate_Score'] = user_pred['Movie_Id'].apply(lambda x: svd.predict(model_input, x).est)
            user_pred = user_pred.sort_values('Estimate_Score', ascending=False)
            print(user_pred.reset_index().drop(columns=['Year', 'Movie_Id', 'index']).head(10))
            time.sleep(1)
            
except KeyboardInterrupt:
    pass
finally:
    consumer.close()

