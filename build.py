"""Regenerate the buildless portfolio from the supplied Word document and artwork."""
from pathlib import Path
import zipfile, xml.etree.ElementTree as ET, re, html, json, shutil, base64
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'Portfolio Website'
OUT=ROOT/'portfolio'
ASSETS=OUT/'assets'
RESUME='daisy-mahadevan-resume-2026.pdf'
resume_source=SRC/'Daisy Resume'/'Daisy Mahadevan_Resume 2026.pdf'
if resume_source.is_file():
    shutil.copy2(resume_source,ASSETS/RESUME)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(SRC/'Website Content/Portfolio Website 2026.docx') as z:
    rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('word/_rels/document.xml.rels'))}
    doc=ET.fromstring(z.read('word/document.xml'))

def text_of(node):
    return ''.join(n.text or '' if n.tag.endswith('}t') else '\n' if n.tag.endswith('}br') else '' for n in node.iter())
paras=[text_of(p).strip() for p in doc.findall('.//w:body/w:p',NS)]
bullet_lines={line.strip() for p in doc.findall('.//w:body/w:p',NS) if p.find('w:pPr/w:numPr',NS) is not None for line in text_of(p).splitlines()}
lines=[line.strip() for p in paras for line in p.splitlines() if line.strip()]
links={text_of(h):rels[h.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']] for h in doc.findall('.//w:hyperlink',NS)}
(OUT/'content-links.json').write_text(json.dumps(links,indent=2))
e=lambda s:html.escape(str(s),quote=True)
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
asset_map={}
# Copy original PNG bytes: preserve transparency, resolution and future source updates.
for folder in ['Hero Image','Claude Design System','Fincent Branding','Fincent Webpages','Swym Branding','Website Audit']:
    source_folder=ROOT/folder if (ROOT/folder).is_dir() else SRC/folder
    for p in sorted(source_folder.glob('*.png')):
        name=slug(folder+' '+p.stem)+'.png'
        target=ASSETS/name
        shutil.copy2(p,target)
        with Image.open(target) as im:
            size=im.size
            if name in ('fincent-webpages-fincent-lp-2-hp.png', 'fincent-webpages-fincent-lp-3.png'):
                size=(im.width // 2, im.height // 2)
                im.resize(size, Image.Resampling.LANCZOS).save(target, optimize=True)
        asset_map[folder+'/'+p.name]=(name,*size)

def img(path,alt,zoom=True,lazy=True,cls=''):
    name,w,h=asset_map[path]; url='assets/'+name
    image=f'<img src="{url}" alt="{e(alt)}" width="{w}" height="{h}" loading="{"lazy" if lazy else "eager"}" decoding="async" class="{cls}">'
    return f'<a class="artwork" href="{url}" data-lightbox aria-label="Enlarge: {e(alt)}">{image}</a>' if zoom else image

def section_lines(start,end): return lines[lines.index(start)+1:lines.index(end)]
def body_html(ls):
    result=[]
    in_list=False
    for s in ls:
        if s.startswith(('Field Tag:','Field tag:','Field tags:','Button:','[','Heading:')): continue
        s=re.sub(r'^Description:\s*','',s)
        if not s:continue
        s=s.replace('Vincent’s','Fincent’s').replace('under progress','in progress')
        s=s.replace('Fincent, as a design-centric company, the aim was to revamp Fincent’s visual aesthetic, starting with the homepage, keeping in mind the brands new visual identity.', 'For Fincent, a design-centric company, the aim was to revamp the visual aesthetic, starting with the homepage and keeping the brand’s new visual identity in mind.')
        is_bullet=s in bullet_lines
        if is_bullet and not in_list:result.append('<ul>');in_list=True
        if not is_bullet and in_list:result.append('</ul>');in_list=False
        t=e(s)
        t=re.sub(r'^(Observation|Problem|Root Cause|Fix|Design Mechanics|What worked|What I’d improve|Before the system|Step [123]:[^—]*)(:| —)',r'<strong>\1\2</strong>',t)
        result.append(('<li>'+t+'</li>') if is_bullet else ('<p>'+t+'</p>'))
    if in_list:result.append('</ul>')
    return '\n'.join(result)

def blocks(ls):
    out=[];current=None;tag=''
    for s in ls:
        if s.lower().startswith('field tag:'):tag=s.split(':',1)[1].strip()
        elif s.startswith('Heading:'):
            current={'title':s[8:].strip(),'tag':tag,'lines':[]};tag='';out.append(current)
        elif current is not None:current['lines'].append(s)
    return out

def social():
    a=['<a href="mailto:daisy3012@gmail.com">Email<span class="sr-only"> Daisy at daisy3012@gmail.com</span></a>']
    for title in ['LinkedIn','Behance']:
        url=next(v for k,v in links.items() if title.lower() in k.lower())
        a.append(f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{title}<span class="sr-only"> (opens in a new tab)</span></a>')
    a.append(f'<a href="assets/{RESUME}" target="_blank" rel="noopener noreferrer">Resume<span class="sr-only"> (PDF, opens in a new tab)</span></a>')
    return '<div class="social">'+'<span aria-hidden="true">·</span>'.join(a)+'</div>'

LOGO_MARKUP='<a class="site-logo" href="{href}" aria-label="Daisy Mahadevan — Home"><img class="logo-original" src="assets/website-logo.svg" alt="Daisy Mahadevan" width="702" height="234"><img class="logo-white" src="assets/website-logo-white.svg" alt="" aria-hidden="true" width="702" height="234"></a>'

def nav(home=False):
    return '<a class="skip-link" href="#main">Skip to content</a><header class="site-header">'+LOGO_MARKUP.format(href='#about' if home else 'index.html#about')+'<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="main-navigation" aria-label="Open navigation menu"><span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span></button><nav id="main-navigation" aria-label="Main navigation">'+''.join(f'<a href="{"" if home else "index.html"}#{x.lower()}">{"Home" if x=="About" else x}</a>' for x in ['About','Skills','Work','Contact'])+'</nav></header>'

def footer():return '<footer class="project-footer" data-theme="dark">'+social()+'<p>© 2026 Daisy Mahadevan</p></footer>'
# Embed only the logo avatar so browser tabs do not depend on a separate fetch.
FAVICON_MARKUP = ''.join(
    f'<link rel="icon" href="data:{mime};base64,{base64.b64encode((ASSETS/name).read_bytes()).decode()}" type="{mime}" sizes="{size}">'
    for name, mime, size in [
        ('avatar-icon-32.png', 'image/png', '32x32'),
        ('avatar-icon-48.png', 'image/png', '48x48'),
        ('avatar-favicon.svg', 'image/svg+xml', 'any'),
    ]
)
def page(title,content,home=False):
    return f'''<!doctype html>
<html lang="en" class="{'home-document' if home else 'project-document'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} | Daisy Mahadevan</title><meta name="description" content="Design leader with 10+ years in brand, web and marketing design. Open to Design Manager and Graphic Design Lead roles."><meta name="theme-color" content="#253426">{FAVICON_MARKUP}<link rel="apple-touch-icon" href="/assets/avatar-apple-touch-icon.png?v=045273639194" sizes="180x180"><link rel="manifest" href="/site.webmanifest?v=045273639194"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400;1,6..72,500&display=swap" rel="stylesheet"><link rel="stylesheet" href="styles.css?v=b25c92f81d0c">{'<script src="assets/vendor/gsap.min.js" defer></script><script src="assets/vendor/ScrollTrigger.min.js" defer></script>' if home else ''}<script src="script.js?v=9ab0aac21740" defer></script></head><body class="{'home' if home else 'project-page'}">{nav(home)}{content}<dialog class="image-dialog" aria-label="Artwork viewer"><div class="viewer-bar"><span>Artwork preview</span><a class="original-link" target="_blank" rel="noopener">Open full size ↗</a><button type="button" class="close-viewer" aria-label="Close artwork viewer">Close ×</button></div><div class="viewer-scroll"><img alt=""></div></dialog></body></html>'''
projects=[
('website-audit','Website Audit','A clearer JustCall website, built from a consistent system of reusable components.','Website Audit/Hero Center_A.png'),
('claude-design-system','Claude Design System','Brand rules that help Claude create consistent marketing collateral.','Claude Design System/CD_Decks.png'),
('swym-branding','Brand Refresh (Swym)','A fresh visual identity and six web experiences rooted in Swym’s signature green.','Swym Branding/Swym_LP 1_Homepage.png'),
('fincent-branding','Brand Refresh (Fincent)','A lively visual language for a modern, approachable financial brand.','Fincent Branding/Fincent_Logo.png'),
('fincent-webpages','Web Pages (Fincent)','A new look for Fincent’s homepage, product pages and careers experience.','Fincent Webpages/Fincent_LP 2 (HP).png'),
('logos','Logos','A selection of logo and brand identity projects.',None)]
# Repository thumbnails replace the earlier CSS mockup compositions.
thumbnail_sources={
    'website-audit':'Website Audit thumbnail.png',
    'logos':'Logos thumbnail.png',
    'swym-branding':'Swym Branding thumbnail.png',
    'fincent-branding':'Fincent Branding thumbnail.png',
    'fincent-webpages':'Webpages Fincent thumbnail.png',
}
for key,filename in thumbnail_sources.items():
    shutil.copy2(SRC/'Project Thumbnails'/filename,ASSETS/(key+'-thumbnail.png'))
# The edited Claude thumbnail is a checked-in asset; preserve its removed heading.
def thumbnail(key,title,path):
    filename='swym-branding-thumbnail-edited.png' if key=='swym-branding' else key+'-thumbnail.png'
    with Image.open(ASSETS/filename) as artwork: w,h=artwork.size
    return f'<img class="project-thumbnail" src="assets/{filename}" alt="{e(title)} project preview" width="{w}" height="{h}" loading="lazy" decoding="async">'

hero=section_lines('Fold 1: Hero','Fold 2: Services')
about=[s for s in hero if s.startswith('Description:') or s.startswith('I’m a designer') or s.startswith('When I’m')]
keywords=['10+ years','B2B SaaS','detail','colour','typography obsession','AI','stay with me','houseplants','art','music','Spotify algorithm','ocean']
about_html=body_html(about)
for keyword in keywords:
    about_html=re.sub(r'(?<!\w)'+re.escape(keyword)+r'(?!\w)',lambda m:'<strong>'+m.group(0)+'</strong>',about_html)
hero_html=f'''<main id="main"><section class="hero" id="about" data-theme="light"><div class="hero-green"></div><div class="hero-photo">{img('Hero Image/Hero Image Daisy.png','Daisy Mahadevan standing in front of a wall of ivy',False,False)}</div><div class="hero-title"><h1>Hi, I’m Daisy<br>and I <em>design</em> stuff</h1><p class="hero-subtitle">A green thumb for growing ideas, brands and creative teams.</p><a class="button" href="#work"><span class="button-label">My work</span> <span class="button-arrow" aria-hidden="true"></span></a></div><div class="hero-about">{about_html}</div></section>'''
skill_lines=section_lines('Fold 2: Services','Fold 3: Projects'); skill_items=[]
for i,s in enumerate(skill_lines):
    if s.startswith('Above ground:') and i>0:skill_items.append((skill_lines[i-1],s,skill_lines[i+1]))
skills='<section class="skills section-pad" id="skills" data-theme="dark"><div><p class="eyebrow">Services offered</p><h2>What I bring to<br>the table <em>(besides plants)</em></h2><a class="button" href="#work"><span class="button-label">My work</span> <span class="button-arrow" aria-hidden="true"></span></a></div><div class="skill-list">'
for i,(title,above,below) in enumerate(skill_items):
    skills+=f'<details name="skills" {"open" if i==0 else ""}><summary>{e(title)}<span class="toggle" aria-hidden="true"></span></summary><div class="skill-copy"><p>{e(above)}</p><p>{e(below)}</p></div></details>'
skills+='</div></section>'
work='<section class="work section-pad" id="work" data-theme="light"><p class="eyebrow">Projects</p><h2>Some ideas I’ve helped grow</h2><div class="project-grid">'
for key,title,desc,path in projects:
    if key=='website-audit': title='Website Audit (JustCall)'
    picture=thumbnail(key,title,path)
    work+=f'<a class="project-card" href="{key}.html"><div class="card-image">{picture}</div><h3>{e(title)} <span aria-hidden="true">↗</span></h3></a>'
work+='</div></section>'
contact='<section class="contact section-pad" id="contact" data-theme="dark"><p class="eyebrow">Get in touch</p><h2>Let’s dig in</h2><p class="contact-subtitle">Open to Design Manager, Design Lead and Independent roles.</p>'+social()+'<p class="copyright">© 2026 Daisy Mahadevan</p></section></main>'
(OUT/'index.html').write_text(page('Design Manager & Graphic Design Lead — Brand, Web & Marketing Design',hero_html+skills+work+contact,True))

def write_project(key,title,tag,content):
    nextp=projects[(next(i for i,p in enumerate(projects) if p[0]==key)+1)%len(projects)]
    main=f'<main id="main" data-project="{key}" class="case-study" data-theme="light"><div class="case-heading"><p class="eyebrow">{e(tag)}</p><h1>{e(title)}</h1></div>'+content+f'<nav class="project-pagination" aria-label="Project navigation"><a href="index.html#work"><span class="pagination-copy"><span class="pagination-label">Back to the collection</span><span class="pagination-title">All projects</span></span><span class="pagination-arrow" aria-hidden="true">←</span></a><a href="{nextp[0]}.html"><span class="pagination-copy"><span class="pagination-label">Next project</span><span class="pagination-title">{e(nextp[1])}</span></span><span class="pagination-arrow" aria-hidden="true">→</span></a></nav></main>'+footer()
    (OUT/(key+'.html')).write_text(page(title,main))

def sec(title,copy='',art='',tag='',id=''):
    return f'<section class="case-section" {f"id={id}" if id else ""}>'+ (f'<p class="eyebrow">{e(tag)}</p>' if tag else '')+f'<h2>{e(title)}</h2>'+copy+art+'</section>'

# Claude: preserve narrative, four output formats and the complete style guide.
bs=blocks(section_lines('Claude Design System Page','Brand Refresh (Swym) Page'))
claude=''
for i,b in enumerate(bs):
    copy=body_html(b['lines'])
    if i==1:copy+='<a class="text-link" href="#style-guide"><span class="button-label">See style guide</span> <span class="button-arrow" aria-hidden="true"></span></a>'
    if i==3:
        copy='<p>One-pagers, decks, social carousels and battlecards, all created from the same brand rules.</p>'
        for label,f in [('One-pagers','CD_OnePager.png'),('Decks','CD_Decks.png'),('Social carousels','CD_Carousels.png'),('Battlecards','CD_Battlecards.png')]:
            copy+=f'<h3 class="eyebrow output-label">{label}</h3>'+img('Claude Design System/'+f,'JustCall '+label.lower()+' created with the Claude design system')
    claude+=sec(b['title'],copy,tag=b['tag'])
claude+=sec('Style guide',art=img('Claude Design System/CD_Style Guide.png','JustCall design system: logo, typography, colour palette, icons and buttons'),id='style-guide')
write_project('claude-design-system','Claude Design System for JustCall','AI workflow',claude)
# Fincent identity.
bs=blocks(section_lines('Brand Refresh (Fincent) Page','Web Pages (Fincent) Page'))[1:]
arts=[['Fincent_Logo.png'],['Fincent_Typography.png','Fincent_Colors.png'],['Fincent_Web Colors.png'],['Fincent_Icons Illustrations.png'],['Fincent_Icons Illustrations-1.png'],['Fincent_Image style.png']]
fincent=''
for b,files in zip(bs,arts):fincent+=sec(b['title'],body_html(b['lines']),''.join(img('Fincent Branding/'+f,'Fincent '+b['title'].lower()) for f in files))
write_project('fincent-branding','Brand Refresh for Fincent','Branding',fincent)
# Group controls above full-width, collapsible artwork.
def design_actions(items, external=''):
    controls=[]
    for label,art,secondary in items:
        style='button button-secondary' if secondary else 'button'
        controls.append('<details class="design-disclosure"><summary class="'+style+'"><span class="button-label">'+e(label)+'</span><span class="disclosure-icon" aria-hidden="true"></span></summary><div class="design-content">'+art+'</div></details>')
    return '<div class="design-actions">'+''.join(controls)+external+'</div>'

def swym_video_ads():
    cards=[]
    for i in range(1,4):
        cards.append(f'<a class="video-ad" href="assets/swym-video-ad-{i}.mp4" data-video aria-label="Play Swym YouTube ad {i}"><span class="video-ad-preview"><video src="assets/swym-video-ad-{i}.mp4#t=0.1" preload="metadata" muted playsinline aria-hidden="true" tabindex="-1"></video><span class="video-ad-play" aria-hidden="true"></span></span></a>')
    section='<section class="case-section video-ads" id="video-ads"><p class="eyebrow">Video campaigns</p><h2>Swym on YouTube</h2><p>Three video ads created for YouTube.</p><div class="video-ad-grid">'+''.join(cards)+'</div></section>'
    viewer='<dialog class="video-dialog" aria-labelledby="video-viewer-title"><div class="video-panel"><div class="video-viewer-bar"><span id="video-viewer-title">Swym YouTube ad</span><button type="button" class="close-viewer" aria-label="Close video viewer">Close ×</button></div><video controls playsinline preload="none" aria-label="Swym video ad"></video><p class="video-error" role="status" hidden>Unable to play this video. <a href="#" class="video-download">Open the MP4 directly</a>.</p></div></dialog>'
    return section+viewer

# Swym: links come directly from the Word relationships, in document order.
bs=blocks(section_lines('Brand Refresh (Swym) Page','Brand Refresh (Fincent) Page'))
intro=[s for s in bs[0]['lines'] if not s.startswith(('Here are','1.','2.','3.','4.','5.','6.'))]
swym='<div class="case-intro">'+body_html(intro)+'</div>'
for title,f in [('Style guide','Swym_Style Guide.png'),('Product graphics','Swym_Product Graphics.png'),('Brand in context','Swym_Mockups.png')]:swym+=sec(title,art=img('Swym Branding/'+f,'Swym '+title.lower()))
proto=[(k,v) for k,v in links.items() if 'figma.com' in v]
for i,(label,url) in enumerate(proto,1):
    label=re.sub(r'^\d+\.\s*','',label)
    prototype=f'<a class="button button-secondary" href="{e(url)}" target="_blank" rel="noopener noreferrer"><span class="button-label">View Figma prototype</span> <span class="button-arrow" aria-hidden="true"></span><span class="sr-only"> (opens in a new tab)</span></a>'
    filename='Swym_LP 1_Homepage.png' if i==1 else f'Swym_LP {i}.png'
    swym+=sec(label,art=design_actions([('See Design',img('Swym Branding/'+filename,'Swym '+label+' page design'),False)],prototype))
for i in range(1,4):
    shutil.copy2(SRC/'Swym Branding'/'Swym Video Ads'/f'Shopify Plus Video Ad {i}.mp4',ASSETS/f'swym-video-ad-{i}.mp4')
swym+=swym_video_ads()
write_project('swym-branding','Brand Refresh for Swym','Branding',swym)
# Native disclosure controls keep artwork available without a long initial scroll.
def design_dropdown(art,label='See design'):
    return '<details class="design-disclosure"><summary class="button"><span class="button-label">'+e(label)+'</span> <span class="disclosure-icon" aria-hidden="true"></span></summary><div class="design-content">'+art+'</div></details>'

# Copy the supplied Fincent hover previews and fullscreen videos.
for slug,filename in [('homepage','Fincent Homepage video.mp4'),('product-pages','Fincent Product Pages video.mp4')]:
    shutil.copy2(SRC/'Fincent Webpages'/filename,ASSETS/f'fincent-{slug}.mp4')
bs=blocks(section_lines('Web Pages (Fincent) Page','Logos Page'))[1:]
web=''
for i,b in enumerate(bs):
    title=b['title']
    if i==0:
        title='Homepage exploration'
        art='<a class="video-ad fincent-video" href="assets/fincent-homepage.mp4" data-video data-arrival-video data-fullscreen aria-label="Play Homepage animation"><span class="video-ad-preview"><video src="assets/fincent-homepage.mp4#t=0.1" preload="metadata" muted loop playsinline aria-hidden="true" tabindex="-1"></video><span class="video-ad-play" aria-hidden="true"></span></span></a>'
        art+=design_dropdown(img('Fincent Webpages/Fincent_LP 2 (HP).png','Fincent homepage exploration with product features and customer stories'))
    elif i==1:
        art='<a class="video-ad fincent-video" href="assets/fincent-product-pages.mp4" data-video data-arrival-video data-fullscreen aria-label="Play Product page walkthrough"><span class="video-ad-preview"><video src="assets/fincent-product-pages.mp4#t=0.1" preload="metadata" muted loop playsinline aria-hidden="true" tabindex="-1"></video><span class="video-ad-play" aria-hidden="true"></span></span></a>'
        art+=design_dropdown(img('Fincent Webpages/Fincent_LP 3.png','Fincent product page design'))
    else:
        art=design_dropdown(img('Fincent Webpages/Fincent_LP 1.png','Fincent careers page: team, testimonials, benefits and open roles'))
    web+=sec(title,body_html(b['lines']),art)
web+='<dialog class="video-dialog" aria-labelledby="video-viewer-title"><div class="video-panel"><div class="video-viewer-bar"><span id="video-viewer-title">Fincent video</span><button type="button" class="close-viewer" aria-label="Close video viewer">Close ×</button></div><video controls playsinline preload="none" aria-label="Fincent video"></video><p class="video-error" role="status" hidden>Unable to play this video. <a href="#" class="video-download">Open the MP4 directly</a>.</p></div></dialog>'
write_project('fincent-webpages','Web designs for Fincent','Landing pages',web)
# Preserve numeric artwork order and original animated GIFs.
from logo_projects import render_logos
logos=render_logos(SRC/'Logos',ASSETS)
write_project('logos','Logos & brand identities','Selected identities',logos)
# Complete audit with all before/after pairs and reusable templates.
bs=blocks(section_lines('Website Audit Page','Claude Design System Page'))[1:]
pairs={'Navbar':'Nav Bar','Hero (Center-aligned)':'Hero Center','Hero (Left-aligned)':'Hero Left','Capsule tabs':'Capsule tabs','Features (bento)':'Product Features Bento','Integrations':'Integrations','Social Proof':'Social Proof','Pricing':'Pricing','Footer':'Footer','Footer Banner':'Footer Banner','Hub':'Hub','Security Badges':'Security Badges'}
audit='';security_seen=False
for b in bs:
    title=b['title']; art='';copy=body_html(b['lines'])
    if title=='Security Badges':
        if security_seen:title='Calculator'
        security_seen=True
    if b['tag']=='Templates':
        templates={
            'Product': [('Desktop Template','Template Product.png',False),('See Live Page','Template Product_Live Page.png',True)],
            'Solutions': [('Desktop Design','Template Solutions_Desktop.png',False),('Mobile Design','Template Solutions_Mobile.png',False),('See Live Page','Template Solutions_Live Page 1.png',True),('see live page','Template Solutions_Live Page 2.png',True)],
            'Hub': [('See Live Page','Template Hub_Live Page 1.png',False),('See Live Page','Template Hub_Live Page 2.png',False),('Integrations Page','Template Hub_Live Page 3.png',False)]
        }[title]
        actions=design_actions([(label,img('Website Audit/'+f,'JustCall '+title+' — '+Path(f).stem),secondary) for label,f,secondary in templates])
        if title=='Solutions':
            actions=re.sub(r'<a class="artwork" href="assets/website-audit-template-solutions-mobile.png".*?</a>',lambda _: '<div class="phone-mockup"><div class="phone-screen" tabindex="0" role="region" aria-label="Scrollable JustCall Solutions mobile design"><div class="phone-page"><img src="assets/website-audit-template-solutions-mobile.png" alt="JustCall Solutions mobile page design" width="2480" height="23072" loading="lazy" decoding="async"></div></div></div>',actions,flags=re.S)
        if title in ('Solutions', 'Product', 'Hub'):
            from solution_previews import device_previews
            actions=device_previews(actions)
        template_section=sec(title,copy,actions,'Template')
        if title=='Hub': template_section=template_section.replace('class="case-section"','class="case-section hub-template"',1)
        audit+=template_section
        continue
    elif title=='Competitor Research':
        art=img('Website Audit/Competitor Research.png','Benchmark of SaaS website layouts used in the JustCall audit')
        # The reference places the research board immediately after the introductory line.
        first,*rest=b['lines'];copy=body_html([first])+art+body_html(rest);art=''
    elif title in pairs or title in ['Calculator','Homepage Redesign']:
        base=pairs.get(title,title)
        files=['Homepage_Before.png','Homepage_After.png'] if title=='Homepage Redesign' else [base+'.png',base+'_A.png']
        art='<div class="comparison">'+''.join(f'<figure><figcaption class="eyebrow">{label}</figcaption>'+img('Website Audit/'+f,'JustCall '+title.lower()+' — '+label.lower())+'</figure>' for label,f in zip(['Before','After'],files))+'</div>'
        copy,art=art+copy,''
    section=sec(title,copy,art,b['tag'])
    if title=='Competitor Research':
        section=section.replace('class="case-section"','class="case-section competitor-research"',1)
    if '<div class="comparison">' in section and title!='Homepage Redesign':
        section=section.replace('class="case-section"','class="case-section audit-topic"',1)
        section=section.replace('<h2>'+e(title)+'</h2>','<details class="audit-disclosure"><summary><h2>'+e(title)+'</h2><span class="toggle" aria-hidden="true"></span></summary><div class="audit-detail-content">',1)
        section=section.replace('</section>','<button type="button" class="button button-secondary collapse-comparison"><span class="button-label">Collapse comparison</span></button></div></details></section>')
    audit+=section
write_project('website-audit','Website Audit for JustCall','Audit',audit)
# Avatar icons are maintained assets referenced by the shared page template.
# Do not recreate legacy favicon variants during content builds.
print(f'Built {len(list(OUT.glob("*.html")))} pages, {len(asset_map)} original PNG artworks, {len(proto)} prototype links and {len(skill_items)} skills.')
