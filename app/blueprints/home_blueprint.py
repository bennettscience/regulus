from datetime import datetime
from threading import currentThread
from typing import List

import requests

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user

from app.extensions import cache
from app.wrappers import restricted

home_bp = Blueprint("home_bp", __name__)


@home_bp.get("/")
def index():
    if current_user.is_anonymous:
        return render_template("auth/login.html")
    else:
        if request.headers.get("HX-Request"):
            return render_template("home/index-partial.html")
        else:
            return render_template("home/index.html")


@home_bp.get("/create")
@restricted
def create():
    from app.models import CourseType, Location
    from app.schemas import CourseTypeSchema, LocationSchema

    if request.headers.get("HX-Request"):
        template = "admin/forms/create-form-partial.html"
    else:
        template = "admin/forms/create-form-full.html"

    course_types = CourseType.query.all()
    locations = sorted(Location.query.all())

    content = {
        "course_types": CourseTypeSchema(many=True).dump(course_types),
        "locations": LocationSchema(many=True).dump(locations),
    }

    return render_template(template, **content)


@home_bp.route("/resource-query")
@cache.cached(timeout=3600)
def update():
    today = datetime.now()

    # Get the blog post and youtube video
    blog_post = get_blog_post()
    youtube_video = get_youtube_video()

    # This is kind of a mess, but it helps handle all cases. It can probably be done better.
    # Both calls come back successfully
    if not isinstance(blog_post, Exception) and not isinstance(
        youtube_video, Exception
    ):
        if (today - blog_post["published_at"]) < (
            today - youtube_video["published_at"]
        ):
            resource = blog_post
        else:
            resource = youtube_video
    else:
        if isinstance(blog_post, Exception) and isinstance(youtube_video, Exception):
            resource = {"message": "Something has gone terribly wrong"}
        elif not isinstance(blog_post, Exception) and isinstance(
            youtube_video, Exception
        ):
            resource = blog_post
        elif isinstance(blog_post, Exception) and not isinstance(
            youtube_video, Exception
        ):
            resource = youtube_video
        else:
            resource = {"message": "You should not have reached this spot."}

    return jsonify(**resource)


@cache.cached(timeout=3600, key_prefix="last_blog")
def get_blog_post():
    headers = {"Authorization": "Bearer " + current_app.config["BLOG_AUTH_TOKEN"]}

    try:
        response = requests.get(
            "https://blog.elkhart.k12.in.us/wp-json/wp/v2/posts?per_page=1&order=desc&_embed",
            headers=headers,
        ).json()[0]

        result = {
            "published_at": datetime.strptime(response["date"], "%Y-%m-%dT%H:%M:%S"),
            "link": f"{response['link']}?utm_source=chrome_extension",
            "thumbnail": response["_embedded"]["wp:featuredmedia"][0]["source_url"],
            "title": response["title"]["rendered"],
        }
    except Exception as e:
        result = e

    return result


@cache.cached(timeout=3600, key_prefix="last_youtube")
def get_youtube_video():

    token = current_app.config["YOUTUBE_AUTH_TOKEN"]
    # Set the referrer header
    headers = {"Referer": "https://events.elkhart.k12.in.us"}
    yt_request = requests.get(
        f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=UUgwJ38NKsSVTBW_yzw8n1eQ&sort=desc&maxResults=1&key={token}",  # noqa
        headers=headers,
    )
    try:
        response = yt_request.json()["items"][0]["snippet"]
        result = {
            "published_at": datetime.strptime(
                response["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
            ),
            "link": f"https://youtube.com/watch?v={response['resourceId']['videoId']}/?utm_source=chrome_extension",
            "thumbnail": response["thumbnails"]["standard"]["url"],
            "title": response["title"],
        }
    except Exception as e:
        result = e

    return result
