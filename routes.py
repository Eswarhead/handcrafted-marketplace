from flask import Blueprint, request, jsonify, current_app, send_from_directory
from models import Product, Artisan, User
from mongoengine.errors import NotUniqueError
from utils import upload_image,upload_video
import uuid, os
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('api', __name__)

# Serve local uploaded static files when using local storage
@bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    static_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    return send_from_directory(static_dir, filename)

def product_to_dict(p):
    """Convert Product Document to JSON-serializable dict."""
    m = p.to_mongo().to_dict()
    # convert ObjectId to string
    if '_id' in m:
        m['id'] = str(m['_id'])
        del m['_id']
    # convert artisan (embedded) if present
    if 'artisan' in m and m['artisan'] is not None:
        art = m['artisan']
        # mongoengine embedded becomes SON object; ensure it's serializable
        try:
            m['artisan'] = {
                'name': art.get('name'),
                'slug': art.get('slug'),
                'location': art.get('location'),
                'bio': art.get('bio'),
                'images': art.get('images', []),
                'video_url': art.get('video_url', None)
            }
        except Exception:
            m['artisan'] = art
        if 'heritage_video_url' in m:
            m['heritage_video_url'] = m.get('heritage_video_url')
    return m

@bp.route('/products', methods=['GET'])
def list_products():
    q = request.args.get('q')
    page = int(request.args.get('page', 1))
    per = int(request.args.get('per', 24))
    # fetch products active=True
    query = Product.objects(active=True)
    if q:
        query = query.filter(title__icontains=q)
    total = query.count()
    items = query.skip((page-1)*per).limit(per)
    out = [product_to_dict(p) for p in items]
    return jsonify({'total': total, 'items': out})

@bp.route('/products/<slug>', methods=['GET'])
def get_product(slug):
    p = Product.objects(slug=slug, active=True).first()
    if not p:
        return jsonify({'msg': 'not found'}), 404
    return jsonify(product_to_dict(p))


'''@jwt_required()
def create_product():
    
    # If authentication present, validate seller
    uid = get_jwt_identity()
    if uid:
        user = User.objects(id=uid).first()
        if not user:
            return jsonify({'msg':'invalid user'}), 401
        if user.role != 'seller' and user.role != 'admin':
            return jsonify({'msg':'only sellers can create products'}), 403

    # parse simple form fields
    title = request.form.get('title')
    if not title:
        return jsonify({'msg': 'title required'}), 400
    slug = request.form.get('slug') or title.lower().strip().replace(' ', '-')
    description = request.form.get('description') or ''
    price = float(request.form.get('price') or 0.0)
    artisan_name = request.form.get('artisan_name') or 'Unknown Artisan'
    artisan_slug = request.form.get('artisan_slug') or artisan_name.lower().replace(' ', '-')
    artisan_location = request.form.get('artisan_location') or ''
    artisan_bio = request.form.get('artisan_bio') or ''

    # build artisan embedded document
    artisan = Artisan(
        name=artisan_name,
        slug=artisan_slug,
        location=artisan_location,
        bio=artisan_bio,
        images=[]
    )

    # collect images (multiple)
    images = []
    if 'images' in request.files:
        files = request.files.getlist('images')
        for f in files:
            try:
                name = f.filename or f"{uuid.uuid4().hex}"
                url = upload_image(f, name)
                images.append(url)
                # also append to artisan images if you want
                artisan.images.append(url)
            except Exception as e:
                current_app.logger.exception("image upload failed")
                # continue with others

    # parse making_process: accept JSON in a field or simple numbered fields
    making_process = []
    mp_json = request.form.get('making_process')  # expected JSON array string optionally
    if mp_json:
        try:
            import json
            arr = json.loads(mp_json)
            if isinstance(arr, list):
                making_process = arr
        except Exception:
            pass

    # fallback: look for fields like making_step_1_text
    if not making_process:
        for k, v in request.form.items():
            if k.startswith('making_step_'):
                making_process.append({'text': v})

    prod = Product(
        title=title,
        slug=slug,
        description=description,
        artisan=artisan,
        making_process=making_process,
        images=images,
        price=price
    )

    try:
        prod.save()
    except NotUniqueError:
        return jsonify({'msg': 'slug already exists'}), 400
    return jsonify({'msg': 'created', 'product': product_to_dict(prod)}), 201'''
