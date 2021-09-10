from typing import List, Literal

import requests

API_KEY = open('api_key.txt').read()
BASE_URL = "https://www.googleapis.com/youtube/v3/"


def chunks(l, n):
    return (l[i:i + n] for i in range(0, len(l), n))


########################################################################################
# Functions calling API

# Return a list of video and playlist IDs for a search
def get_search_results(text: str,
                       max_results: int = 10,
                       type: Literal['video', 'playlist'] = 'video') -> List[str]:
    all_items = []
    next_page_token = ""
    while (len(all_items) < max_results) and (next_page_token is not None):
        res = requests.get(BASE_URL + "search",
                           params={
                               "key": API_KEY,
                               "maxResults": max_results,
                               "nextPageToken": next_page_token,

                               "q": text,
                               "part": "id",
                               "type": type
                           })
        res.raise_for_status()
        data = res.json()
        all_items += data['items']
        next_page_token = data.get('nextPageToken')

    id_key = 'videoId' if type == 'video' else 'playlistId'
    id_list = [item['id'][id_key] for item in all_items]
    return id_list


# video_ids = get_search_results("unreal tutorial", 15, 'video')
# playlist_ids = get_search_results("unreal tutorial", 15, 'playlist')


# Get details for a video or list of videos or a playlist
def get_video_details(video_ids: List[str],
                      max_results: int = 10, ):
    all_items = []
    next_page_token = ""
    while len(all_items) < max_results and next_page_token is not None:
        res = requests.get(BASE_URL + "videos",
                           params={
                               "key": API_KEY,
                               "maxResults": max_results,
                               "nextPageToken": next_page_token,

                               "part": "id,snippet,statistics,contentDetails",
                               "id": ','.join(video_ids)
                           })
        res.raise_for_status()
        data = res.json()

        all_items += data['items']
        next_page_token = data.get('nextPageToken')

    return all_items


# details = get_video_details(video_ids)


# Get a playlist_id for the playlist of all channel uploads
# https://stackoverflow.com/questions/18953499/youtube-api-to-fetch-all-videos-on-a-channel
def get_channel_uploads_playlist(channel_id):
    res = requests.get(BASE_URL + "channels",
                       params={
                           "key": API_KEY,

                           "part": "contentDetails",
                           "forUsername": channel_id
                       })
    res.raise_for_status()
    data = res.json()

    if data['pageInfo']['totalResults'] == 0:
        raise ValueError(f"Channel not found: {channel_id}")

    playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return playlist_id


# channel_id = "PewDiePie"
# playlist_id = get_channel_uploads_playlist(channel_id)


def get_playlist_videos(playlist_id,
                        max_results: int = 10
                        ):
    all_items = []
    next_page_token = ""
    while len(all_items) < max_results and next_page_token is not None:
        res = requests.get(BASE_URL + "playlistItems",
                           params={
                               "key": API_KEY,
                               "maxResults": max_results,
                               "nextPageToken": next_page_token,

                               "part": "contentDetails",
                               "playlistId": playlist_id
                           })
        res.raise_for_status()
        data = res.json()

        all_items += data['items']
        next_page_token = data.get('nextPageToken')

    id_list = [item['contentDetails']['videoId'] for item in all_items]

    return id_list


# playlist_videos = get_playlist_videos(playlist_id)


def get_video_comments(video_id,
                       max_results: int = 10
                       ):
    all_items = []
    next_page_token = ""
    while len(all_items) < max_results and next_page_token is not None:
        res = requests.get(BASE_URL + "commentThreads",
                           params={
                               "key": API_KEY,
                               "maxResults": max_results,
                               "nextPageToken": next_page_token,

                               "part": "snippet,replies",
                               "videoId": video_id
                           })
        res.raise_for_status()
        data = res.json()

        all_items += data['items']
        next_page_token = data.get('nextPageToken')

    id_list = [item['id'] for item in all_items]

    return id_list


# video_id = "gw-Oi2i5FyQ"
# comments = get_video_comments(video_id)

