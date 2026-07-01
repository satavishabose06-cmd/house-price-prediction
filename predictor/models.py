from django.db import models
from django.utils import timezone

class Prediction(models.Model):
    location = models.CharField(max_length=255, default='Unknown')
    sqft = models.IntegerField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    floors = models.IntegerField(default=1)
    year_built = models.IntegerField(null=True, blank=True)
    parking = models.BooleanField(default=False)
    furnishing = models.CharField(max_length=50, default='Unfurnished')
    
    predicted_price = models.DecimalField(max_digits=12, decimal_places=2)
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Prediction: ${self.predicted_price} ({self.location}, {self.sqft} sqft, {self.bedrooms} BHK)"
