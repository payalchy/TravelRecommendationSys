# Google Maps API Setup

This project now uses Google Maps Geocoding API for accurate destination coordinate lookups. Here's how to set it up:

## Step 1: Get a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Geocoding API**:
   - Search for "Geocoding API" in the search bar
   - Click on it and enable it
4. Go to **Credentials** in the left sidebar
5. Click **Create Credentials** → **API Key**
6. Copy your API key

## Step 2: Set Up the API Key

You have two options:

### Option A: Environment Variable (Recommended for Production)
```bash
# On Windows PowerShell:
$env:GOOGLE_MAPS_API_KEY = "your-api-key-here"

# On Windows Command Prompt:
set GOOGLE_MAPS_API_KEY=your-api-key-here

# On Linux/Mac:
export GOOGLE_MAPS_API_KEY="your-api-key-here"
```

Then run your Django server:
```bash
python manage.py runserver
```

### Option B: Direct Configuration (Quick Testing)
Edit `config/settings.py` and add your API key:
```python
GOOGLE_MAPS_API_KEY = "your-api-key-here"
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Verify It Works

Once you have the API key set up, new destinations added or updated will automatically fetch coordinates from Google Maps for better accuracy.

To update existing destinations with Google Maps coordinates, run:
```bash
python manage.py fill_missing_coordinates --force
```

## Cost Considerations

- **Free Tier**: 25,000 requests per month
- Typical usage: 1 request per new/updated destination
- Costs: $0.007 per request after free tier

## Fallback Behavior

If Google Maps API is not configured or fails:
- The system will automatically fall back to **OpenStreetMap Nominatim API** (free, slower, less accurate)
- This ensures the app continues to work even without a paid API key

## Support

For more information:
- [Google Maps Geocoding API Docs](https://developers.google.com/maps/documentation/geocoding)
- [Django Settings Documentation](https://docs.djangoproject.com/en/6.0/topics/settings/)
