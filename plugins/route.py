import os
import re
import math
import logging
import secrets
import mimetypes
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from web import multi_clients, work_loads
from web.exceptions import FIleNotFound, InvalidHash
from web.custom_dl import ByteStreamer
from info import *

routes = web.RouteTableDef()

# Global cache defined properly at the module level
class_cache = {}

@routes.get("/favicon.ico")
async def favicon_route_handler(request):
    return web.FileResponse('web/favicon.ico')

# 🏡 मुख्य होम पेज
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("TechifyBots Web Server is Running Perfectly!")

# 🍿 EXACT SILENTXBOTZ PREMIUM VIDEO PLAYER (100% WORKING & NOT FOUND FIXED)
@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        secure_hash = ""
        
        # 📌 CRITICAL FIX: Alphanumeric String Tokens (Letters + Numbers dono) ko direct fetch karna
        # Isse BAADBAADviAAAmfnaVMU2xygYcnYuRYE jise tokens bina crash ke bypass honge
        clean_id = path.split("/")[0] if "/" in path else path
        
        secure_hash = request.rel_url.query.get("hash", "")

        # Multi-Client cached objects logic to dynamically extract file property layout names
        index = min(work_loads, key=work_loads.get)
        faster_client = multi_clients[index]
        
        global class_cache
        if faster_client in class_cache:
            tg_connect = class_cache[faster_client]
        else:
            tg_connect = ByteStreamer(faster_client)
            class_cache[faster_client] = tg_connect
            
        try:
            # Token context direct routing parameter setup
            file_id = await tg_connect.get_file_properties(clean_id)
            display_name = file_id.file_name
        except Exception:
            display_name = path.split("/")[-1].replace("_", " ").replace("-", " ").replace(".mkv", "").title()

        protocol = "https" if request.secure else "http"
        
        # 🚀 REAL TELEGRAM PIPELINE DATA BINDINGS (Bina load pade watch/download karne ke liye)
        download_url = f"{protocol}://{request.host}/{clean_id}"
        if secure_hash:
            download_url += f"?hash={secure_hash}"

        # 🎨 EXACT SCREENSHOT PURPLE PREMIUM DYNAMIC DESIGN TEMPLATE MODEL
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SilentXBotz | Premium Stream</title>
            <style>
                body {{ background-color: #0b0114; color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; text-align: center; padding: 15px; margin: 0; }}
                .container {{ max-width: 500px; margin: 20px auto; background: #140529; padding: 20px; border-radius: 16px; border: 1px solid #251145; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }}
                h2 {{ color: #b67dff; font-size: 19px; font-weight: 600; margin-bottom: 25px; letter-spacing: 0.5px; }}
                .video-wrapper {{ position: relative; width: 100%; border-radius: 12px; overflow: hidden; background: #000000; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }}
                video {{ width: 100%; display: block; outline: none; }}
                .meta-box {{ background: #1f0b3b; padding: 18px; border-radius: 12px; text-align: left; border: 1px solid #2c1452; }}
                .tag {{ background: #822eff; color: white; display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
                .title-text {{ font-size: 15px; font-weight: 500; line-height: 1.5; margin-bottom: 20px; color: #ecd9ff; word-wrap: break-word; }}
                .btn-group {{ display: flex; gap: 8px; margin-bottom: 14px; }}
                .btn {{ padding: 11px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; gap: 6px; font-size: 13.5px; transition: background 0.2s; }}
                .btn-download {{ background: #270e47; color: #d6b3ff; flex: 1.1; border: 1px solid #431f73; text-align: center; }}
                .btn-copy {{ background: #270e47; color: #d6b3ff; flex: 1.2; border: 1px solid #431f73; }}
                .btn-share {{ background: #270e47; color: #d6b3ff; flex: 1; border: 1px solid #431f73; }}
                .btn-external {{ background: linear-gradient(90deg, #7b31f5, #9c5cff); color: white; width: 100%; box-sizing: border-box; font-size: 14px; padding: 13px; margin-top: 5px; box-shadow: 0 4px 12px rgba(123, 49, 245, 0.3); }}
                .audio-warning {{ font-size: 12px; color: #cca3ff; margin-top: 15px; text-align: center; font-style: italic; opacity: 0.85; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Enjoy Premium Streaming Experience</h2>
                
                <div class="video-wrapper">
                    <video controls poster="https://ibb.co" preload="none">
                        <source src="{download_url}" type="video/mp4">
                        Your browser does not support HTML video play paths.
                    </video>
                </div>

                <div class="meta-box">
                    <div class="tag">▶️ HD STREAMING</div>
                    <div class="title-text">{display_name}</div>
                    
                    <div class="btn-group">
                        <a href="{download_url}" class="btn btn-download">📥 Download</a>
                        <button onclick="navigator.clipboard.writeText(window.location.href); alert('Streaming link copied to clipboard!');" class="btn btn-copy">📋 Copy Link</button>
                        <button onclick="window.open('https://telegram.me' + encodeURIComponent(window.location.href));" class="btn btn-share">🤝 Share</button>
                    </div>
                    
                    <!-- Exact Android Deep Linking intent model for MX / VLC Player routing mapping -->
                    <a href="intent://{download_url.replace('http://', '').replace('https://', '')}#Intent;package=com.mxtech.videoplayer.ad;S.title={display_name};end" class="btn btn-external">🚀 Open in External Player</a>
                    
                    <div class="audio-warning">⚠️ Browser Does Not Support EAC3 Audio. If No Sound, Please Use External Players.</div>
                </div>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html_content, content_type='text/html')
        
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

# 📥 बैकएंड MEDIA STREAMER
@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        
        # 📌 FIX: Pure alphanumeric matching strings extraction logic
        clean_id = path.split("/")[0] if "/" in path else path
        secure_hash = request.rel_url.query.get("hash", "")
        
        return await media_streamer(request, clean_id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except web.HTTPNotFound:
        raise
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logging.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

async def media_streamer(request: web.Request, clean_id: str, secure_hash: str):
    range_header = request.headers.get("Range", 0)
    
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]
    
    if MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    global class_cache
    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logging.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect
        
    file_id = await tg_connect.get_file_properties(clean_id)
    
    if secure_hash and file_id.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with Token {clean_id}")
        raise InvalidHash
    
    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    mime_type = file_id.mime_type
    file_name = file_id.file_name

    if mime_type:
        if not file_name:
            try:
                file_name = f"{secrets.token_hex(2)}.{mime_type.split('/')[-1]}"
            except (IndexError, AttributeError):
                file_name = f"{secrets.token_hex(2)}.unknown"
    else:
        if file_name:
            mime_type = mimetypes.guess_type(file_id.file_name)
        else:
            mime_type = "application/octet-stream"
            file_name = f"{secrets.token_hex(2)}.unknown"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Range, Content-Type",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges",
        },
    )
        
