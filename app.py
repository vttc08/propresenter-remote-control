from flask import Flask, render_template, request
import requests as req
import os
import dotenv
import time

dotenv.load_dotenv(".env")

BASE_URL = os.getenv('PP_BASE_URL')


s = req.Session()
app = Flask(__name__)

def prev_next_req(url, mode):
    endpoint = f'{url}/v1/trigger/{mode}'
    s.get(endpoint)

def get_macros():
    endpoint = f'{BASE_URL}/v1/macros?chunked=false'
    response = s.get(endpoint).json()
    return [macro.get('id').get('name') for macro in response]

def get_active():
    endpoint = f'{BASE_URL}/v1/presentation/slide_index?chunked=false'
    response = s.get(endpoint).json()
    response = response['presentation_index']
    uuid = response['presentation_id'].get('uuid')
    name = response['presentation_id'].get('name')
    index = response.get('index')
    return uuid, name, index

def get_image(quality=400):
    uuid, name, index = get_active()
    endpoint = f'{BASE_URL}/v1/presentation/{uuid}/thumbnail/{index}?quality={quality}'
    return endpoint

def get_other_images():
    uuid, name, index = get_active()
    images = []
    for i in range(index-2, index+3):
        images.append(f'{BASE_URL}/v1/presentation/{uuid}/thumbnail/{i}?quality=400')
    return images

def stream_status():
    endpoint = f'{BASE_URL}/v1/capture/status'
    response = s.get(endpoint).json()
    response = response['status']
    if response == "inactive":
        return False
    else:
        return True
    
def validate_settings():
    endpoint = f'{BASE_URL}/v1/capture/settings'
    response = s.get(endpoint).json()
    routing = response['audio_routing']
    if routing[2] == [0] and routing[3] == [1] \
    and routing[0] == [] and routing[1] == []:
        return True
    else:
        return False

@app.route('/', methods=['GET'])
def index():
    curr_image = get_image(quality=400)
    return render_template('index.html', macros=get_macros(), image=curr_image, livestream=stream_status(), otherimages=get_other_images(), presentation=get_active()[1])
    
@app.route('/', methods=['POST'])
def prev_next():
    index = get_active()[2]
    action = request.form.get('slide')
    prev_next_req(BASE_URL, action)
    while index == get_active()[2]:
        pass
    curr_image = get_image(quality=400)
    return render_template('index.html', macros=get_macros(), image=curr_image, livestream=stream_status(), otherimages=get_other_images(), presentation=get_active()[1])

@app.route('/macro', methods=['POST'])
def trigger_macro():
    macro = request.form.get('action')
    print(f'{BASE_URL}/v1/macro/{macro}/trigger')
    endpoint = f'{BASE_URL}/v1/macro/{macro}/trigger'
    print(endpoint)
    s.get(endpoint)
    return '', 204

@app.route('/livestream', methods=['POST'])
def toggle_livestream():
    livestream = stream_status()
    if livestream: # livestream is on
        action = 'stop'
    else:
        action = 'start'
    valid_settings = validate_settings()
    if valid_settings:
        endpoint = f'{BASE_URL}/v1/capture/{action}'
        s.get(endpoint)
        time.sleep(1)
        return render_template('index.html', macros=get_macros(), image=get_image(quality=400), livestream=stream_status())
    else:
        return render_template('index.html', macros=get_macros(), image=get_image(quality=400), livestream=stream_status(), valid_settings="Invalid settings. Please check your audio routing.")

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv('PORT'))
