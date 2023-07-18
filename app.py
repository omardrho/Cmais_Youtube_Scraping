from urllib import request
import pandas as pd
from flask import Flask, jsonify
from googleapiclient.discovery import build
app = Flask(__name__)

#My static parameters
api_key = 'AIzaSyCAyePluw95z8diqa8AvravqVsY93DEHMk'
youtube = build('youtube', 'v3', developerKey=api_key)

part = 'snippet,statistics'
max_results = 5
# initial channel id
channel_id = 'UCXwDLMDV86ldKoFVc_g8P0g'

def get_videos_with_comments(channel_id, published_after=None):
    import pandas as pd

    data = []
    search_params = {
        'type': 'video',
        'part': 'id,snippet',
        'maxResults': max_results,
        'order': 'date',
        'channelId': channel_id
    }

    if published_after:
        search_params['publishedAfter'] = published_after

    response = youtube.search().list(**search_params).execute()
    video_ids = [item['id']['videoId'] for item in response['items']]

    for video_id in video_ids:
        video_data = {
            'Title': None,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'Description': None,
            'View Count': None,
            'Published At': None,
            'Comments': None  # Initialize the comments field to None
        }

        video_response = youtube.videos().list(part=part, id=video_id).execute()
        if 'items' in video_response and len(video_response['items']) > 0:
            video_item = video_response['items'][0]['snippet']
            video_data['Title'] = video_item['title']
            video_data['Description'] = video_item['description']
            video_data['View Count'] = video_response['items'][0]['statistics']['viewCount']
            video_data['Published At'] = video_item['publishedAt']


            comments_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                textFormat='plainText',
                maxResults=max_results
            ).execute()

            if 'items' in comments_response and len(comments_response['items']) > 0:
                comments = [comment['snippet']['topLevelComment']['snippet']['textDisplay']
                            for comment in comments_response['items']]
                video_data['Comments'] = comments

        data.append(video_data)

    if len(data) > 0:
        relative_last = data[0]['Published At']
    else:
        relative_last = None

    df = pd.DataFrame(data)
    return df, relative_last
def get_channel_id(channel_name):
    search_response = youtube.search().list(
        q=channel_name,
        part='id',
        type='channel',
        maxResults=1
    ).execute()


    channel_id = search_response['items'][0]['id']['channelId']

    return channel_id

# def extract_video_id(video_url):
#     video_id = None
#     if 'https://www.youtube.com/watch?v=' in video_url:
#         video_id = video_url.split('v=')[-1]
#         if '&' in video_id
#             video_id = video_id.split('&')[0]
#         return video_id
#     else:
#         return "Invalid URL"


# def channel_video_comments(url):
#     id_video = extract_video_id(url)
#     response = youtube.commentThreads().list(
#         part='snippet',
#         videoId=id_video,
#         maxResults=55
#     ).execute()
#
#     comments = []
#     for item in response['items']:
#         comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
#         comments.append(comment)
#
#     return comments



@app.route('/videos/<channel_name>', methods=['GET'])
def get_videos_route(channel_name):
    channel_id = get_channel_id(channel_name)
    df, relative_last = get_videos_with_comments(channel_id)
    return jsonify(df.to_dict(orient='records')), 200

# @app.route('/videos/after', methods=['GET'])
# def get_videos_after_route():
#     t = request.args.get('publishedAfter')
#     df, relative_last = get_videos(channel_id, published_after=t)
#     return jsonify(df.to_dict(orient='records')), 200

# @app.route('/videos/comments/<path:url>', methods=['GET'])
# def get_video_comments(url):
#     comments=channel_video_comments(url)
#     return comments
@app.route('/')
def index():
    return "CMAIS API, use /videos/<channel_name> to get videos from a channel"


if __name__ == '__main__':
    app.run()


