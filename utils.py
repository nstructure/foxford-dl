from pathlib import Path
from glob import glob
import re
from PIL import Image

class ImagesToPDF(object):
    def __init__(self, dir):
        self._dir = dir
    
    def convert(self, filepath, glob_pattern):
        
        def natural_sort(l): 
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
            return sorted(l, key=alphanum_key)

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath = filepath.with_suffix('.pdf')

        images = natural_sort(
            glob(f'{self._dir}/{glob_pattern}')
        )

        imglist = []
        
        for i in images:
            imglist.append(Image.open(i).convert('RGB'))
        
        if imglist:
            imglist[0].save(
                filepath,
                save_all=True,
                append_images=imglist[1:]
            )