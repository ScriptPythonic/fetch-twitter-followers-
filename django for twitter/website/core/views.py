"""
Twitter Followers Viewer Application
Created By: ScriptPythonic
"""

import requests
import base64
import tweepy
from decouple import config
from django.shortcuts import render, redirect
from django.http import HttpResponse
import json
from typing import List, Dict, Any

# Twitter API credentials
consumer_key = config('CONSUMER_KEY')
consumer_secret = config('CONSUMER_SECRET')
access_token = config('ACCESS_TOKEN')
access_token_secret = config('ACCESS_TOKEN_SECRET')

def followers_view(request) -> HttpResponse:
    """
    View to display the followers count for specified Twitter usernames.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the rendered template.
    """
    if request.method == 'GET':
        try:
            with open('data.json', 'r') as json_file:
                usernames: List[str] = json.load(json_file)
        except FileNotFoundError:
            return HttpResponse('No data found in data.json')

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        user_data: List[Dict[str, Any]] = []
        error_message: str = ''

        try:
            for username in usernames:
                user = api.get_user(screen_name=username)
                follower_count: int = user.followers_count
                profile_image_url: str = user.profile_image_url_https
                user_data.append({'username': username, 'follower_count': follower_count, 'profile_image_url': profile_image_url})
        except Exception as e:
            error_message = f"Error: {e}"

        user_data.sort(key=lambda x: x['follower_count'], reverse=True)

        return render(request, 'followers.html', {'user_data': user_data, 'error_message': error_message})

    return render(request, 'followers.html')

def index(request) -> HttpResponse:
    """
    View to handle the submission of a Twitter username and retrieve its followers.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the rendered template or redirection.
    """
    if request.method == 'POST':
        username: str = request.POST.get('username')

        if not username:
            return HttpResponse('Username is required')

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        try:
            user = api.get_user(screen_name=username)
            user_id: int = user.id
        except Exception as e:
            print(f"Error: {e}")
            return HttpResponse('Failed to retrieve user ID')

        token_url: str = 'https://api.twitter.com/oauth2/token'
        credentials: str = f"{consumer_key}:{consumer_secret}"
        encoded_credentials: str = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }
        data = {
            'grant_type': 'client_credentials',
        }

        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            bearer_token: str = response.json().get('access_token')
        else:
            return HttpResponse('Failed to obtain bearer token')

        headers = {
            'Authorization': f'Bearer {bearer_token}',
        }
        url: str = f'https://api.twitter.com/2/users/{user_id}/followers'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data: Dict[str, Any] = response.json()
            
            if 'data' in data and isinstance(data['data'], list):
                followers: List[str] = [follower['username'] for follower in data['data']]
            else:
                followers = []

            total_followers: int = data['meta'].get('total_count', 0)
            
            with open('data.json', 'w') as json_file:
                json.dump(followers, json_file)

            return redirect('followers_view')
        else:
            return HttpResponse(f"Error: {response.status_code}")

    return render(request, 'home.html')
