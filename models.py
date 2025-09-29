from mongoengine import (
    Document, EmbeddedDocument, StringField, ReferenceField,
    ListField, EmbeddedDocumentField, IntField, BooleanField,
    DateTimeField, FloatField, DictField
)
import datetime

class Artisan(EmbeddedDocument):
    name = StringField(required=True)
    slug = StringField(required=True)
    location = StringField()
    bio = StringField()
    images = ListField(StringField())
    video_url = StringField()

class Product(Document):
    title = StringField(required=True)
    slug = StringField(required=True, unique=True)
    description = StringField()
    artisan = EmbeddedDocumentField(Artisan)
    making_process = ListField(DictField())  # each item: {step:int, text:str, image:str}
    images = ListField(StringField())
    base_price = FloatField(default=0.0)
    price = FloatField(default=0.0)  # convenience field for frontend
    stock = IntField(default=0)
    active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    heritage_video_url = StringField() # <-- ADD THIS LINE
    active = BooleanField(default=True)

    meta = {'collection': 'products', 'ordering': ['-created_at']}

class User(Document):
    email = StringField(required=True, unique=True)
    name = StringField()
    password_hash = StringField(required=True)
    role = StringField(default='buyer')  # 'buyer' or 'seller' (or 'admin')
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'users'}

class Order(Document):
    user = ReferenceField(User)
    items = ListField(DictField())  # {product_id, title, qty, price}
    shipping_address = DictField()
    total = FloatField()
    status = StringField(default='created')
    payment = DictField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'orders'}
