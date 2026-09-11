import math
from pyrogram.file_id import FileId

from aiohttp import web
from web import multi_clients, work_loads
from web.custom_dl import ByteStreamer


routes = web.RouteTableDef()

# Reuse ByteStreamer objects
class_cache = {}


@routes.get("/favicon.ico")
async def favicon_route_handler(request):
    return web.FileResponse("web/favicon.ico")


# Home page
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.Response(
        text="TechifyBots Web Server is Running Perfectly!",
        content_type="text/plain"
    )


# Get/reuse Telegram streamer
async def get_streamer():
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    global class_cache

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
    else:
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    return tg_connect, index


# Premium video player page
@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):

    try:
        path = request.match_info["path"]
        clean_id = path.split("/")[-1]

        secure_hash = request.rel_url.query.get("hash", "")

        # Try getting file name from database
        try:
            from database.ia_filterdb import get_file_details

            file_info = await get_file_details(clean_id)

            if file_info:
                display_name = file_info.file_name
            else:
                display_name = "Premium Video Asset"

        except Exception:
            display_name = (
                path.split("/")[-1]
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )

        protocol = "https" if request.secure else "http"

        download_url = f"{protocol}://{request.host}/{clean_id}"

        if secure_hash:
            download_url += f"?hash={secure_hash}"

        html_content = f"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>SilentXBotz | Premium Streaming</title>

<link
rel="stylesheet"
href="https://cdn.plyr.io/3.7.8/plyr.css"
/>

<style>

body {{
    background-color: #0b0114;
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
    padding: 15px;
    margin: 0;
}}

.container {{
    max-width: 500px;
    margin: 20px auto;
    background: #140529;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #251145;
}}

h2 {{
    color: #b67dff;
    font-size: 28px;
    margin-bottom: 25px;
}}

.video-wrapper {{
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
    background: black;
    margin-bottom: 20px;
}}

.meta-box {{
    background: #1f0b3b;
    padding: 18px;
    border-radius: 12px;
    text-align: left;
    border: 1px solid #2c1452;
}}

.tag {{
    background: #822eff;
    color: white;
    display: inline-block;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 15px;
}}

.title-text {{
    font-size: 18px;
    font-weight: bold;
    line-height: 1.5;
    margin-bottom: 20px;
    word-wrap: break-word;
}}

.btn-group {{
    display: flex;
    gap: 8px;
    margin-bottom: 14px;
}}

.btn {{
    flex: 1;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #431f73;
    background: #270e47;
    color: #d6b3ff;
    font-weight: bold;
    text-decoration: none;
    cursor: pointer;
}}

.btn-external {{
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 14px;
    border-radius: 8px;
    background: linear-gradient(
        90deg,
        #7b31f5,
        #9c5cff
    );
    color: white;
    text-align: center;
    text-decoration: none;
    font-weight: bold;
}}

.audio-warning {{
    font-size: 13px;
    color: #cca3ff;
    margin-top: 18px;
    text-align: center;
}}

video {{
    width: 100%;
    max-height: 500px;
}}

</style>

</head>

<body>

<div class="container">

<h2>Enjoy Premium Streaming Experience</h2>

<div class="video-wrapper">

<video
id="player"
playsinline
controls
preload="metadata"
>

<source src="{download_url}">

Your browser does not support video playback.

</video>

</div>


<div class="meta-box">

<div class="tag">
▶️ HD STREAMING
</div>

<div class="title-text">
{display_name}
</div>


<div class="btn-group">

<a
href="{download_url}"
class="btn"
download
>
📥 Download
</a>


<button
class="btn"
onclick="
navigator.clipboard.writeText(window.location.href);
alert('Streaming link copied!');
"
>
📋 Copy Link
</button>


<button
class="btn"
onclick="
navigator.share
?
navigator.share({{
title: document.title,
url: window.location.href
}})
:
window.open(
'https://t.me/share/url?url='
+ encodeURIComponent(window.location.href)
);
"
>
🤝 Share
</button>

