from flask import Flask, render_template, request, send_file
import instaloader
import os
import requests
from datetime import datetime

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# 🔑 Global loader with sessionid
# Yahan apna Instagram sessionid paste karo (DevTools → Cookies → sessionid)
SESSIONID = "YAHAN_APNA_SESSIONID_PASTE_KARO"
loader = instaloader.Instaloader()
loader.context._session.cookies.set("sessionid", SESSIONID)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/preview', methods=['POST'])
def preview():
    link = request.form['link']

    try:
        if "instagram.com/p/" in link or "instagram.com/reel/" in link:
            shortcode = link.strip().split("/")[-2]
            post = instaloader.Post.from_shortcode(loader.context, shortcode)

            is_video = post.is_video
            media_url = post.video_url if is_video else post.url
            caption = post.caption or "No caption available."

            # Save caption
            caption_filename = os.path.join(DOWNLOAD_FOLDER, "caption.txt")
            with open(caption_filename, "w", encoding="utf-8") as f:
                f.write(caption)

            return render_template("preview.html", link=link, media_url=media_url, is_video=is_video, caption=caption)
        else:
            return "Invalid Instagram link!"
    except Exception as e:
        return f"Failed: {str(e)}"

@app.route('/download', methods=['POST'])
def download():
    link = request.form['link']
    resolution = request.form.get('resolution', 'high')

    try:
        if "instagram.com/p/" in link or "instagram.com/reel/" in link:
            shortcode = link.strip().split("/")[-2]
            post = instaloader.Post.from_shortcode(loader.context, shortcode)

            media_url = post.video_url if post.is_video else post.url
            file_ext = ".mp4" if post.is_video else ".jpg"
            local_filename = os.path.join(DOWNLOAD_FOLDER, f"insta_download{file_ext}")

            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(media_url, stream=True, headers=headers)
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Save download history
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("download_history.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"{now} — {link} — {resolution} resolution — {'Video' if post.is_video else 'Image'} — Saved\n")

            return send_file(local_filename, as_attachment=True)
        else:
            return "Invalid Instagram link!"
    except Exception as e:
        return f"Failed: {str(e)}"

@app.route('/download_caption')
def download_caption():
    caption_path = os.path.join(DOWNLOAD_FOLDER, "caption.txt")
    return send_file(caption_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
