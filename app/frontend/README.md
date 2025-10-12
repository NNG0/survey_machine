# Survey Machine Frontend

An Angular-based web application for intelligent literature research powered by AI.

## 🏗️ Architecture Overview

The frontend is built using **Angular 19** with a standalone component architecture, utilizing reactive state management and service-based API communication.

### Technology Stack

- **Framework**: Angular 19 (Standalone Components)
- **Language**: TypeScript 5.7
- **Styling**: CSS with component-scoped styles
- **State Management**: Angular Signals + Custom Service Layer
- **HTTP Client**: RxJS-based observables
- **Markdown Rendering**: Marked.js
- **Build Tool**: Angular CLI

## 📂 Project Structure

```
src/
├── app/
│   ├── components/          # UI Components
│   │   ├── header/          # Navigation header
│   │   ├── footer/          # Page footer
│   │   ├── hero/            # Search interface with filters
│   │   ├── results/         # Paper search results display
│   │   ├── topics/          # Topic navigation
│   │   ├── collection/      # Saved papers collection
│   │   ├── paper-card/      # Individual paper card component
│   │   ├── drafts/          # Project/draft management
│   │   ├── draft-detail/    # Detailed draft editor
│   │   └── about/           # About page
│   │
│   ├── services/            # Business Logic Layer
│   │   ├── state/           # State Management
│   │   │   ├── app-state.service.ts    # Global app state
│   │   │   ├── article.store.ts        # Article/paper store
│   │   │   └── draft.store.ts          # Draft/project store
│   │   ├── restapiservice.service.ts   # Main API communication
│   │   ├── papers.service.ts           # Paper persistence
│   │   └── projects.service.ts         # Project/draft operations
│   │
│   ├── types/               # TypeScript Definitions
│   │   ├── models.ts        # Data models and interfaces
│   │   └── state.ts         # State-related types
│   │
│   ├── app.component.ts     # Root component
│   ├── app.config.ts        # App configuration
│   └── app.routes.ts        # Routing configuration
│
├── index.html               # Main HTML entry point
├── main.ts                  # Application bootstrap
└── styles.css               # Global styles
```

## 🔄 State Management

The application uses a **hybrid state management approach**:

### 1. **Signal-based State** (`AppStateService`)
- Utilizes Angular Signals for reactive state updates
- Manages workflow stages and request status
- Tracks history of state changes
- Handles workflow persistence

### 2. **Store Pattern** (`ArticleStore`, `DraftStore`)
- Specialized stores for domain-specific operations
- Handles CRUD operations on articles and drafts
- Coordinates with backend API for persistence
- Manages saved papers and draft content

### State Flow
```
User Action → Component → Store/Service → API Call → State Update → UI Re-render
```

## 🔌 API Integration

### Backend Communication
The app communicates with a Python FastAPI backend through `RESTAPIService`:

**Key Endpoints:**
- **Literature Search**: `/api/search` - AI-powered paper discovery
- **Workflow Management**: `/api/workflow` - State persistence
- **Paper Storage**: `/api/papers` - Paper database operations
- **Draft Management**: `/api/drafts` - Survey draft operations

### Request Pipeline Stages
The application follows a multi-stage workflow (`RequestStages`):

1. `FINDING_LITERATURE` (100) - Search for relevant papers
2. `PARSE_PAPERS` (200) - Extract paper content
3. `CREATING_KEY_QUESTIONS` (50) - Generate research questions
4. `ADJUST_KEY_QUESTIONS` (300) - Refine questions
5. `EXTRACT_RELEVANT_RESULTS_FROM_PAPERS` (500) - Extract findings
6. `CREATING_DRAFT_HEADINGS` (600) - Generate outline
7. `FILLING_DRAFT_CONTENT` (700) - Fill content
8. `FINISHED` (999) - Complete

## 🎨 Key Components

### Hero Component
- **Purpose**: Main search interface
- **Features**: 
  - Query input with filters (year, citations, keywords)
  - Advanced semantic search toggle
  - Loading state management

### Results Component
- **Purpose**: Display search results
- **Features**:
  - Paper cards with relevance scores
  - Save/unsave functionality
  - Filter and sort capabilities

### Collection Component
- **Purpose**: Manage saved papers
- **Features**:
  - Persistent paper storage
  - Remove/organize papers
  - Export capabilities

### Drafts Component
- **Purpose**: Survey draft management
- **Features**:
  - Create/edit/delete drafts
  - Markdown editor
  - AI-assisted content generation

## 🚀 Development

### Prerequisites
- Node.js 20+
- npm or yarn
- Docker (for containerized deployment)

### Local Development

```bash
# Install dependencies
npm install

# Start dev server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build frontend

# With hot reloading (requires volume mount)
# Add to docker-compose.yml:
volumes:
  - ./app/frontend/src:/app/src
```

## 🔧 Configuration

### Angular Configuration
- **Output Path**: `dist/`
- **Port**: 4200
- **Base HREF**: `/`

### API Configuration
Backend API URL is configured in the services layer (default: `http://localhost:8001`)

## 📝 Key Features

✅ **AI-Powered Literature Search** - Semantic search with relevance scoring  
✅ **Advanced Filtering** - Year, citations, keywords, subject area  
✅ **Paper Collection** - Save and organize research papers  
✅ **Draft Management** - Create AI-assisted survey drafts  
✅ **Workflow Persistence** - Resume research sessions  
✅ **Markdown Support** - Rich text editing for drafts  
✅ **Responsive Design** - Mobile-friendly interface  

## 🔒 Security Considerations

- No sensitive data stored in frontend
- API calls use relative paths
- CORS configured on backend
- Input validation on forms

## 📦 Build & Deployment

### Production Build
```bash
npm run build
```

### Docker Deployment
```bash
docker build -t survey-frontend .
docker run -p 4200:4200 survey-frontend
```

## 🐛 Debugging

- **Dev Tools**: Angular DevTools browser extension
- **Console Logging**: Enabled in development mode
- **RxJS Debugging**: Use `tap()` operators for stream inspection

## 📚 Further Documentation

- [Angular Documentation](https://angular.dev)
- [RxJS Documentation](https://rxjs.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
