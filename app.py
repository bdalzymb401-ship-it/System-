from flask import Flask, request, jsonify
import yt_dlp
import os
import re
import hashlib

app = Flask(__name__)

def get_video_id(url):
    if 'youtube.com' in url or 'youtu.be' in url:
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
    return hashlib.md5(url.encode()).hexdigest()[:12]

# ══════════════════════════════════════════════════
# ✅ نقطة جلب رابط الصوت المباشر
# ══════════════════════════════════════════════════
@app.route('/api/v1/stream', methods=['GET'])
def get_stream_url():
    video_id = request.args.get('id', '')
    url      = request.args.get('url', '')

    if not video_id and not url:
        return jsonify({"status": "error", "message": "No ID or URL"}), 400

    if not url:
        url = f"https://www.youtube.com/watch?v={video_id}"

    # 🛠️ تم تعديل الإعدادات هنا لتقرأ ملف الكوكيز وتتخطى حظر يوتيوب
    ydl_opts = {
        'quiet':         True,
        'no_warnings':   True,
        'format':        'bestaudio[ext=m4a]/bestaudio/best',
        'skip_download': True,
        'cookiefile':    'cookies.txt',  # <-- تم إضافة هذا السطر بنجاح 🎉
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            title    = info.get('title',    'Unknown')
            artist   = info.get('uploader', info.get('channel', 'Unknown'))
            duration = info.get('duration', 0) or 0

            stream_url = info.get('url', '')

            if not stream_url:
                for fmt in info.get('formats', []):
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        stream_url = fmt.get('url', '')
                        break

            thumbnail  = ''
            thumbnails = info.get('thumbnails', [])
            if thumbnails:
                thumbnail = thumbnails[-1].get('url', '')
            if not thumbnail:
                thumbnail = f"https://i.ytimg.com/vi/{info.get('id', video_id)}/hqdefault.jpg"

            mins, secs = divmod(int(duration), 60)

            return jsonify({
                "status":       "success",
                "stream_url":   stream_url,
                "title":        title,
                "artist":       artist,
                "duration":     duration,
                "duration_str": f"{mins}:{secs:02d}",
                "thumbnail":    thumbnail,
                "video_id":     info.get('id', video_id)
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ══════════════════════════════════════════════════
# ✅ فحص الصحة
# ══════════════════════════════════════════════════
@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "server": "BAR9E Music Stream Server"
    })

# ══════════════════════════════════════════════════
# ✅ التشغيل
# ══════════════════════════════════════════════════
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8765))
    print("=" * 60)
    print("  🎵 BAR9E Music Stream Server")
    print(f"  📡 Running on port: {port}")
    print("  🔗 Stream API: /api/v1/stream?id=VIDEO_ID")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