@bp.route('/products', methods=['POST'])
@jwt_required()  # Ensures a valid token is required
def create_product():
    """
    Creates a new product. Only accessible by users with the 'seller' role.
    """
    # 1. Get the current user's ID from the token and verify their role
    current_user_id = get_jwt_identity()
    user = User.objects(id=current_user_id).first()

    if not user or user.role != 'seller':
        return jsonify({"msg": "Access forbidden: Sellers only!"}), 403

    # 2. Check that the required form data and image file are present
    if 'image' not in request.files:
        return jsonify({"msg": "Image file is required"}), 400
    
    form_data = request.form
    required_fields = ['title', 'description', 'price', 'artisan_name']
    if not all(field in form_data for field in required_fields):
        return jsonify({"msg": "Missing required form fields"}), 400

    video_url = None
    if 'heritage_video' in request.files:
        video_file = request.files['heritage_video']
        if video_file.filename != '': # Check if a file was actually selected
            video_url = upload_video(video_file, filename=video_file.filename)

    # 3. Handle the image upload
    try:
        image_file = request.files['image']
        image_url = upload_image(image_file, filename=image_file.filename)
    
    except Exception as e:
        current_app.logger.error(f"Image upload failed: {e}")
        return jsonify({"msg": "Image upload failed"}), 500
 
    
    # 4. Create and save the new product
    try:
        new_product = Product(
            title=form_data['title'],
            slug=f"{form_data['title'].lower().replace(' ', '-')}-{str(uuid.uuid4())[:4]}",
            description=form_data['description'],
            price=float(form_data['price']),
            images=[image_url],
            heritage_video_url=video_url,
            artisan=Artisan(
                name=form_data['artisan_name'],
                slug=form_data['artisan_name'].lower().replace(' ', '-')
            )
        )
        new_product.save()
        return jsonify({
            "msg": "Product created successfully",
            "product": product_to_dict(new_product)
        }), 201
    except NotUniqueError:
        return jsonify({"msg": "A product with this slug already exists"}), 409
    except Exception as e:
        current_app.logger.error(f"Database save failed: {e}")
        return jsonify({"msg": "Could not save product to database"}), 500

@bp.route('/artisan/<slug>', methods=['GET'])
def artisan_page(slug):
    products = Product.objects(artisan__slug=slug, active=True)
    if products.count() == 0:
        return jsonify({'msg': 'no artisan found'}), 404
    sample = products.first()
    artisan = sample.artisan
    prod_list = [product_to_dict(p) for p in products]
    # artisan to plain dict
    art_dict = {
        'name': artisan.name,
        'slug': artisan.slug,
        'location': artisan.location,
        'bio': artisan.bio,
        'images': artisan.images or [],
        'video_url': getattr(artisan, 'video_url', None)
    }
    return jsonify({'artisan': art_dict, 'products': prod_list})

# Seller-only endpoints
@bp.route('/seller/products', methods=['GET'])
@jwt_required()
def seller_products():
    uid = get_jwt_identity()
    user = User.objects(id=uid).first()
    if not user:
        return jsonify({'msg':'invalid user'}), 401
    if user.role != 'seller' and user.role != 'admin':
        return jsonify({'msg':'unauthorized'}), 403
    # For MVP: return all products (could be filtered by seller id if you add seller reference)
    prods = Product.objects()
    return jsonify([product_to_dict(p) for p in prods])

'''@bp.route('/seller/products', methods=['POST'])
@jwt_required()
def seller_add_product():
    uid = get_jwt_identity()
    user = User.objects(id=uid).first()
    if not user:
        return jsonify({'msg':'invalid user'}), 401
    if user.role != 'seller' and user.role != 'admin':
        return jsonify({'msg':'unauthorized'}), 403
    # reuse create_product logic: call create_product() but that function expects form data in request
    return create_product()'''