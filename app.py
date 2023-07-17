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

def get_videos(channel_id, published_after=None):
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

    response = youtube.videos().list(part=part, id=','.join(video_ids)).execute()

    for item in sorted(response['items'], key=lambda x: x['snippet']['publishedAt'], reverse=True):
        video_data = {
            'Title': item['snippet']['title'],
            'url': f"https://www.youtube.com/watch?v={item['id']}",
            'Description': item['snippet']['description'],
            'View Count': item['statistics']['viewCount'],
            # 'Likes': item['statistics']['likeCount'],  # Not all videos have likes/dislikes
            'Published At': item['snippet']['publishedAt'],
            # More metadata can be added
        }
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

def channel_video_comments(video_id):
    response = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        maxResults=55
    ).execute()

    comments = []
    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
        comments.append(comment)

    return comments

@app.route('/videos/<channel_name>', methods=['GET'])
def get_videos_route(channel_name):
    channel_id = get_channel_id(channel_name)
    df, relative_last = get_videos(channel_id)
    return jsonify(df.to_dict(orient='records')), 200


@app.route('/videos/after', methods=['GET'])
def get_videos_after_route():
    t = request.args.get('publishedAfter')
    df, relative_last = get_videos(channel_id, published_after=t)
    return jsonify(df.to_dict(orient='records')), 200

@app.route('/video/comments/<video_id>', methods=['GET'])
def get_video_comments(video_id):
    comments=channel_video_comments(video_id)
    return jsonify(comments), 200

#Update
app.route('/')
def index():
    return "CMAIS API, use /videos/<channel_name> to get videos from a channel, /videos/after?publishedAfter=2020-01-01T00:00:00Z to get videos after a date, /video/comments/<video_id> to get comments from a video"

if __name__ == '__main__':
    app.run()
