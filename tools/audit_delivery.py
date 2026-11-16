"""Verify the actual submission ZIP, rendered pages, PNGs and both streams of the film."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

import cv2
import numpy as np
from PIL import Image
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
QA=ROOT/'qa'/'edition'


def digest(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


movie=DIST/'山河织路-演示片.mp4'
offline=DIST/'山河织路-离线单文件.html'
archive=DIST/'山河织路-参赛材料.zip'
documents=[ROOT/'docs'/name for name in ('设计说明.pdf','交互流程图.pdf')]
boards=sorted((ROOT/'docs'/'boards').glob('board_*.png'))
pages=[len(PdfReader(file).pages) for file in documents]
assert pages==[7,2]
assert len(boards)==5
for file in boards:
    with Image.open(file) as image:
        assert image.size==(2400,1500)
        stripes=np.asarray(image.convert('RGB'))[:,::8].std(axis=1).mean(axis=1)
        assert np.sum(stripes[110:-100]<.5)<10,file
with ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    members=bundle.namelist()
    packed={}
    for member in members:
        with bundle.open(member) as stream:
            packed[member]=hashlib.file_digest(stream,'sha256').hexdigest()
    font_sources=ROOT/'assets'/'sources'/'lettering'
    for file in [offline,movie,*documents,*boards,ROOT/'assets'/'sources'/'作品素材说明.md',
                 font_sources/'sources.json',font_sources/'mashanzheng-OFL.txt',font_sources/'zcoolqingkehuangyou-OFL.txt']:
        assert digest(file) in packed.values(),file
    screens=[f for f in members if f.startswith('03_') and f.endswith('.png')]
    assert len(screens)==12
    captured={digest(file) for file in (ROOT/'qa'/'optimized').glob('*.png')}
    assert all(packed[file] in captured for file in screens)
assert digest(movie)==digest(ROOT/'production'/'film_delivery.mp4')
ffmpeg=ROOT/'node_modules'/'ffmpeg-static'/'ffmpeg.exe'
probe=subprocess.run([str(ffmpeg),'-hide_banner','-i',str(movie)],capture_output=True,encoding='utf-8',errors='replace').stderr
assert re.search(r'Video: h264.*1920x1080',probe)
assert re.search(r'Audio: aac.*48000 Hz, stereo',probe)
subprocess.run([str(ffmpeg),'-v','error','-i',str(movie),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
video=cv2.VideoCapture(str(movie))
frames=int(video.get(cv2.CAP_PROP_FRAME_COUNT));fps=video.get(cv2.CAP_PROP_FPS)
assert (frames,fps)==(2448,24.)
gallery=Image.new('RGB',(960,3*180),'#eee3d2')
for i,seconds in enumerate((2,9,23,37,51,65,78,84,98)):
    video.set(cv2.CAP_PROP_POS_FRAMES,round(seconds*fps))
    ok,pixels=video.read()
    assert ok and pixels.std()>7
    image=Image.fromarray(cv2.cvtColor(pixels,cv2.COLOR_BGR2RGB))
    gallery.paste(image.resize((320,180),Image.Resampling.LANCZOS),(i%3*320,i//3*180))
video.release()
gallery.save(ROOT/'qa'/'animation'/'film-contact.jpg',quality=91)
# Keep each passage uncut in the short viewing copy. Only the time spent inside
# each chapter is removed; the interactive edition and competition film are intact.
clips=[(15.1,21.3),(30.8,36.2),(43.0,48.5),(56.7,62.5)]
filters=[]
for i,(start,end) in enumerate(clips):
    filters.append(f'[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,scale=960:540[v{i}]')
    filters.append(f'[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,'
                   f'afade=t=in:d=0.1,afade=t=out:st={end-start-.10:.2f}:d=0.1[a{i}]')
filters.append(''.join(f'[v{i}][a{i}]' for i in range(len(clips)))+'concat=n=4:v=1:a=1[v][a]')
preview=ROOT/'qa'/'crossings'
preview.mkdir(exist_ok=True)
subprocess.run([str(ffmpeg),'-y','-loglevel','error','-i',str(movie),'-filter_complex',';'.join(filters),
                '-map','[v]','-map','[a]','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-c:a','aac',
                '-movflags','+faststart',str(preview/'四段跨岛预览.mp4')],check=True)
native=json.loads((QA/'native-audit.json').read_text('utf-8'))
assert len(native)==11 and all(row['meshes'] and not row['missing'] for row in native)
checks=json.loads((ROOT/'qa'/'optimized'/'results.json').read_text('utf-8'))
perf=json.loads((QA/'performance.json').read_text('utf-8'))
assert not checks['runtimeErrors'] and not perf['errors']
arrivals=json.loads((QA.parent/'arrival'/'checks.json').read_text('utf-8'))
departures=json.loads((QA/'departures.json').read_text('utf-8'))
assert set(arrivals['results'])=={'desktop','phone'} and not arrivals['errors']
assert len(departures['flights'])==4 and not departures['errors']
visual=json.loads((QA.parent/'refinement'/'visibility.json').read_text('utf-8'))
assert len(visual['samples'])==20 and all(not row['clip'] and not row['blockers'] for row in visual['samples'])
assert len(visual['labels'])==5 and all(not row['pairs'] and not row['outside'] for row in visual['labels'])
assert len(visual['flights'])==8 and all(row['crossesGap'] and row['bothBanks'] and not row['hits'] for row in visual['flights'])
parking=json.loads((QA.parent/'refinement'/'cinema.json').read_text('utf-8'))
assert len(parking['bicycles'])==2 and parking['centerSpacing']>1.15
report=dict(outputs=[dict(path=f.relative_to(ROOT).as_posix(),bytes=f.stat().st_size,sha256=digest(f))
                     for f in (archive,movie,offline,*documents)],
            packagedFiles=len(members),interfacePNGs=len(screens),boards=dict(count=5,pixels=[2400,1500]),
            pdfPages=dict(design=pages[0],flow=pages[1]),
            film=dict(seconds=frames/fps,frames=frames,pixels=[1920,1080],fps=fps,audio='AAC stereo 48000 Hz'),
            nativeBlends=len(native),runtimeRegressionChecks=checks['checks'],fixedCameraFps=[r['fps'] for r in perf['chapters']],
            stationViews=len(visual['samples']),overviewLayouts=len(visual['labels']),parkingSpacingMetres=parking['centerSpacing'],
            continuousIslandCrossings=4,flightViews=len(visual['flights']),adjacentChapterFlightSeconds=visual['input']['chapter']['flightSeconds'],
            letterAndLaunchViewports=list(arrivals['results']),readyMs=departures['readyMs'],
            firstCrossingWorstMs=[flight['worst']['ms'] for flight in departures['flights']],
            movingCrossingFps=[r['fps'] for r in perf['crossings']])
(QA/'delivery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Verified',len(members),'ZIP members,',frames,'film frames and',sum(pages),'PDF pages')
