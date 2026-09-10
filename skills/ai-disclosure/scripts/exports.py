"""Portable HTML documents; strict semantic markup and byte-preserving raster embeds."""
import base64
import html
from html.parser import HTMLParser
from urllib.parse import urlsplit

TAGS = set('article section main div aside header footer h1 h2 h3 h4 h5 h6 span strong em b i u s p br figure figcaption img blockquote ul ol li table tbody thead tfoot tr td th a code pre time hr dl dt dd'.split())
VOID = {'br', 'img', 'hr'}


def image_uri(payload):
    if len(payload) > 20 * 1024 * 1024:
        raise ValueError('Portable export supports raster images up to 20 MiB each')
    if payload.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'image/png'
    elif payload.startswith(b'\xff\xd8\xff'):
        mime = 'image/jpeg'
    elif payload.startswith((b'GIF87a', b'GIF89a')):
        mime = 'image/gif'
    elif payload[:4] == b'RIFF' and payload[8:12] == b'WEBP':
        mime = 'image/webp'
    else:
        raise ValueError('Portable export supports PNG, JPEG, GIF and WebP; other assets need a dedicated export')
    return 'data:' + mime + ';base64,' + base64.b64encode(payload).decode('ascii')


class DocumentExport(HTMLParser):
    def __init__(self, loader):
        super().__init__(convert_charrefs=True)
        self.loader, self.parts, self.stack = loader, [], []

    def handle_starttag(self, tag, attrs):
        if tag not in TAGS:
            raise ValueError('Unsupported element in portable export: ' + tag)
        attrs = dict(attrs)
        if any(key in attrs for key in ('hidden', 'inert', 'style')) or attrs.get('aria-hidden') == 'true':
            raise ValueError('Export needs explicit visible publication markup without hidden content or inline styles')
        output = {}
        if attrs.get('id'):
            output['id'] = attrs['id']
        classes = set(attrs.get('class', '').split()) & {'aid-notice', 'aid-media'}
        if classes:
            output['class'] = ' '.join(sorted(classes))
        if tag == 'img':
            if not attrs.get('src') or 'srcset' in attrs or 'alt' not in attrs:
                raise ValueError('Export images need explicit src and alt, without responsive alternatives')
            output['src'] = image_uri(self.loader(attrs['src']))
            output['alt'] = attrs['alt'] or ''
        if tag == 'a' and attrs.get('href'):
            url = attrs['href']
            if not url.startswith('#') and urlsplit(url).scheme.lower() not in {'http', 'https', 'mailto'}:
                raise ValueError('Export links need absolute HTTP(S)/mailto URLs or document anchors')
            output['href'] = url
        if tag in {'td', 'th'}:
            for key in ('colspan', 'rowspan'):
                if key in attrs:
                    if not attrs[key] or not attrs[key].isdigit() or not 1 <= int(attrs[key]) <= 100:
                        raise ValueError('Invalid table span')
                    output[key] = attrs[key]
            if attrs.get('scope') in {'row', 'col', 'rowgroup', 'colgroup'}:
                output['scope'] = attrs['scope']
        self.parts.append('<' + tag + ''.join(' ' + k + '="' + html.escape(v, quote=True) + '"' for k, v in output.items()) + '>')
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID or not self.stack or self.stack.pop() != tag:
            raise ValueError('Export requires properly nested, explicitly closed HTML')
        self.parts.append('</' + tag + '>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        self.parts.append(html.escape(data))

    def handle_decl(self, decl):
        raise ValueError('Document declarations are not allowed inside an exported component')


def render_document(fragment, loader, title, language):
    if not isinstance(title, str) or not title.strip():
        raise ValueError('Export needs a document title')
    if not isinstance(language, str) or not language or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-' for c in language):
        raise ValueError('Export needs an explicit language tag')
    parser = DocumentExport(loader)
    parser.feed(fragment)
    parser.close()
    if parser.stack:
        raise ValueError('Export contains unclosed elements')
    css = '''body{max-width:48rem;margin:2rem auto;padding:0 1rem;font:1rem/1.6 system-ui,sans-serif;color:#172b24;background:white}img{max-width:100%;height:auto}figure{margin:1rem 0}.aid-media{position:relative}.aid-media>.aid-notice{position:absolute;top:.6rem;left:.6rem}.aid-notice{display:table;font:500 .875rem/1.5 system-ui,sans-serif;color:#183d33;background:#f2faf6;border:1px solid #55776c;border-radius:.25rem;padding:.2rem .5rem}table{border-collapse:collapse}td,th{padding:.4rem;border:1px solid #888}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{overflow-wrap:anywhere}@media print{body{margin:0;max-width:none}.aid-notice{color:black;background:white;print-color-adjust:exact}figure{break-inside:avoid}}'''
    return ('<!doctype html><html lang="' + html.escape(language, quote=True) + '"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            '<title>' + html.escape(title) + '</title><style>' + css + '</style></head><body>'
            + ''.join(parser.parts) + '</body></html>')
