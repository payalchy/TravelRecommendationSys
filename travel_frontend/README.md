# Travel Recommendation System - Frontend

A React-based frontend for the Travel Recommendation System with Django backend API integration.

## Project Structure

```
travel_frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/           # Page components (Recommendations, Profile, etc.)
│   ├── services/        # API service layer
│   ├── styles/          # CSS/styling
│   ├── App.jsx
│   └── index.jsx
├── public/
├── package.json
└── vite.config.js
```

## Setup

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

```bash
cd travel_frontend
npm install
```

### Development Server

```bash
npm run dev
```

Runs on `http://localhost:5173` (Vite default)

### Build for Production

```bash
npm run build
```

## API Integration

The frontend communicates with the Django backend at `http://localhost:8000`

### Key Endpoints
- `POST /api/recommendations/` - Get destination recommendations
- `GET /api/destination-geocode/` - Geocode destination names

## Technology Stack

- **React** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Router** - Navigation

## Next Steps

1. Install dependencies
2. Configure API base URL
3. Build recommendation search component
4. Display destination results
5. Add user profile integration
