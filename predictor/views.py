import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Prediction

def login_view(request):
    if request.method == 'POST':
        return redirect('dashboard')
    return render(request, 'predictor/login.html')

def register_view(request):
    if request.method == 'POST':
        return redirect('login')
    return render(request, 'predictor/register.html')

def dashboard_view(request):
    predictions = Prediction.objects.all().order_by('-created_at')
    total_predictions = predictions.count()
    
    if total_predictions > 0:
        avg_price = sum(p.predicted_price for p in predictions) / total_predictions
    else:
        avg_price = 0
        
    context = {
        'total_predictions': total_predictions,
        'avg_price': avg_price,
        'predictions': predictions[:10]  # Show latest 10
    }
    return render(request, 'predictor/dashboard.html', context)

def result_view(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    
    margin = (100 - prediction.confidence_score) / 100 * float(prediction.predicted_price)
    min_price = float(prediction.predicted_price) - margin
    max_price = float(prediction.predicted_price) + margin
    
    similar_houses = []
    for i in range(3):
        sqft_diff = random.randint(-300, 300)
        price_diff = sqft_diff * 150 + random.randint(-100000, 100000)
        similar_houses.append({
            'sqft': prediction.sqft + sqft_diff,
            'bhk': prediction.bedrooms,
            'price': float(prediction.predicted_price) + price_diff,
            'distance': round(random.uniform(0.5, 3.5), 1)
        })
        
    trend_data = []
    base_sqft = max(500, prediction.sqft - 600)
    for i in range(6):
        s = base_sqft + (i * 300)
        p = s * 150 + float(prediction.predicted_price) - (prediction.sqft * 150) + random.randint(-50000, 50000)
        trend_data.append({'sqft': s, 'price': p})
        
    context = {
        'prediction': prediction,
        'min_price': min_price,
        'max_price': max_price,
        'similar_houses': similar_houses,
        'trend_data': json.dumps(trend_data),
    }
    return render(request, 'predictor/result.html', context)

@csrf_exempt
def predict_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            location = data.get('location', 'Unknown')
            sqft = int(data.get('sqft', 0))
            bedrooms = int(data.get('bedrooms', 0))
            bathrooms = int(data.get('bathrooms', 0))
            floors = int(data.get('floors', 1))
            year_built = data.get('year_built')
            year_built = int(year_built) if year_built else None
            parking = data.get('parking') == 'true'
            furnishing = data.get('furnishing', 'Unfurnished')
            
            # Simple mock model for demonstration
            base_price = 50000
            if location.lower() in ['downtown', 'city center']:
                base_price += 100000
            elif location.lower() in ['suburb', 'residential']:
                base_price += 30000
                
            sqft_value = sqft * 150
            bed_value = bedrooms * 20000
            bath_value = bathrooms * 15000
            floor_value = floors * 10000
            parking_value = 15000 if parking else 0
            
            furnish_value = 0
            if furnishing == 'Fully Furnished':
                furnish_value = 25000
            elif furnishing == 'Semi-Furnished':
                furnish_value = 10000
                
            year_penalty = 0
            if year_built:
                age = 2026 - year_built
                year_penalty = max(0, age * 1000) # prevent negative penalty
            
            # Add some slight randomness to simulate ML
            random_factor = random.uniform(0.95, 1.05)
            predicted_price = (base_price + sqft_value + bed_value + bath_value + floor_value + parking_value + furnish_value - year_penalty) * random_factor
            
            # Confidence score drops if inputs are outside "normal" ranges
            confidence_score = 95.0
            if sqft > 5000 or sqft < 500: confidence_score -= 15.0
            if bedrooms > 6 or bedrooms < 1: confidence_score -= 10.0
            if bathrooms > 5 or bathrooms < 1: confidence_score -= 10.0
            if floors > 3: confidence_score -= 5.0
            if year_built and (year_built < 1900 or year_built > 2026): confidence_score -= 20.0
            
            # Bound confidence between 50 and 99
            confidence_score = max(50.0, min(99.9, confidence_score + random.uniform(-2, 2)))
            
            # Save to database
            prediction = Prediction.objects.create(
                location=location,
                sqft=sqft,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                floors=floors,
                year_built=year_built,
                parking=parking,
                furnishing=furnishing,
                predicted_price=predicted_price,
                confidence_score=confidence_score
            )
            
            return JsonResponse({
                'success': True,
                'prediction_id': prediction.id,
                'predicted_price': round(predicted_price, 2),
                'confidence_score': round(confidence_score, 1)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def delete_prediction(request, prediction_id):
    if request.method in ['POST', 'DELETE']:
        try:
            prediction = get_object_or_404(Prediction, id=prediction_id)
            prediction.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})
