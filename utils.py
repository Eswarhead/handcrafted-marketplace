import os
import uuid
from config import CLOUDINARY_URL
import cloudinary.uploader

USE_CLOUDINARY = bool(CLOUDINARY_URL)

# local uploads directory (used when Cloudinary not configured)
LOCAL_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)

def upload_image(file_storage, filename=None):
    """
    Upload file_storage (werkzeug FileStorage) to Cloudinary if configured,
    otherwise saves to backend/static/uploads and returns a local URL path.
    """
    filename = filename or (getattr(file_storage, 'filename', None) or str(uuid.uuid4()))
    if USE_CLOUDINARY:
        # cloudinary.uploader.upload accepts file-like or file path
        res = cloudinary.uploader.upload(file_storage, public_id=os.path.splitext(filename)[0], overwrite=True)
        return res.get('secure_url')
    else:
        # save locally
        safe_name = f"{uuid.uuid4().hex}_{filename}"
        path = os.path.join(LOCAL_UPLOAD_DIR, safe_name)
        # file_storage could be werkzeug.datastructures.FileStorage
        file_storage.save(path)
        # return a URL path client can load from backend static endpoint
        return  f"http://localhost:5000/static/uploads/{safe_name}"

VIDEO_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'videos')
os.makedirs(VIDEO_UPLOAD_DIR, exist_ok=True)

def upload_video(file_storage, filename=None):
    if not filename:
        filename = file_storage.filename
    
    # We are not using Cloudinary for videos in this example
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(VIDEO_UPLOAD_DIR, safe_name)
    file_storage.save(path)
    return f"http://localhost:5000/static/uploads/videos/{safe_name}"