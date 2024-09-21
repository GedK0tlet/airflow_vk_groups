import requests
from docutils.nodes import comment

base_url='https://api.vk.com/method/'

def fetch_data(token: str, link: str, ti, **kwargs):
    result = wall_get(domain=link, serv_key=token, count_posts=1)
    comments = ""
    for item in result[1][0]:
        if item != '':
            comments += f":{item}:"
    ti.xcom_push(key='linck_group', value=link)
    ti.xcom_push(key='text_post', value=result[0][0][0])
    ti.xcom_push(key='vk_post_id', value=result[0][0][1])
    ti.xcom_push(key='comments_post', value=comments)

def wall_get(domain, serv_key, count_posts):
    url=base_url+'wall.get'
    comments = []
    posts = []
    payload={'access_token': serv_key,'owner_id': -1,'domain':f'{domain}', 'offset':0, 'count':count_posts, 'v': "5.236"}
    resp =  requests.post(url,data=payload)
    if resp.status_code==200:
        q = resp.json()['response']['items']
        for item in q:
            posts.append([item['text'], item['id']])
            tr = wall_getComment(post_id=item['id'], count_comments=10, owner_id=int(item['owner_id']), serv_key=serv_key)
            comments.append(tr)
        return posts, comments

    else:
        print('Somthing strange')

def wall_getComment(post_id, count_comments, owner_id, serv_key):
    url=base_url+'wall.getComments'
    threads_msgs = []
    payload={'access_token': serv_key,'owner_id': owner_id,'post_id':f'{post_id}', 'offset':0, 'thread_items_count': 10,  'count':count_comments, 'v': "5.236"}
    resp =  requests.post(url,data=payload)
    if resp.status_code==200:
        try:
            q = resp.json()["response"]["items"]
            for item in q:
                threads_msgs.append(item['text'])
                thred = item["thread"]['items']
                for m in thred:
                    import re
                    s = re.sub(r'\[.*?\]', '', m['text'])
                    if s != ',' or s != ',':
                        threads_msgs.append(s)
                    else: pass
            return threads_msgs
        except:
            return []
    else:
        print('Somthing strange')