</div>


<a
href="intent://{download_url.replace('http://', '').replace('https://', '')}#Intent;package=com.mxtech.videoplayer.ad;end"
class="btn-external"
>
🚀 Open in External Player
</a>


<div class="audio-warning">

⚠️ Some MKV files or EAC3 audio may not be supported by browsers.
If video/audio does not play, use an external player.

</div>

</div>

</div>


<script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>

<script>

document.addEventListener(
"DOMContentLoaded",
function () {{

    const video =
        document.getElementById("player");

    if (video && typeof Plyr !== "undefined") {{

        new Plyr(video, {{
            controls: [
                "play-large",
                "play",
                "progress",
                "current-time",
                "duration",
                "mute",
                "volume",
                "fullscreen"
            ]
        }});

    }}

}}
);

</script>

</body>

</html>
"""

        return web.Response(
            text=html_content,
            content_type="text/html"
        )

    except Exception as e:

        raise web.HTTPInternalServerError(
            text=str(e)
        )


# Media streaming route
@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):

    try:
        path = request.match_info["path"]
        clean_id = path.split("/")[-1]

        tg_connect, index = await get_streamer()

        # Decode Telegram File ID
        try:
            file_id = FileId.decode(clean_id)

        except Exception:
            # Fallback for numeric message ID
            try:
                message_id = int(clean_id)

                file_id = await tg_connect.get_file_properties(
                    message_id
                )

            except Exception:
                raise web.HTTPBadRequest(
                    text="Invalid file ID"
                )

        # Get file information
        try:
            file_info = await tg_connect.client.get_file(
                clean_id
            )

            file_size = file_info.file_size

            file_name = (
                file_info.file_path.split("/")[-1]
                if file_info.file_path
                else "video"
            )

        except Exception:
            raise web.HTTPBadRequest(
                text="Unable to get file information"
            )

        range_header = request.headers.get("Range")

        # Handle range request
        if range_header:

            byte_range = (
                range_header
                .replace("bytes=", "")
                .split("-")
            )

            from_bytes = int(byte_range[0])

            if len(byte_range) > 1 and byte_range[1]:
                until_bytes = int(byte_range[1])
            else:
                until_bytes = file_size - 1

        else:

            from_bytes = 0
            until_bytes = file_size - 1

        until_bytes = min(
            until_bytes,
            file_size - 1
        )

        # Chunk size: 1 MB
        chunk_size = 1024 * 1024

        offset = (
            from_bytes
            - (from_bytes % chunk_size)
        )

        first_part_cut = (
            from_bytes - offset
        )

        last_part_cut = (
            until_bytes % chunk_size
        ) + 1

        req_length = (
            until_bytes
            - from_bytes
            + 1
        )

        part_count = math.ceil(
            (until_bytes + 1)
            / chunk_size
        ) - math.floor(
            offset / chunk_size
        )

        # Stream file from Telegram
        body = tg_connect.yield_file(
            file_id,
            index,
            offset,
            first_part_cut,
            last_part_cut,
            part_count,
            chunk_size
        )

        mime_type = (
            "video/mp4"
            if file_name.lower().endswith(".mp4")
            else "application/octet-stream"
        )

        headers = {
            "Content-Type": mime_type,
            "Content-Length": str(req_length),
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
            "Content-Disposition":
                f'inline; filename="{file_name}"'
        }

        if range_header:
            headers["Content-Range"] = (
                f"bytes {from_bytes}-"
                f"{until_bytes}/{file_size}"
            )

        response = web.StreamResponse(
            status=206 if range_header else 200,
            headers=headers
        )

        await response.prepare(request)

        async for chunk in body:
            await response.write(chunk)

        await response.write_eof()

        return response

    except web.HTTPException:
        raise

    except Exception as e:
        raise web.HTTPInternalServerError(
            text=str(e)
)
