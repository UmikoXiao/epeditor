import requests
import json
from urllib.parse import urlencode

API_URL = 'http://ec2-3-107-91-195.ap-southeast-2.compute.amazonaws.com:4444'

def sendQuestion(question,**kwargs):
    """
    Send a question to the API and return the answer.
    
    Parameters
    ----------
    question : str
        The question to be sent to the API for processing.
    **kwargs : dict, optional
        Additional keyword arguments to pass to the requests.post method.
        Supported options include 'timeout' (int or float, default 15) and 'url' (str, automatically set).
    
    Returns
    -------
    str
        The answer from the API response. If a timeout or request exception occurs, an error message is returned instead.
    """
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
    """
    Clear messages by sending a GET request to the specified API endpoint.
    
    Parameters
    ----------
    **kwargs : dict
        Arbitrary keyword arguments passed to the requests.Session.get method.
        Expected keys include:
        - 'url' (str): The API endpoint URL, automatically set to '{API_URL}/clear_messages'.
        - 'timeout' (float or tuple, optional): How long to wait for the server to send data before giving up, default is 15 seconds.
    
    Returns
    -------
    str
        Response text if the request is successful; otherwise, an error message indicating timeout or request exception.
    """
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