# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Strictly adhere to DRY, SOLID, KISS and YAGNI principles!

## Commands

Development:

- `npm run dev` - Start Vite development server with hot reload
- `npm run build` - TypeScript compilation + Vite production build
- `npm run build:pwa` - Production PWA build
- `npm run preview` - Preview production build locally
- `npm run serve:pwa` - Serve PWA build on port 5000
- `npm run lint` - ESLint with TypeScript support

## Architecture

Sensylate is a React PWA for CSV-based portfolio analysis and strategy visualization. It connects to a FastAPI backend for data retrieval and portfolio updates.

### Core Architecture

**State Management**: React Context pattern with `AppContext` centralizing:

- File selection (`selectedFile`)
- View mode (`table` vs `text`)
- CSV data cache (`csvData`)
- Loading/error states
- Update status tracking

**Data Flow**:

1. `api.ts` handles HTTP requests with in-memory caching for offline support
2. Custom hooks (`useCSVData`, `useFileList`, `usePortfolioUpdate`) manage async operations
3. Context providers wrap the app for state distribution

**Component Structure**:

- `App.tsx` - Root component with provider hierarchy
- `components/` - Reusable UI components (DataTable, FileSelector, etc.)
- `context/` - React Context providers (App state, Offline detection)
- `hooks/` - Custom hooks for data fetching and business logic
- `services/` - API layer with offline caching
- `utils/` - CSV parsing utilities using PapaParse

### Key Technologies

- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Build**: Vite with React plugin + PWA plugin
- **Data**: @tanstack/react-table for advanced table features
- **HTTP**: Axios with proxy to localhost:8000
- **CSV**: PapaParse for parsing
- **PWA**: vite-plugin-pwa with Workbox for caching strategies

### API Integration

Backend API endpoints (proxied through Vite):

- `GET /api/data/list/strategies` - List available CSV files
- `GET /api/data/csv/{filePath}` - Fetch CSV data
- `POST /api/scripts/update-portfolio` - Update portfolio data

### Offline Support

The app includes comprehensive offline capabilities:

- In-memory caching of file lists and CSV data
- Service worker caching for static assets
- Network-first strategy for API calls with cache fallback
- Offline detection with user notifications
