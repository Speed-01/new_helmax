from django.apps import AppConfig

class ManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manager'


import cloudinary
import cloudinary.uploader


# Dummy products data
products = [
    {
        "id": 1,
        "name": "Steelbird SIBR 17 Helmet",
        "price": 1999,
        "stock": 40,
        "category": "Fullface Helmet",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg"
    },
    {
        "id": 2,
        "name": "Studds Shifter Helmet",
        "price": 2000,
        "stock": 40,
        "category": "Fullface Helmet",
        "image_url": "https://res.cloudinary.com/demo/image/upload/sample2.jpg"
    }
]


