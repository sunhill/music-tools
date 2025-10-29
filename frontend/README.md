# Spotify Export Frontend

A React-based frontend for the Spotify Export application that displays your Spotify artists in a modern, responsive interface.
The frontend folder contains a React application written in TypeScript. It uses Material-UI (MUI) for UI components and theming, React Router for client-side routing, and Axios for API calls. The structure includes reusable components (such as ArtistCard), a main app component (App.tsx), and a clear separation of concerns. The app displays Spotify artists with features like search, sorting, pagination, and view toggling (grid/list). State management is handled with React Hooks. The project is set up for modern frontend development with npm scripts for building, testing, and running the app.


## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)
- A running instance of the Spotify Export backend (FastAPI server)

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd spotify-export
   ```

2. **Navigate to Frontend Directory**
   ```bash
   cd frontend
   ```

3. **Install Dependencies**
   ```bash
   npm install
   ```

4. **Start the Development Server**
   ```bash
   npm start
   ```
   This will start the development server on [http://localhost:3000](http://localhost:3000).

5. **Ensure Backend is Running**
   Make sure your FastAPI backend is running on `http://localhost:8001`. The frontend expects the following endpoints to be available:
   - `GET /artists` - Returns a list of Spotify artists

> **Important**: All npm commands must be run from the `frontend` directory, not the root project directory.

## Available Routes

- `/artists` - Displays a list of all Spotify artists
- `/` - Home page (redirects to /artists)

## Project Structure

```
spotify-export/
├── frontend/           # Frontend React application
│   ├── public/        # Static files
│   │   ├── index.html # HTML template
│   │   └── manifest.json # Web app manifest
│   ├── src/          # Source code
│   │   ├── App.tsx   # Main application component
│   │   ├── index.tsx # Application entry point
│   │   └── components/ # Reusable components
│   │       └── ArtistCard.tsx # Artist card component
│   ├── package.json  # Project dependencies and scripts
│   └── tsconfig.json # TypeScript configuration
└── ...               # Backend files
```

## Features

- Modern, responsive UI using Material-UI components
- Dark theme matching Spotify's aesthetic
- Artist cards displaying:
  - High-resolution artist image
  - Name
  - Genres
- Search functionality to filter artists
- Loading and error states
- TypeScript for type safety
- Client-side routing with React Router

## Available Scripts

All scripts must be run from the `frontend` directory:

```bash
cd frontend
npm start    # Runs the app in development mode
npm test     # Launches the test runner
npm run build # Builds the app for production
npm run eject # Ejects from Create React App
```

## Dependencies

- React 18
- Material-UI (MUI) for components
- Axios for API calls
- TypeScript for type safety
- React Router for client-side routing

## Development

The application uses:
- TypeScript for type safety
- Material-UI for components and theming
- Axios for API calls
- React Hooks for state management
- React Router for navigation

## Building for Production

To create a production build:

```bash
cd frontend
npm run build
```

This will create an optimized production build in the `build` folder.

## Troubleshooting

1. **CORS Issues**
   If you encounter CORS errors, ensure your backend has CORS enabled and is configured to accept requests from `http://localhost:3000`.

2. **Backend Connection**
   If the frontend can't connect to the backend, verify that:
   - The backend server is running on port 8001
   - The backend URL in `App.tsx` matches your backend configuration

3. **TypeScript Errors**
   If you see TypeScript errors, try:
   ```bash
   cd frontend
   npm install
   ```

4. **Command Not Found**
   If you get "command not found" errors, make sure you're in the `frontend` directory:
   ```bash
   cd frontend
   ```

5. **Routing Issues**
   If you encounter 404 errors when refreshing the page, ensure you're using the correct route paths:
   - `/artists` for the artists list
   - `/` for the home page

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 