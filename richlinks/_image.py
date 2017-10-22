import os
from PIL import Image, ImageOps


# TODO gif support (requires video transcoding)
def normalize_full_img(path, settings):
    try:
        im = Image.open(path)
        im.verify()
    except:
        return False

    im = Image.open(path).convert("RGBA")

    max_dimensions = settings["images"]["full"]["max_dimensions"]
    full_quality = settings["images"]["full"]["quality"]

    if (im.size[0] > max_dimensions[0] or im.size[1] > max_dimensions[1]):
        im.thumbnail(max_dimensions, Image.BICUBIC)
        im.save(path, im.format, quality=full_quality, optimize=True)

    # TODO filesize check #minimum gif support

    return True


def make_thumb(path, dimensions, settings, crop=True):
    try:
        temp_im = Image.open(path).convert("RGBA")
    except:
        return None

    im = Image.new('RGBA', temp_im.size, (255, 255, 255, 255))
    im.paste(temp_im, mask=temp_im)

    thumbnail_location = settings["images"]["thumb"]["save_location"]

    thumbnail_quality = settings["images"]["thumb"]["quality"]

    if crop:
        im = ImageOps.fit(im, dimensions, Image.BICUBIC)
    else:
        im.thumbnail(dimensions, Image.BICUBIC)

    img_basename = os.path.basename(path)
    img_basename = os.path.splitext(img_basename)[0]

    thumb_filename = "thumbnail_%s_%ix%i.jpg" % (img_basename, im.size[0],
                                                 im.size[1])
    thumb_path = os.path.join(thumbnail_location, thumb_filename)

    im.save(thumb_path, "JPEG", quality=thumbnail_quality, optimize=True)

    return (thumb_path, im.size)
