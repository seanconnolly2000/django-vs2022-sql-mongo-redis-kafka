import requests    
 
class api_base(object):
  # Below are examples of possible API calls.
    def __init__(self): 
        self.headers = {"Authorization": "Token XXXXXXXXXXXXXXXXXXXXXXXXXX"}

    def _make_request(self, url):
        try:
            res = requests.get(url=url, headers=self.headers)
            data = res.json()
            return data
        except:
            return None

class apis(api_base):
    def service(self):
        return {'json_data': True}
        url = "https://.../api/v1/service"  #put valid service here
        return self._make_request(url)
 
    def service_with_parameter(self, pk):
        url = f"https://../api/v1/service/{pk}"  #put valid service here
        return self._make_request(url)
 


