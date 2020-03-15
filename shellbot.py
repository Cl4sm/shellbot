#!/usr/bin/env python3.7
import json
import os
import random
import pprint
from datetime import datetime

import slack
import requests
from flask import Flask, request

from ctf_time import CTFTime

app = Flask(__name__)
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
client = slack.WebClient(token=SLACK_BOT_TOKEN)

active_users = []
chosen_ctf = {}
current_voting = {}

pp = pprint.PrettyPrinter(indent=4)

def get_active_users_from_channel():
    pass
    #client.users_list()

@app.route('/vote_upcoming_ctfs', methods=['POST'])
def upcoming_ctfs():
    assert request.method == 'POST'

    slack_data = {"blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Upcoming CTFs*"
            }
        }
    ]}

    for ctf in [x for x in ctf_t.upcoming_ctfs if not x['onsite']]:
        fields = []
        fields.append({
            "type": "mrkdwn",
            "text": f"*CTF*\n<{ctf['url']}|{ctf['title']}>"
        })

        fields.append({
            "type": "mrkdwn",
            "text": f"*ctftime*\n<{ctf['ctftime_url']}>"
        })

        fields2 = []

        fields2.append({
            "type": "mrkdwn",
            "text": f"*Start Time*\n<!date^{int(datetime.fromisoformat(ctf['start']).timestamp())}^{{date_long_pretty}} {{time}} | {ctf['start']}>"
        })

        fields2.append({
            "type": "mrkdwn",
            "text": f"*End Time*\n<!date^{int(datetime.fromisoformat(ctf['finish']).timestamp())}^{{date_long_pretty}} {{time}} | {ctf['finish']}>"
        })

        duration_string = ""
        if ctf['duration']['days'] > 0:
            duration_string += str(ctf['duration']['days']) + " day"
            if ctf['duration']['days'] > 1:
                duration_string += 's'

        duration_string += " "
        if ctf['duration']['hours'] > 0:
            duration_string += str(ctf['duration']['hours']) + " hour"
            if ctf['duration']['hours'] > 1:
                duration_string += 's'

        fields3 = []

        fields3.append({
            "type": "mrkdwn",
            "text": f"*Duration*\n{duration_string}"
        })
        fields3.append({
            "type": "mrkdwn",
            "text": f"*Votes*\n0"
        })

        actions = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "This one!",
                        "emoji": False
                    },
                    "style": "primary",
                    "value": f"vote_{ctf['id']}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Description",
                        "emoji": False
                    },
                    "value": f"desc_{ctf['id']}"
                }
            ]
        }

        section = {
            "type": "section",
            "fields": fields,
            "block_id": f"start_{ctf['id']}"
        }
        section2 = {
            "type": "section",
            "fields": fields2,
        }

        section3 = {
            "type": "section",
            "fields": fields3,
            "block_id": f"end_{ctf['id']}"
        }

        slack_data['blocks'].append(section)
        slack_data['blocks'].append(section2)
        slack_data['blocks'].append(section3)
        slack_data['blocks'].append(actions)
        slack_data['blocks'].append({"type": "divider"})

    client.chat_postMessage(
        channel=request.form['channel_id'],
        blocks=slack_data['blocks']
    )
    return ""


@app.route('/active_users', methods=["POST"])
def workspace_active_users():
    assert request.method == "POST"
    response = client.conversations_list()
    assert response['ok']
    #pp.pprint(response.data['channels'])
    channels = [x for x in response.data['channels']]
    for chan in channels:
        pp.pprint(chan['name'])
    return ""
    #with open('./active_users_list', 'rb') as f:
    #    active_users = json.load(f)
    #    return json.dumps(list(active_users.keys()))


#@app.route('/update_active_users')
#def update_active_users():
#    with open('./active_users_list', 'w+') as f:
#        active_users = get_active_users()
#        json.dump(active_users, f)
#    return json.dumps(True)


@app.route('/syscall', methods=['POST'])
def syscall():
    assert request.method == 'POST'
    pp.pprint(request.form)
    arch, syscall = request.form['text'].split(' ')
    all_syscalls = []
    found_syscalls = []
    try:
        with open(f'./syscalls/{arch}_syscalls.json', 'rb') as f:
            all_syscalls = json.load(f)
    except Exception as e:
        print(f"COULD NOT OPEN: syscalls/{arch}_syscalls.json")
        print(e)
        client.chat_postEphemeral(
            channel=request.form['channel_id'],
            text="That arch isn't supported, try: x86, x64",
            user=request.form['user_id']
        )
        return ''

    if '0x' in syscall:
        syscall = int(syscall, 16)
    elif syscall.isdigit():
        syscall = int(syscall)

    if type(syscall) is int:
        for sc in all_syscalls:
            if 'rax' in sc and int(sc['rax']) == int(syscall):
                found_syscalls.append(sc)
                break
    else:
        for sc in all_syscalls:
            if 'name' in sc and syscall.strip().lower() == sc['name'].strip().lower():
                found_syscalls.append(sc)

    sys_output = []
    for sc in found_syscalls:
        sys_str = []
        for key in [x for x in sc.keys() if x != 'name']:
            sys_str.append(f"*{key}*: {sc[key]}")
        sys_output.append(sc['name'] + ' - ' + f'\n\t'.join(sys_str) + ')')

    result = client.conversations_open(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": '\n\n'.join(sys_output)
                }

            }
        ],
        users=[request.form['user_id']]
    )
    print(result)
    return ''

