# # wardrobe/tryon.py
# """
# Calls a self-hosted OOTDiffusion instance (running on Google Colab's free
# GPU tier, exposed via a temporary gradio.live public URL) to generate a
# photo of the user wearing wardrobe item(s) — virtual try-on.

# Unlike the free public IDM-VTON demo, this exposes a real "category"
# parameter (Upper-body / Lower-body / Dress), so bottoms are correctly
# placed on the legs instead of being misapplied to the torso.

# Since this runs on your own Colab notebook rather than a permanent
# service, OOTD_SPACE_URL in .env needs to be updated with a fresh URL
# each time the Colab runtime restarts (session limits, disconnects, etc).
# Falls back to the public levihsu/OOTDiffusion Space if no URL is set,
# though that Space is known to be broken/crashing as of this writing.
# """

# from PIL import Image
# import tempfile

# def _flatten_to_white(image_path):
#     """Garment images with transparency (like our background-removed
#     processed_image PNGs) can confuse the try-on model — transparent
#     areas can render as see-through holes or invented texture instead
#     of being treated as 'no background here'. Flatten onto plain white
#     first so the model only ever sees a normal, opaque garment photo."""
#     img = Image.open(image_path)
#     if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
#         img = img.convert("RGBA")
#         background = Image.new("RGB", img.size, (255, 255, 255))
#         background.paste(img, mask=img.split()[-1])
#         tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
#         background.save(tmp.name)
#         return tmp.name
#     return image_path

# import os
# from gradio_client import Client, handle_file

# HF_TOKEN = os.environ.get("HF_TOKEN")
# SPACE_NAME = os.environ.get("OOTD_SPACE_URL", "levihsu/OOTDiffusion")

# _client = None

# def _get_client():
#     global _client
#     if _client is None:
#         _client = Client(SPACE_NAME)
#     return _client


# def _run_single_garment(person_image_path, garment_image_path, category):
#     client = _get_client()
#     garment_image_path = _flatten_to_white(garment_image_path)  # NEW
#     result = client.predict(
#         vton_img=handle_file(person_image_path),
#         garm_img=handle_file(garment_image_path),
#         category=category,
#         n_samples=1,
#         n_steps=30,  # bumped from 20 — a bit more denoising helps fidelity/reduces invented detail
#         image_scale=2,
#         seed=-1,
#         api_name="/process_dc",
#     )
#     ...

#     # process_dc returns a gallery: a list of {"image": <path>, "caption": ...}
#     output = result[0] if isinstance(result, list) else result
#     if isinstance(output, dict):
#         path = output.get("image") or output.get("path") or output.get("url")
#     else:
#         path = output

#     print("DEBUG resolved path:", path, "exists:", os.path.exists(path) if path else None)  # TEMP
#     return path

# def generate_tryon(person_image_path, top_image_path=None, bottom_image_path=None,
#                     bottom_category="Lower-body"):
#     """
#     Applies a top and/or bottom, each correctly masked to its own body
#     region. bottom_category should be "Dress" when the bottom item is a
#     dress, otherwise "Lower-body". If both top and bottom are given, the
#     top is applied first, then the bottom is applied to THAT result.
#     Returns the local filepath of the final image.
#     """
#     current_person_path = person_image_path

#     if top_image_path:
#         current_person_path = _run_single_garment(current_person_path, top_image_path, "Upper-body")

#     if bottom_image_path:
#         current_person_path = _run_single_garment(current_person_path, bottom_image_path, bottom_category)

#     return current_person_path


# wardrobe/tryon.py
"""
Calls a self-hosted OOTDiffusion instance (running on Google Colab's free
GPU tier, exposed via a temporary gradio.live public URL) to generate a
photo of the user wearing wardrobe item(s) — virtual try-on.

Unlike the free public IDM-VTON demo, this exposes a real "category"
parameter (Upper-body / Lower-body / Dress), so bottoms are correctly
placed on the legs instead of being misapplied to the torso.

Since this runs on your own Colab notebook rather than a permanent
service, OOTD_SPACE_URL in .env needs to be updated with a fresh URL
each time the Colab runtime restarts (session limits, disconnects, etc).
Falls back to the public levihsu/OOTDiffusion Space if no URL is set,
though that Space is known to be broken/crashing as of this writing.
"""

from PIL import Image
import tempfile
import os
from gradio_client import Client, handle_file


def _flatten_to_white(image_path):
    """Images with transparency (background-removed garment PNGs, or a
    person photo with a transparent background) need to be flattened onto
    plain white before going into OOTDiffusion — otherwise transparent
    areas either render as black (a naive RGB conversion drops the alpha
    channel without compositing it onto anything first) or confuse the
    model as see-through holes instead of 'no background here'."""
    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])  # use alpha channel as paste mask
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        background.save(tmp.name)
        return tmp.name
    return image_path


HF_TOKEN = os.environ.get("HF_TOKEN")
SPACE_NAME = os.environ.get("OOTD_SPACE_URL", "levihsu/OOTDiffusion")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Client(SPACE_NAME)
    return _client


def _run_single_garment(person_image_path, garment_image_path, category):
    client = _get_client()
    person_image_path = _flatten_to_white(person_image_path)   # CHANGED — flatten person photo too
    garment_image_path = _flatten_to_white(garment_image_path)
    result = client.predict(
        vton_img=handle_file(person_image_path),
        garm_img=handle_file(garment_image_path),
        category=category,
        n_samples=1,
        n_steps=30,  # bumped from 20 — a bit more denoising helps fidelity/reduces invented detail
        image_scale=2,
        seed=-1,
        api_name="/process_dc",
    )
    ...

    # process_dc returns a gallery: a list of {"image": <path>, "caption": ...}
    output = result[0] if isinstance(result, list) else result
    if isinstance(output, dict):
        path = output.get("image") or output.get("path") or output.get("url")
    else:
        path = output

    print("DEBUG resolved path:", path, "exists:", os.path.exists(path) if path else None)  # TEMP
    return path

def generate_tryon(person_image_path, top_image_path=None, bottom_image_path=None,
                    bottom_category="Lower-body"):
    """
    Applies a top and/or bottom, each correctly masked to its own body
    region. bottom_category should be "Dress" when the bottom item is a
    dress, otherwise "Lower-body". If both top and bottom are given, the
    top is applied first, then the bottom is applied to THAT result.
    Returns the local filepath of the final image.
    """
    current_person_path = person_image_path

    if top_image_path:
        current_person_path = _run_single_garment(current_person_path, top_image_path, "Upper-body")

    if bottom_image_path:
        current_person_path = _run_single_garment(current_person_path, bottom_image_path, bottom_category)

    return current_person_path



