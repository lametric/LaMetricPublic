import httplib2
from urllib.parse import urlencode
import json
import pickle
import base64
from sys import stderr
from json.decoder import JSONDecodeError
import config # <<=== delete if you hard coded your client_id and client_secret below 

CLIENT_ID = config.app['client_id'] # assign your client_id here
CLIENT_SECRET = config.app['client_secret'] # assign your client_secret here

AUTHORIZATION_URL = 'https://developer.lametric.com/api/v2/oauth2/authorize'
TOKEN_URL = 'https://developer.lametric.com/api/v2/oauth2/token'
CALLBACK_URL = 'http://lametric.com/redirect'
SCOPES = 'basic+devices_read'


## Exceptions
class LaMetricException (Exception):
    def __init__(self, message=''):
        Exception.__init__(self)
        self.message = message;
    
    def __str__(self):
        return 'Error. {}'.format(self.message)
    
    
class LaMetricCloudException (LaMetricException):
    def __init__(self, message='', status=0):
        self.status = status;
        LaMetricException.__init__(self, message)
        
    def __str__(self): 
        if self.status == 0:
            return 'LaMetric Cloud Error. {}'.format(self.message)
        else:   
            return 'LaMetric Cloud Error. {}: {}'.format(self.status, self.message)
        
        
class LaMetricDeviceException (LaMetricException):
    def __init__(self, message='', status=0):
        self.status = status
        LaMetricException.__init__(self, message)
        
    def __str__(self): 
        if self.status == 0:
            return 'LaMetric Device Error. {}'.format(self.message)
        else:   
            return 'LaMetric Device Error. {}: {}'.format(self.status, self.message)   
        
        

