from django.db import models
from django.contrib.auth.models import User

class WardrobeItem(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wardrobe_items")
    image = models.ImageField(upload_to="wardrobe/")
    category = models.CharField(max_length=30)
    category_confidence = models.FloatField()
    texture = models.CharField(max_length=30)
    texture_confidence = models.FloatField()
    season = models.CharField(max_length=20)
    season_confidence = models.FloatField()
    season_probs = models.JSONField()
    dominant_colors = models.JSONField()
    mask_found = models.BooleanField()
    uploaded_at = models.DateTimeField(auto_now_add=True)