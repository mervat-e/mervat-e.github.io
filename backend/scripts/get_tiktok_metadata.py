import requests
import json
import os
import time
import re
from bs4 import BeautifulSoup

def __load_json(path):
    with open(path) as file:
        data = json.load(file)
    return data

def __extract_tiktok_video_links(filename):
    video_links = []
    data = __load_json(f'resources/user_data/tiktok/{filename}')
    videolist = data["Your Activity"]["Watch History"]["VideoList"]
    for video in videolist:
        video_links.append(video["Link"])
    return video_links

def get_video_data(video_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/",
    }
    try:
        with requests.Session() as s:
            response = s.get(video_url, headers=headers)
            response.raise_for_status()
            return response.text, s.cookies.get_dict()
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None

def get_comments(video_id, cookies):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://www.tiktok.com/@user/video/{video_id}",
        "Accept": "application/json, text/plain, */*",
    }
    
    params = {
        "aweme_id": video_id,
        "count": 5,
        "cursor": 0,
        "device_platform": "web",
        "aid": 1988  # TikTok's web app ID
    }
    
    try:
        response = requests.get(
            "https://www.tiktok.com/api/comment/list/",
            headers=headers,
            params=params,
            cookies=cookies
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Comment request failed: {e}")
        return None

def parse_video_data(html):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        script_tag = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
        data = json.loads(script_tag.string)
        
        # Updated JSON path
        item_info = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {})
        if not item_info:
            return None

        author = item_info.get('author', {})
        stats = item_info.get('stats', {})
        desc = item_info.get('desc', '')
        commerce_info = item_info.get('commerceConfigData', {})
        
        # Extract content disclosure
        has_content_disclosure = commerce_info.get('has_affiliate', False) or \
                               commerce_info.get('commerce_user', {}).get('commercial_activity_enabled', False)

        return {
            'author': author.get('uniqueId'),
            'author_url': f"https://www.tiktok.com/@{author.get('uniqueId')}",  # Added account URL
            'description': desc,
            'hashtags': re.findall(r'#(\w+)', desc),
            'account_name': author.get('uniqueId'),
            'links': re.findall(r'https?://\S+', desc),
            'likes': stats.get('diggCount'),
            'comments_count': stats.get('commentCount'),
            'has_content_disclosure': has_content_disclosure
        }
    except Exception as e:
        print(f"Parsing failed: {e}")
        return None

def parse_comments(comments_data):
    if not comments_data or comments_data.get('status_code') != 0:
        return []
    
    return [{
        'user': c.get('user', {}).get('unique_id'),
        'comment': c.get('text'),
        'likes': c.get('digg_count'),
        'timestamp': c.get('create_time')
    } for c in comments_data.get('comments', [])[:5]]

def get_tiktok_metadata(video_url):
    html, cookies = get_video_data(video_url)
    if html and cookies:
        video_info = parse_video_data(html)
        if video_info:
            # Extract video ID using improved regex
            video_id = re.search(r'/video/(\d+)', video_url.split('?')[0]).group(1)
            comments_data = get_comments(video_id, cookies)
            video_info['first_comments'] = parse_comments(comments_data)
            return video_info
    return None

def save_new_tiktok_metadata_video(filename):
    video_links = __extract_tiktok_video_links(filename)
    if not os.path.exists('resources/tiktok_video/tiktok_metadata.json'):
        # Create the directory if it doesn't exist
        with open('resources/tiktok_video/tiktok_metadata.json', 'w') as file:
            json.dump({"metadata": {}, "account_metadata":{}}, file, indent=4)
        print("File created successfully.")

    with open('resources/tiktok_video/tiktok_metadata.json', "r") as file:
        try:
            tiktok_metadata = json.load(file)
        except Exception as e:
            print(f"Error loading JSON: {e}")


    for link in video_links:
        print(video_links.index(link)/len(video_links) * 100, "%")
        if link in tiktok_metadata["metadata"]:
            print(f"Metadata for {link} already exists.")
            continue
        try:
            data = get_tiktok_metadata(link)
            tiktok_metadata["metadata"].update({link: data})
            account_url = tiktok_metadata["metadata"][link]["author_url"]
            if account_url not in tiktok_metadata["account_metadata"]:
                account_data = get_tiktok_account(account_url)
                tiktok_metadata["account_metadata"].update({account_url: account_data})
        except Exception as e:
            print(f"Error fetching data for {link}: {e}")
    with open('resources/tiktok_video/tiktok_metadata.json', 'w') as file:
        json.dump(tiktok_metadata, file, indent=4)
###################################
###########ACCOUNT#################
###################################
def get_account_data(account_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/",
    }
    try:
        with requests.Session() as s:
            response = s.get(account_url, headers=headers)
            response.raise_for_status()
            return response.text, s.cookies.get_dict()
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None

def parse_account_data(html):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        script_tag = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
        data = json.loads(script_tag.string)
        
        # Extract account information
        user_info = data.get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {}).get('userInfo', {})
        if not user_info:
            return None

        user_data = user_info.get('user', {})
        stats = user_info.get('stats', {})

        return {
            'account_name': user_data.get('uniqueId'),
            'biography': user_data.get('signature'),
            'total_likes': stats.get('heartCount'),  # Might be total likes received
            'followers': stats.get('followerCount'),
            'following': stats.get('followingCount'),
            'video_count': stats.get('videoCount'),
        }
    except Exception as e:
        print(f"Parsing failed: {e}")
        return None
    
def get_tiktok_account(account_url):
    html, cookies = get_account_data(account_url)
    if html:
        account_info = parse_account_data(html)
        if account_info:
            return account_info
        else:
            print("Failed to parse account data.")
    else:
        print("Could not retrieve account page.")