# log into your Mailchimp account and look at the URL in your browser.
# You’ll see something like https://us19.admin.mailchimp.com/
# the us19 part is the data center.


import hashlib
import json
import requests


def hash_subscriber(email):
    email = email.lower().encode()
    return hashlib.md5(email).hexdigest()


class Mailchimp():
    def __init__(self, server, api_key, list_id=-1):
        self.list_id = list_id
        self.auth = ("", api_key)
        self.api_url = f'https://{server}.api.mailchimp.com/3.0'
        self.make_list_baseurl(list_id)

    def make_list_baseurl(self, list_id):
        self.list_id = list_id
        self.list_baseurl = f'{self.api_url}/lists/{list_id}'

    def get_members_baseurl(self):
        baseurl = f'{self.list_baseurl}/members'
        return baseurl

    def ping(self):
        if self.list_id is None:
            return "Everything's Chimpy!"

        url = f'{self.api_url}/ping'
        response = requests.get(url, auth=self.auth)
        j = response.json()
        return(j['health_status'])

    def get_lists(self):
        url = f'{self.api_url}/lists'
        params = {"fields": "lists.id,lists.name"}
        r = requests.get(url, auth=self.auth, params=params)
        result = dict([[i['name'], i['id']] for i in r.json()['lists']])
        return r.status_code, result

    def add_list(self, name):
        url = f'{self.api_url}/lists'
        contact = {'company': 'Maryland Governor', 'address1': '110 State Circle', 'address2': '',
                   'city': 'Annapolis', 'state': 'MD', 'zip': '21401', 'country': 'USA',
                   'phone': '1-410-974-3901'}
        campaign_defaults = {'from_name': 'Marc', "from_email": 'ms@quizitive.com',
                             'subject': 'testing', 'language': 'en'}
        data = {'name': name, 'contact': contact, 'permission_reminder': 'permission_reminder',
                'campaign_defaults': campaign_defaults, 'email_type_option': False}
        r = requests.post(url, auth=self.auth, data=json.dumps(data))
        self.make_list_baseurl(r.json()['id'])
        return r.status_code, self.list_id

    def delete_list(self, list_id):
        url = f'{self.api_url}/lists/{list_id}'
        r = requests.delete(url, auth=self.auth)
        return r.status_code

    def get_list_id(self, name):
        list_id = -1
        status_code, result = self.get_lists()
        if 200 == status_code and (name in result):
            list_id = result[name]
        return list_id

    def delete_list_by_name(self, name):
        list_id = self.get_list_id(name)
        if type(list_id) == str:
            status_code = self.delete_list(list_id)
        return list_id

    def get_members(self):
        baseurl = self.get_members_baseurl()
        r = requests.get(baseurl, auth=self.auth)
        return r.status_code, dict([(i['email_address'], i['status']) for i in r.json()['members']])

    def add_member_to_list(self, email):
        if self.list_id is None:
            return 200, 'subscribed'

        url = f"{self.get_members_baseurl()}"
        data = {"email_address": email, "status": "subscribed"}
        r = requests.post(url, auth=self.auth, data=json.dumps(data))
        return r.status_code, r.json()['status']

    def update_member(self, email, data={'status': 'subscribed'}):
        if self.list_id is None:
            return 200, data['status']

        sub_hash = hash_subscriber(email)
        url = f"{self.get_members_baseurl()}/{sub_hash}"
        r = requests.put(url, auth=self.auth, data=json.dumps(data))
        return r.status_code, r.json()['status']

    def unsubscribe(self, email):
        data = {'status': 'unsubscribed'}
        return self.update_member(email, data)

    def subscribe(self, email):
        status_code, status = self.add_member_to_list(email)
        if status_code != 200:
            data = {'status': 'subscribed'}
            status_code, status = self.update_member(email, data)
        return status_code, status

    def delete_permanent(self, email):
        # THIS IS VERY PERMANENT

        if self.list_id is None:
            return 200

        sub_hash = hash_subscriber(email)
        url = f"{self.get_members_baseurl()}/{sub_hash}/actions/delete-permanent"
        r = requests.post(url, auth=self.auth)
        return r.status_code
