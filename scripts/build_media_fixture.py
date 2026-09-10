"""Silent audio fixtures test playback mechanics, never legal disclosure wording."""
import sys, pathlib, wave, json
sys.path.insert(0, str(pathlib.Path.cwd() / 'skills/ai-disclosure/scripts'))
import importlib.util
spec=importlib.util.spec_from_file_location('publisher', 'skills/ai-disclosure/scripts/site.py')
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
root=pathlib.Path('.local-preview/media-input'); root.mkdir(parents=True,exist_ok=True)
for name,seconds in [('notice',0.5),('recording',4)]:
 with wave.open(str(root / (name+'.wav')),'wb') as w:
  w.setparams((1,2,8000,0,'NONE','not compressed')); w.writeframes(b'\0\0'*int(8000*seconds))
(root/'index.html').write_text('<html><head><title>Playback mechanics test</title></head><body><figure class="aid-media" data-ai-content="recording"><!-- ai-disclosure --><audio src="recording.wav" data-ai-notice-src="notice.wav"></audio></figure></body></html>')
r=p.inventory(root)[1]['records'][0]
f=pathlib.Path('.local-preview/media-facts.json'); f.write_text(json.dumps({'version':1,'role':'publisher','items':[{'id':'recording','revision':r['revision'],'kind':'audio','origin':'ai_generated','applicable':True,'deepfake':True,'evidence':'Synthetic fixture: silence tests playback mechanics only'}]}))
print(p.build(root,f,pathlib.Path('.local-preview/media-output'))['ready_to_render'])
