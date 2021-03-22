# Evolved from Justin Mitchel - https://www.codingforentrepreneurs.com/blog/Mailchimp-integration
# Also see https://Mailchimp.com/developer/marketing/api

# log into your Mailchimp account and look at the URL in your browser.
# You’ll see something like https://us19.admin.mailchimp.com/
# the us19 part is the data center.


import hashlib
import json
import requests


def get_subscriber_hash(email):
    email = email.lower().encode()
    return hashlib.md5(email).hexdigest()


class Mailchimp(object):
    def __init__(self, server, api_key, list_id):
        super(Mailchimp, self).__init__()
        self.auth = ("", api_key)
        self.api_url  = f'https://{server}.api.mailchimp.com/3.0'
        self.list_baseurl = f'{self.api_url}/lists/{list_id}'

    def get_members_baseurl(self):
        baseurl = f'{self.list_baseurl}/members'
        return baseurl

    def ping(self):
        url = f'{self.api_url}/ping'
        return requests.get(url, auth=self.auth)

    def add_list(self, name):
        url = f'{self.api_url}/lists'
        contact = {'company': 'Quizitive, LLC', 'address1': '3421 Terrapin Road', 'address2': '',
                   'city': 'Baltimore', 'state': 'MD', 'zip': '21208', 'country': 'USA',
                   'phone': '1-212-580-1175'}
        campaign_defaults = {'from_name': 'Marc', "from_email": 'ms@quizitive.com',
                             'subject': 'testing', 'language': 'en'}
        data = {'title': name, 'name': name, 'contact': contact, 'permission_reminder': 'permission_reminder',
                'campaign_defaults': campaign_defaults, 'email_type_option': False}
        r = requests.post(url, auth=self.auth, data=json.dumps(data))
        return r.status_code, r.json()

    def get_members(self):
        baseurl = self.get_members_baseurl()
        r = requests.get(baseurl, auth=self.auth)
        return r.status_code, [(i['email_address'], i['status']) for i in r.json()['members']]

    def delete_member(self, email):
        # THIS IS VERY PERMANENT
        sub_hash = get_subscriber_hash(email)
        url = f"{self.get_members_baseurl()}/{sub_hash}/actions/delete-permanent"
        r = requests.post(url, auth=self.auth)
        return r.status_code, r.json()

    def add_member_to_list(self, email):
        url = f"{self.get_members_baseurl()}"
        data = {"email_address": email, "status": "subscribed"}
        r = requests.post(url, auth=self.auth, data=json.dumps(data))
        return r.status_code, r.json()

    # ...


    def check_valid_status(self, status):
        choices = ['subscribed','unsubscribed', 'cleaned', 'pending']
        if status not in choices:
            raise ValueError("Not a valid choice")
        return status

    def change_subscription_status(self, email, status):
        subscriber_hash     = get_subscriber_hash(email)
        members_baseurl       = self.get_members_baseurl()
        baseurl            = "{members_baseurl}/{sub_hash}".format(
                                members_baseurl=members_baseurl, 
                                sub_hash=subscriber_hash
                                )
        data                = {
                                "status": self.check_valid_status(status)
                            }
        r                   = requests.put(baseurl, 
                                auth=self.auth,
                                data=json.dumps(data)
                                )
        return r.status_code, r.json()

    def check_subscription_status(self, email):
        subscriber_hash     = get_subscriber_hash(email)
        members_baseurl       = self.get_members_baseurl()
        baseurl            = "{members_baseurl}/{sub_hash}".format(
                                members_baseurl=members_baseurl, 
                                sub_hash=subscriber_hash
                                )
        r                   = requests.get(baseurl, 
                                auth=self.auth
                                )
        return r.status_code, r.json()

    def unsubscribe(self, email):
        return self.change_subscription_status(email, status='unsubscribed') 

    def resubscribe(self, email):
        return self.change_subscription_status(email, status='subscribed')

    def subscribe(self, email):
        sub_hash = get_subscriber_hash(email)
        url = f"{self.get_members_baseurl()}/{sub_hash}/actions/delete-permanent"
        r = requests.post(url, auth=self.auth)
        return r.status_code, r.json()




        # pass    ... more to do here
        # If on list then resubscribe else subscribe
        # self.check_subscription_status(email)
        # self.resubscribe(email)
    
