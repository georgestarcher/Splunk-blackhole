import requests
import logging
import pprint
import json
#import simplejson as json
from requests.auth import HTTPBasicAuth

# This code is actually getting complicated!
# Some things to consider
#
#  Data typing is currently a mess.  Splunk (mostly) doesn't care
#  Long as you keep everything a string.  What we should TRY to do
#  is build in some type safety by looking at the collection
#  configuration, esp w.r.t data types and from there figure out what
#  types we need to cast things to.

logger = logging.getLogger('kvstore_client')
logger.setLevel(logging.INFO)

# Because of how seldom a Splunk instance is set up with good certs
requests.packages.urllib3.disable_warnings()
ssl_verify = False


class HTTPSplunkAuth(requests.auth.AuthBase):
    """Attaches HTTP Splunk Session Authentication to the given Request object."""
    def __init__(self, auth_token):
        self.token = auth_token

    def __eq__(self, other):
        return all([
            self.token == getattr(other, 'token', None)
        ])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['Authorization'] = 'Splunk %s' % str(self.token)
        return r


class KV():
    def __init__(self, url, app, collection, user='nobody', login=None, password=None, auth_token=None, json_cls=None):

        self.url = url
        self.token = auth_token
        self.app = app
        self.collection = collection
        self.user = user
        self.password=password
        self.json_cls=json_cls

        if login is not None  and password is not None:
            self.auth=HTTPBasicAuth(login,password)
        elif auth_token is not None:
            self.auth=HTTPSplunkAuth(auth_token)
        else:
            raise Exception("No No No not in my house")


    # Not really that useful but
    def getCollectionInfo(self):
        headers = {}

        # This call is special, splunkd *requires* a user of "-"  (as of 6.3.5 / 6.4 anyway)
        wholeurl = '/'.join([self.url, 'servicesNS', '-', self.app,
                             'storage/collections/config', self.collection])
        r = requests.get(wholeurl,
                         auth=self.auth,
                         headers=headers,
                         verify=ssl_verify,
                         params={'output_mode': 'json'})
        #logger.debug(wholeurl)
        #logger.debug(r.request.headers)
        #logger.debug(repr(r))
        #logger.debug(r.text)
        #logger.debug(pprint.pformat(r.json()['entry'][0]))
        return r.json()['entry'][0]  # Strip off the outer entry stuff since we should only be returning one

# Returns an array of things

    def get(self, key=None, **kwargs):
        headers = {
            'Content-Type': 'application/json'
        }

        getparams = {
            #'output_mode' : 'json'
        }
        getparams.update(kwargs)

        wholeurl = '/'.join([self.url, 'servicesNS', self.user, self.app,
                             'storage/collections/data', self.collection])

        if key is not None:
            wholeurl = '/'.join([wholeurl, key])

        r = requests.get(wholeurl, 
                         auth=self.auth,
                         headers=headers, 
                         verify=ssl_verify,
                         params=getparams)
        #logger.debug('Request returns status %s ' % r.status_code)
        #logger.debug(wholeurl)
        #logger.debug(r.request)
        #logger.debug(repr(r))
        #logger.debug(r.text)
        #logger.debug(pprint.pformat(r.json()))
        q = r.json()
        #logger.debug('finished jsoning')

        return q

    # Wondering if this should be broken into 'update' and 'create' functions
    # but for now I like the basic get/put semantic
    def put(self, data, key=None, user=None, **kwargs):

        if user is None:
            u=self.user
        else:
            u=user

        headers = {
            'Content-Type': 'application/json'
        }

        getparams = {
            'output_mode' : 'json'
        }

        getparams.update(kwargs)

        wholeurl = '/'.join([self.url, 'servicesNS', u, self.app,
                             'storage/collections/data', self.collection])

        if key is not None:
            wholeurl = '/'.join([wholeurl, key])

        r = requests.post(wholeurl,
                          auth=self.auth,
                          headers=headers,
                          verify=ssl_verify,
                          data=json.dumps(data,cls=self.json_cls))

        logger.debug('Request returns status %s ' % r.status_code)
        #logger.debug(wholeurl)
        #logger.debug(r.request)
        #logger.debug(repr(r))
        #logger.debug(r.text)
        #logger.debug(data)

        if r.status_code == requests.codes.created or r.status_code == requests.codes.ok :
            resdict = json.loads(r.text)
            logger.debug("resdict=%s" % pprint.pformat(resdict))
            return (True,r.status_code,resdict.get('_key',None))

        elif r.status_code == requests.codes.conflict:

            # This may be the wrong thing to do here but
            # From a wrapping API perspective it seems like retrying
            # To update a specific key seems like the right thing to do

            # Warning, recursion :)  And there's no filter on recursion depth here either
            #logger.info("Retrying conflict as update to key=%s" % data['_key'])
            return self.put(data,data['_key'],**kwargs)

        else:
            # Probably an error at this point

            resdict = json.loads(r.text)
            output = None
            if 'messages' in resdict:
                output = "\n".join([ "%s %s" % (f['type'],f['text']) for f in resdict['messages'] ])
            return (False,r.status_code,json.loads(r.text))

