#!/usr/bin/env python3
"""Five-minute loopback observer for Google's documented IFrame API sample."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
import json,os,time
folder=Path('/tmp/asus-youtube-workload');folder.mkdir(mode=0o700)
state={'pid':os.getpid(),'status':'running','events':[],'latest':None}
HTML=b'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ASUS YouTube workload</title><style>body{font:24px sans-serif;margin:24px;background:#f6f3ed;color:#143c36}iframe{max-width:100%}button{font:inherit;padding:20px}pre{font:17px monospace;white-space:pre-wrap}</style><h1>YouTube playback check</h1><p>Google's documented player sample, muted.</p><div id="player"></div><p><button id="play">Play sample</button></p><pre id="status">Loading player...</pre><script>
let player,finished=false;function report(kind,extra={}){let d={kind,time:Date.now(),...extra};if(player&&player.getPlayerState){d.playerState=player.getPlayerState();d.playbackTime=player.getCurrentTime();d.duration=player.getDuration();d.loadedFraction=player.getVideoLoadedFraction();d.muted=player.isMuted();d.quality=player.getPlaybackQuality()}document.getElementById('status').textContent=JSON.stringify(d,null,2);fetch('/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).catch(()=>{})}
window.onYouTubeIframeAPIReady=()=>{player=new YT.Player('player',{width:640,height:360,videoId:'M7lc1UVf-VE',playerVars:{playsinline:1,origin:location.origin,rel:0},events:{onReady:()=>{player.mute();document.getElementById('play').focus();report('ready')},onStateChange:e=>report('player-state',{state:e.data}),onError:e=>report('player-error',{error:e.data}),onAutoplayBlocked:()=>report('autoplay-blocked')}})};
document.getElementById('play').onclick=e=>{if(e.isTrusted&&player){player.mute();player.playVideo();report('trusted-play')}};setInterval(()=>{if(player&&player.getCurrentTime){report('progress');if(!finished&&player.getCurrentTime()>=15){finished=true;player.pauseVideo();report('complete')}}},1000);report('loaded');const s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';s.onerror=()=>report('api-load-error');document.head.appendChild(s);
</script>'''
def save():
    temporary=folder/'state.new';temporary.write_text(json.dumps(state)+'\n');temporary.replace(folder/'state.json')
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/':body,kind=HTML,'text/html; charset=utf-8'
        elif self.path=='/state':body,kind=json.dumps(state).encode(),'application/json'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0))
        if self.path!='/state' or not 0<n<8192:self.send_error(400);return
        event=json.loads(self.rfile.read(n));state['latest']=event;state['events'].append(event);state['events']=state['events'][-120:];save();self.send_response(204);self.end_headers()
server=HTTPServer(('127.0.0.1',8086),Handler);server.timeout=.5;save();deadline=time.monotonic()+300
try:
    while time.monotonic()<deadline and not (folder/'STOP').exists():server.handle_request()
finally:server.server_close();state['status']='stopped';save()
