import requests
import json
from urllib.parse import urlencode

API_URL = 'http://ec2-3-107-91-195.ap-southeast-2.compute.amazonaws.com:4444'

def sendQuestion(question,**kwargs):
    fetch = requests.Session()
    kwargs['timeout'] = 15 if 'timeout' not in kwargs else kwargs['timeout']
    kwargs['url']=f'{API_URL}/process_data'
    kwargs['data'] = {"question": question}
    try:
        r= fetch.post(**kwargs)
    except requests.exceptions.Timeout:
        return f"Request timed out ({kwargs['timeout']}s). Please try again."
    except requests.exceptions.RequestException as e:
        return f"Error:{e}"
    finally:
        return json.loads(r.text)['answer']

def cleanMsg(**kwargs):
    fetch = requests.Session()
    kwargs['url'] = f'{API_URL}/clear_messages'
    kwargs['timeout'] = 15 if 'timeout' not in kwargs else kwargs['timeout']
    try:
        r = fetch.get(**kwargs)
    except requests.exceptions.Timeout:
        return f"Request timed out ({kwargs['timeout']}s). Please try again."
    except requests.exceptions.RequestException as e:
        return f"Error:{e}"
    finally:
        return r.text