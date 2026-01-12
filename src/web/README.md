# SmartFileOrganizer Web UI

Modern, responsive web interface for SmartFileOrganizer built with React, TypeScript, and Material-UI.

## Features

- 🎨 **Modern UI**: Clean, intuitive interface with Material-UI components
- 🌓 **Dark/Light Mode**: Toggle between dark and light themes
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- ⚡ **Real-time Updates**: WebSocket-powered live scan progress
- 📊 **Dashboard**: Overview of system health, recent scans, and categories
- 🔍 **Scanner**: Interactive file scanning with progress tracking
- 📋 **Results**: Filterable and sortable file listing
- ⚙️ **Settings**: Configure AI provider, scan preferences, and more

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Python backend server running

### Development

1. Install dependencies:
```bash
cd src/web
npm install
```

2. Start the development server:
```bash
npm run dev
```

The UI will be available at `http://localhost:3000`

### Production Build

1. Build the production bundle:
```bash
npm run build
```

2. The built files will be in `dist/` directory

3. Start the Python backend to serve the UI:
```bash
smartfile serve
```

The UI will be available at `http://localhost:8001`

## Tech Stack

- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe code
- **Material-UI (MUI)**: Component library
- **Vite**: Fast build tool
- **Zustand**: Lightweight state management
- **Axios**: HTTP client
- **React Router**: Client-side routing

## Project Structure

```
src/web/
├── src/
│   ├── api/
│   │   └── client.ts          # API client
│   ├── components/
│   │   ├── Dashboard.tsx      # Home dashboard
│   │   ├── Scanner.tsx        # Scan interface
│   │   ├── Results.tsx        # Results view
│   │   ├── Settings.tsx       # Settings page
│   │   └── Layout.tsx         # Main layout
│   ├── utils/
│   │   └── store.ts           # Global state
│   ├── App.tsx                # Root component
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles
├── public/                    # Static assets
├── index.html                 # HTML template
├── package.json               # Dependencies
├── tsconfig.json              # TypeScript config
└── vite.config.ts             # Vite config
```

## API Integration

The UI communicates with the FastAPI backend via:

- **REST API**: For CRUD operations
- **WebSocket**: For real-time scan updates

All API endpoints are proxied through Vite during development.

## Accessibility

- Keyboard navigation support
- ARIA labels for screen readers
- High contrast support via theme
- Responsive font sizes

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

MIT License - see [LICENSE](../../LICENSE) for details.
