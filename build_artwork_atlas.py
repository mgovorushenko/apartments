"""Pack licensed local source images into a single static GPU/export texture."""
from pathlib import Path
from PIL import Image

root=Path(__file__).with_name('assets')
atlas=Image.new('RGB',(1024,1024),(235,232,224))
for name,xy in [('nordic-lake-art.png',(0,0)),('monet-lilies.jpg',(512,0)),('corot-forest.jpg',(0,512))]:
    # Original aspect is restored by each artwork's UV mapping in all renderers.
    im=Image.open(root/name).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
    atlas.paste(im,xy)
atlas.save(root/'artwork-atlas.png',optimize=True)