class LaMetricCloudClient:
    """Simple class for accessing LaMetric Cloud"""
    
    USERS_ME_DEVICES_URL = 'https://developer.lametric.com/api/v2/users/me/devices'
    
    def __init__(self, client_id, client_secret):
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = None
        self._refresh_token = None
        self._http = httplib2.Http()
        return

    def authentication_url(self):
        return AUTHORIZATION_URL + '?response_type=code&client_id=' + \
            self._client_id + '&scope=' + SCOPES + '&redirect_uri=' + \
            CALLBACK_URL

    def authenticate(self, code):   
        if self._access_token != None and self._refresh_token != None:            
            return
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        body = {'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': CALLBACK_URL,
            'code': code}
        try:
            res, content = self._http.request(TOKEN_URL, "POST", urlencode(body), headers)
            parsed = json.loads(content.decode('utf-8'))
            if res.status == 200:              
                self._access_token = parsed['access_token']
                self._refresh_token = parsed['refresh_token']
            else:
                raise LaMetricCloudException(parsed['errors'][0]['message'], res.status)
        except httplib2.ServerNotFoundError:
            raise LaMetricCloudException("Host is not reachable");
        except JSONDecodeError:
            raise LaMetricCloudException("Authenticate. Unknown response format.");
           
           
    def refresh_token(self):
        if self._refresh_token != None:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            body = {'grant_type': 'refresh_token',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': self._refresh_token}
            try:
                res, content = self._http.request(TOKEN_URL, "POST", urlencode(body), headers)
                parsed = json.loads(content.decode('utf-8'))
                if res.status == 200:
                    self._access_token = parsed['access_token']
                    self._refresh_token = parsed['refresh_token']
                else:
                    raise LaMetricCloudException(parsed['errors'][0]['message'], res.status)
            except httplib2.ServerNotFoundError:
                raise LaMetricCloudException("Host is not reachable")
            except JSONDecodeError:
                raise LaMetricCloudException("Refresh token. Unknown response format.")
            
    
    def has_refresh_token(self):
        return self._refresh_token != None
        
        
    def get_devices(self):
        headers = {'Accept': 'application/json', 
                   'Authorization': 'Bearer %s' % self._access_token};
        res = {}
        try:
            res, body = self._http.request(LaMetricCloudClient.USERS_ME_DEVICES_URL, 
                                           "GET", 
                                           headers=headers)
            devices = json.loads(body.decode('utf-8'))     
            if res.status == 200:
                return devices
            else:
                raise LaMetricCloudException(devices['errors'][0]['message'],res.status)
        except httplib2.ServerNotFoundError:            
            raise LaMetricCloudException("Host is not reachable")
        except JSONDecodeError:
            raise LaMetricCloudException("Unknown response format")
        
        
    def save_state(self):
        state = {}
        state['access_token'] = self._access_token;
        state['refresh_token'] = self._refresh_token;
        with open ('lametric_cloud.pickle', 'wb') as f:
            pickle.dump(state, f)
        return
    
    
    def restore_state(self):
        try:
            with open ('lametric_cloud.pickle', 'rb') as f:
                state = pickle.load(f)     
                self._access_token = state['access_token']
                self._refresh_token = state['refresh_token']
        except FileNotFoundError:
            # No file, not restoring state
            return



class LaMetricDeviceClient:
    """ Simple LaMetric Time client
    """
    ## API endpoints
    API_URL = 'http://{host}:{port}/api/v2'
    DEVICE_URL = 'http://{host}:{port}/api/v2/device'
    NOTIFICATION_URL = 'http://{host}:{port}/api/v2/device/notifications' 
    
    
    def __init__(self, ip, api_key):
        self._ipv4 = ip
        self._api_key = api_key
        self._http = httplib2.Http()
        return
    
    
    def get_api_info(self):     
        auth = 'dev:'+self._api_key;
        headers = {'Authorization': 'Basic ' + base64.b64encode(auth.encode()).decode('utf-8'), 
                   'Accept':'application/json'}       
        res, body = self._http.request(LaMetricDeviceClient.API_URL.format(host=self._ipv4, 
                                                                           port=8080), 
                                       "GET", headers=headers)
        parsed = json.loads(body.decode('utf-8'))
        if res.status == 200:            
            return parsed
        else:
            raise LaMetricDeviceException(parsed['errors'][0]['message'], res.status)
        
        
    def get_device_info(self):
        auth = 'dev:'+self._api_key;
        headers = {'Authorization': 'Basic ' + base64.b64encode(auth.encode()).decode('utf-8'), 
                   'Accept':'application/json'}       
        res, body = self._http.request(LaMetricDeviceClient.DEVICE_URL.format(host=self._ipv4, 
                                                                              port=8080),
                                       "GET", headers=headers)
        parsed = json.loads(body.decode('utf-8'))
        if res.status == 200:
            return parsed
        else:
            raise LaMetricDeviceException(parsed['errors'][0]['message'], res.status)
                                                                           
            
    def send_notification(self, frames, repeat=1, sound={}):    
        auth = 'dev:'+self._api_key;
        headers = {'Authorization': 'Basic ' + base64.b64encode(auth.encode()).decode('utf-8'), 
                   'Accept':'application/json',
                   'Content-Type':'application/json'}  
        body = {
                'priority':'warning',
                'icon_type':'info',
                'model': {
                          'frames':frames,
                          'cycles':repeat,
                          'sound':sound
                          }
        }
        
        try:
            res, body = self._http.request(LaMetricDeviceClient.NOTIFICATION_URL.format(host=self._ipv4, 
                                                                              port=8080),
                                       "POST",
                                       body=json.dumps(body).encode('utf-8'),
                                       headers = headers)
            parsed = json.loads(body.decode('utf-8'))
            if res.status == 200 or res.status == 201:            
                return parsed
            else:
                raise LaMetricDeviceException(parsed['errors'][0]['message'], res.status)
        except httplib2.ServerNotFoundError:            
            raise LaMetricDeviceException("Host is not reachable")
        except JSONDecodeError:
            raise LaMetricDeviceException("Unknown response format")
        
        
                                                      
def run_example():
    print('LaMetric Time API Demo')
    lametric_client = LaMetricCloudClient(CLIENT_ID, CLIENT_SECRET)
    lametric_client.restore_state()  
    
    try:
        if lametric_client.has_refresh_token(): 
            lametric_client.refresh_token()
        else:
            print('Insert this URL into browser: {}'.format(lametric_client.authentication_url()))
            code = input('Insert code here ------->>>')
            lametric_client.authenticate(code)
        
        lametric_client.save_state()
        devices = lametric_client.get_devices()        
        count = len(devices)
        
        print('You have {} device(s):'.format(count))
        for idx, device in enumerate(devices):
            print(' {}  Name: \"{}\", connected to: \"{}\", IP: {}'
              .format(idx+1, 
                      device['name'], 
                      device['wifi_ssid'], 
                      device['ipv4_internal']))
        
        index = 0
        while (index < 1 or index > count):
            index = int(input('Choose device [1-{}]:'.format(count)))
            index = index-1
      
        device_ip = devices[index]['ipv4_internal']
        device_api_key = devices[index]['api_key']  
        device_client = LaMetricDeviceClient(device_ip, device_api_key) 
        
        while True:
            icon = input("Enter icon code or hit enter (find code on http://developer.lametric.com/icons) [a2867] ---> ")
            if icon == 'exit':
                break
            if icon == '':
                icon = 'a2867'
            message = input("Enter message or hit enter [WORKS!]--> ")
            if message == '':
                message = 'WORKS!'
                
            frames = [
                      {"icon":icon,
                       "text":message}
                      ]
            
            sound = {"category":"notifications","id":"positive1"}            
            device_client.send_notification(frames=frames, sound=sound)
            print("====Success! One more try (type \"exit\" to stop)====")
        
    except LaMetricException as e:
        print(e, file=stderr)
    

if __name__ == '__main__':
    try:
        run_example()    
    finally:
        print('\nDone.')
        exit(0)
