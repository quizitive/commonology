# https://github.com/mailchimp/mailchimp-marketing-python
import os
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing import api_client

# log into your Mailchimp account and look at the URL in your browser.
# You’ll see something like https://us19.admin.mailchimp.com/
# the us19 part is the server prefix.
SERVER_PREFIX = 'us2'


# https://stackoverflow.com/questions/64682474/python-and-mailchimp-integration
def send_mail():
    # find this out at https://mailchimp.com/en/help/about-api-keys/
    api_key = os.getenv('MAILCHIMP_APIKEY')

    try:
        client = MailchimpMarketing.Client()
        client.set_config({"api_key": api_key, "server": SERVER_PREFIX})

        # find out list id: https://mailchimp.com/en/help/find-audience-id/
        campaign_data = dict(
            type='regular',
            recipients=dict(list_id='…'),
            settings=dict(
                subject_line='lorem ipsum',
                from_name='John Doe',
                reply_to='john@doe.com',
            )
        )
        campaign = client.campaigns.create(campaign_data)
        print(campaign)
        campaign_id = campaign['id']
        content_data = dict(
            plain_text='lorem ipsum',
            html='<p><strong>lorem</strong><br />ipsum</p>'
        )
        response = client.campaigns.set_content(campaign_id, content_data)
        print(response)

        response = client.campaigns.send(campaign_id)
        print(response)
    except api_client.ApiClientError as error:
        print("Error: {}".format(error.text))