@app.route('/close_voting', methods=['POST'])
def close_voting():
    assert request.method == 'POST'
    if current_voting:
        blocks = chosen_ctf['blocks']
        blocks[-1]['elements'] = blocks[-1]['elements'][1:]
        blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Chosen CTF*"
            }
        }] + blocks

        client.chat_postMessage(
            channel=request.form['channel_id'],
            blocks=blocks
        )

        chosen_ctf['blocks']= []
        chosen_ctf['vote_num'] = 0
        for i in range(len(current_voting['blocks'])):
            if 'elements' in current_voting['blocks'][i] and len(current_voting['blocks'][i]['elements']) > 1:
                current_voting['blocks'][i]['elements'] = current_voting['blocks'][i]['elements'][1:]
        
        client.chat_update(
            ts=current_voting['ts'],
            channel=request.form['channel_id'],
            blocks=current_voting['blocks']
        )

        response = client.conversations_create(
            name=f"{chosen_ctf['name'].split(' ')[0]}_{datetime.now().year}".lower(),
        )
        client.channels_setTopic(
            channel=response.data['channel']['id'],
            topic=f"{chosen_ctf['url']} Team: Shellphish, Password: {open('./shellphish_pass', 'r').read().strip()}"
        )

        for user in [x['id'] for x in client.users_list().data['members']]:
            try:
                client.channels_invite(
                    channel=response.data['channel']['id'],
                    user=user
                )
            except slack.errors.SlackApiError as e:
                pp.pprint(e)
                pass
    return ''

@app.route('/interaction', methods=['POST'])
def interaction():
    assert request.method == 'POST'
    interaction_response = json.loads(request.form['payload'])

    if 'desc' in interaction_response['actions'][0]['value']:
        ctf = [x for x in ctf_t.upcoming_ctfs if x['id'] == int(
            interaction_response['actions'][0]['value'].replace('desc_', ''))][0]
        modal = {
            "trigger_id": interaction_response['trigger_id'],
            "view": {
                "type": "modal",
                "callback_id": "modal-identifier",
                "title": {
                    "type": "plain_text",
                    "text": f"Description"
                },
                "blocks": [
                    {
                        "type": "section",
                        "block_id": "section-identifier",
                        "text": {
                            "type": "mrkdwn",
                            "text": ctf['description']
                        },
                    }
                ]
            }
        }

        client.views_open(
            trigger_id=modal['trigger_id'],
            view=modal['view']

        )
    elif 'vote' in interaction_response['actions'][0]['value']:
        ctf = [x for x in ctf_t.upcoming_ctfs if x['id'] == int(
            interaction_response['actions'][0]['value'].replace('vote_', ''))][0]
        new_blocks = interaction_response['message']['blocks']
        for block in new_blocks:
            if block['block_id'] == f"end_{interaction_response['actions'][0]['value'].replace('vote_', '')}":
                vote = block['fields'][-1]['text'].split('\n')
                vote[1] = str(int(vote[1]) + 1)

                if len(vote) != 3:
                    vote.append(f"<@{interaction_response['user']['id']}>")
                else:
                    if interaction_response['user']['id'] in vote[2].replace("<@", "").replace(">", "").split(", "):
                        return ""
                    else:
                        pp.pprint(interaction_response['user']['id'])
                        pp.pprint(vote[2].replace("<@", "").replace(">", "").split(", "))

                    if len(vote[2].split(", ")) > 2:
                        members = vote[2].split(', ')
                        vote[2] = ", ".join([f"<@{interaction_response['user']['id']}>", members[0], members[1], '...'])
                    else:
                        vote[2] = f"<@{interaction_response['user']['id']}>, " + vote[2]

                block['fields'][-1]['text'] = '\n'.join(vote)
                if chosen_ctf:
                    if int(vote[1]) > chosen_ctf['vote_num']:
                        chosen_ctf['vote_num'] = int(vote[1])
                        start_idx = [x for x in range(len(new_blocks)) if 'block_id' in new_blocks[x] and new_blocks[x]['block_id'] == f"start_{interaction_response['actions'][0]['value'].replace('vote_', '')}"][0]
                        chosen_ctf['blocks'] = new_blocks[start_idx:start_idx+4]
                        chosen_ctf['name'] = ctf['title']
                        chosen_ctf['url'] = ctf['ctftime_url']

                else:
                    chosen_ctf['vote_num'] = int(vote[1])
                    start_idx = [x for x in range(len(new_blocks)) if 'block_id' in new_blocks[x] and new_blocks[x]['block_id'] == f"start_{interaction_response['actions'][0]['value'].replace('vote_', '')}"][0]
                    chosen_ctf['blocks'] = new_blocks[start_idx:start_idx+4]
                    chosen_ctf['name'] = ctf['title']
                    chosen_ctf['url'] = ctf['ctftime_url']

        if not current_voting:
            current_voting['ts'] = interaction_response['container']['message_ts']

        current_voting['blocks'] = new_blocks
        client.chat_update(
            ts=interaction_response['container']['message_ts'],
            channel=interaction_response['channel']['id'],
            blocks=new_blocks
        )
    return ""


@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    ctf_t = CTFTime()
    app.run(host='0.0.0.0')
