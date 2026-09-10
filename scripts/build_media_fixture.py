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

# Two actual CMS-style renders plus a rejected update, served by the browser fixture.
component='<article data-ai-content="dynamic"><h2>Published item</h2><!-- ai-disclosure --><p>First version.</p></article>'
def component_facts(source):
    row=p.fragment_inventory(root,source)[1]['records'][0]
    return {'version':1,'role':'publisher','items':[{'id':row['id'],'revision':row['revision'],
        'kind':'text','origin':'ai_generated','applicable':True,'public_interest':True,
        'evidence':'Fixture publishing transaction'}]}
first_facts=component_facts(component)
first=p.render_fragment(root,component,first_facts)
updated=component.replace('First version.','Second version.')
second=p.render_fragment(root,updated,component_facts(updated))
rejected=p.render_fragment(root,updated.replace('Second version.','Unrecorded version.'),first_facts)
output=pathlib.Path('.local-preview/media-output')
(output/'dynamic.json').write_text(json.dumps({'html':second['html']}))
(output/'rejected.json').write_text(json.dumps({'html':rejected['html']}))
(output/'dynamic.html').write_text('<html><head><title>Dynamic publishing fixture</title>'
    '<link rel="stylesheet" href="ai-disclosure.css"><script defer src="dynamic.js"></script></head><body>'
    '<div id="publication">'+first['html']+'</div>'
    '<button data-update="dynamic.json">Publish recorded update</button>'
    '<button data-update="rejected.json">Try unrecorded update</button><p role="status"></p></body></html>')
(output/'dynamic.js').write_text('''document.querySelectorAll('[data-update]').forEach(button=>{
  button.addEventListener('click',async()=>{
    const response=await fetch(button.dataset.update);
    const result=await response.json();
    if(result.html===null){document.querySelector('[role=status]').textContent='Update held: evidence is stale.';return;}
    document.querySelector('#publication').innerHTML=result.html;
    document.querySelector('[role=status]').textContent='Published recorded update.';
  });
});''')
