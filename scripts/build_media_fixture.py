"""Silent audio fixtures test playback mechanics, never legal disclosure wording."""
import sys, pathlib, wave, json, shutil
sys.path.insert(0, str(pathlib.Path.cwd() / 'skills/ai-disclosure/scripts'))
import importlib.util
spec=importlib.util.spec_from_file_location('publisher', 'skills/ai-disclosure/scripts/site.py')
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
root=pathlib.Path('.local-preview/media-input'); root.mkdir(parents=True,exist_ok=True)
for name,seconds in [('notice',0.5),('recording',4)]:
 with wave.open(str(root / (name+'.wav')),'wb') as w:
  w.setparams((1,2,8000,0,'NONE','not compressed')); w.writeframes(b'\0\0'*int(8000*seconds))
(root/'captions.vtt').write_text('WEBVTT\n\n00:00.000 --> 00:04.000\nTest caption text\n')
shutil.copyfile('tests/fixtures/blue.webm',root/'blue.webm')
(root/'index.html').write_text('<html><head><title>Playback mechanics test</title></head><body><figure class="aid-media" data-ai-content="recording"><!-- ai-disclosure --><audio src="recording.wav" data-ai-notice-src="notice.wav"><track kind="captions" src="captions.vtt" srclang="en" label="English" default></audio></figure></body></html>')
(root/'chat.html').write_text('<html><head><title>Interaction notice mechanics test</title></head><body>'
    '<section class="aid-chat" data-ai-content="chat"><h1>AI interaction fixture</h1><!-- ai-disclosure -->'
    '<div role="log" style="min-height:1200px">Test conversation; no model is connected.</div>'
    '<form id="composer"><label>Message<textarea></textarea></label><button type="button">Send test message</button></form>'
    '</section></body></html>')
(root/'video.html').write_text('<html><head><title>Video mechanics test</title></head><body>'
    '<figure class="aid-media" data-ai-content="video"><!-- ai-disclosure -->'
    '<video src="blue.webm"><track kind="captions" src="captions.vtt" srclang="en" label="English" default></video>'
    '</figure></body></html>')
items=[]
for r in p.inventory(root)[1]['records']:
    facts={'id':r['id'],'revision':r['revision'],'origin':'ai_generated','applicable':True,
           'evidence':'Synthetic fixture tests rendering and playback mechanics only'}
    facts.update({'kind':'chatbot','direct_ai_interaction':True} if r['id']=='chat' else {'kind':'audio','deepfake':True})
    if r['id']=='video': facts.update({'kind':'video','audio_deepfake':False})
    items.append(facts)
f=pathlib.Path('.local-preview/media-facts.json')
f.write_text(json.dumps({'version':1,'role':'publisher','items':items}))
print(p.build(root,f,pathlib.Path('.local-preview/media-output'))['ready_to_render'])
