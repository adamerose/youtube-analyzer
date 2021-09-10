try:
    from pandasgui import show
except:
    pass
import pandas as pd
import numpy as np
from textwrap import wrap
import re
import os

from data_extraction import *
import matplotlib.pyplot as plt
import seaborn as sns


# Build a DataFrame of stats for a list of videos or a playlist
def make_df(video_ids: List[str] = None, playlist_id: str = None):
    if (video_ids and playlist_id) or (not video_ids and not playlist_id):
        raise ValueError("You must specify one of video_ids or playlist_id")

    # Get playlist details
    if playlist_id:
        video_ids = get_playlist_videos(playlist_id)
        res = requests.get(BASE_URL + "playlists",
                           params={
                               "key": API_KEY,

                               "part": "id,snippet,contentDetails",
                               "id": playlist_id
                           })
        res.raise_for_status()
        data = res.json()
        playlist_info_raw = data['items'][0]['snippet']
        playlist_info = {'playlist_' + key: val for (key, val) in playlist_info_raw.items()}

    else:
        playlist_info = {}

    # Get video details
    items = get_video_details(video_ids)

    # Reshape and merge video and playlist details
    data_rows = []
    for item in items:
        snippet = item['snippet']
        statistics = item['statistics']
        contentDetails = item['contentDetails']
        data_rows.append({'id': item['id'], **snippet, **statistics, **contentDetails, **playlist_info})

    df = pd.DataFrame(data_rows)

    # Parse datetime
    def parse_duration(duration):
        parsed_duration = 0

        letters = ['D',
                   'H',
                   'M',
                   'S']
        values = [24 * 60 * 60,
                  60 * 60,
                  60,
                  1]

        for letter, value in zip(letters, values):
            match = re.match(rf'.*?([0-9]*){letter}', duration)
            if match:
                parsed_duration += value * int(match.group(1))

        return parsed_duration

    df['duration'] = df['duration'].apply(parse_duration)

    # Convert data types
    df = df.apply(pd.to_numeric, errors='ignore')

    # Calculate statistics
    df['likesPerDislike'] = df['likeCount'] / df['dislikeCount']
    df['likesPerView'] = df['likeCount'] / df['viewCount']
    df['dislikesPerView'] = df['dislikeCount'] / df['viewCount']
    df['link'] = "https://www.youtube.com/watch?v=" + df['id']
    df['positionInPlaylist'] = np.arange(len(df))

    # Move most interesting columns to front
    front_cols = ['link', 'title', 'description', 'viewCount', 'likeCount', 'dislikeCount',
                  'commentCount', 'duration', 'likesPerDislike', 'likesPerView', 'dislikesPerView']
    new_cols = front_cols + [c for c in df.columns if c not in front_cols]
    df = pd.DataFrame(df, columns=new_cols)

    return df


if __name__ == '__main__':
    #
    # # #############################
    # # Get details for playlists
    # all_channels = [
    #     # Brands
    #     'Apple',
    #     'Microsoft',
    #     'spacexchannel',
    #     # Informational
    #     'TEDtalksDirector',
    #     'TEDEducation',
    #     'Vsauce',
    #     'LinusTechTips',
    #     'Kurzgesagt',
    #     'keeroyz',
    #     # Commentary
    #     'h3h3Productions',
    #     'destiny',
    #     'PewDiePie',
    #     'MrBeast6000',
    #     'Chris Ray Gun',
    #     'Shoe0nHead',
    # ]
    #
    # failed = []
    # for channel in all_channels:
    #     try:
    #         playlist_id = get_channel_uploads_playlist(channel)
    #     except Exception as e:
    #         failed.append({'channel': channel, 'error': e})
    #
    # # #############################
    # # Search
    #
    query = "react tutorial"
    playlist_ids = get_search_results(query, type='playlist', max_results=5)

    # #############################
    # Analysis

    all_dfs = []
    for playlist_id in playlist_ids:
        df = make_df(playlist_id=playlist_id)
        # title = df.iloc[0].channelTitle
        # df.sort_values('dislikesPerView', ascending=False).to_csv(f'{title}.csv', index=False)
        all_dfs.append(df)

    full_df = pd.concat(all_dfs, axis=0)

    # Wrap the video titles into multiple lines for when they're put on plot labels
    full_df['title'] = full_df['title'].fillna('')
    for i, row in full_df.iterrows():
        title = row['title']
        full_df.at[i, 'title'] = '\n'.join(wrap(title, 30))

    ####################
    # Plotting

    fig, axes = plt.subplots(2, 2, figsize=(16, 8))
    # Plot the like ratio
    ax = sns.pointplot(x='positionInPlaylist', y=full_df['likeCount'] / full_df['dislikeCount'],
                       data=full_df, hue='playlist_title', ax=axes[0][0])
    ax.set_title('Like/Dislike Ratio')
    ax.set_ylabel("like/dislike Ratio")
    ax.set_xlabel("Video")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.legend(loc='upper right')

    # Plot the like count
    ax = sns.pointplot(x='positionInPlaylist', y=full_df['likeCount'],
                       data=full_df, hue='playlist_title', ax=axes[0][1],
                       )
    ax.set_title('Total Likes')
    ax.set_ylabel("Like Count")
    ax.set_xlabel("Video")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.legend(loc='upper right')

    # Plot the views per like
    ax = sns.pointplot(x='positionInPlaylist', y=full_df['likeCount'] / full_df['viewCount'],
                       data=full_df, hue='playlist_title', ax=axes[1][0])
    ax.set_title('Likes per View')
    ax.set_ylabel("Likes per View")
    ax.set_xlabel("Video")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.legend(loc='upper right')

    # Plot the duration
    ax = sns.pointplot(x='positionInPlaylist', y=full_df['duration'] / 60,
                       data=full_df, hue='playlist_title', ax=axes[1][1])
    ax.set_title('Duration (m)')
    ax.set_ylabel("Duration (m)")
    ax.set_xlabel("Video")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.legend(loc='upper right')

    fig.tight_layout(pad=1)
    plt.show()
