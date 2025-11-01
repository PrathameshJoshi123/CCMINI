# NotesLLM Frontend

A production-ready React + TypeScript frontend for **NotesLLM**, an AI-powered document processing and chat application. Upload PDF documents, get AI-generated summaries, interactive mind maps, flashcards, and chat with your documents using RAG (Retrieval-Augmented Generation).

![NotesLLM Screenshot](https://via.placeholder.com/800x400?text=NotesLLM+Dashboard)

## ✨ Features

- **🔐 Secure Authentication**: JWT-based authentication with protected routes
- **📄 Document Management**: Upload and manage PDF documents with real-time processing status
- **🤖 AI-Generated Content**:
  - **Summaries**: Concise document summaries with copy/download functionality
  - **Mind Maps**: Interactive visual knowledge graphs with React Flow
  - **Flashcards**: Study mode with card flipping and shuffle features
- **💬 RAG-Powered Chat**: Ask questions about your documents with source citations
- **📱 Responsive Design**: Works beautifully on desktop, tablet, and mobile
- **⚡ Real-time Updates**: Live polling for document processing status
- **🎨 Modern UI**: Clean interface built with Tailwind CSS and Headless UI patterns
- **🔔 Toast Notifications**: User-friendly feedback for all actions
- **🧪 Fully Tested**: Unit tests with Vitest and E2E tests with Playwright

## 🛠️ Tech Stack

### Core
- **React 18** - UI library
- **TypeScript 5** - Type safety
- **Vite** - Fast build tool

### UI/Styling
- **Tailwind CSS 3** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library
- **Clsx** - Conditional class names
- **Sonner** - Toast notifications
- **Framer Motion** - Smooth animations

### State & Data
- **TanStack Query v5** (React Query) - Server state management
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **Axios** - HTTP client

### Routing & Navigation
- **React Router v6** - Client-side routing

### Visualization
- **React Flow** - Interactive mind map visualization
- **React Dropzone** - File upload with drag & drop

### Testing
- **Vitest** - Unit testing
- **React Testing Library** - Component testing
- **Playwright** - End-to-end testing

### Code Quality
- **ESLint** - Linting
- **Prettier** - Code formatting
- **TypeScript** - Strict type checking

## 📦 Installation

### Prerequisites
- **Node.js** 18+ and npm/yarn
- Backend API running on `http://localhost:8000` (or configure `VITE_API_BASE_URL`)

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd notesllm-frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   
   Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_POLLING_INTERVAL=5000
   VITE_MAX_FILE_SIZE=52428800
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

   The app will open at `http://localhost:5173`

## 🚀 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server at http://localhost:5173 |
| `npm run build` | Build for production (outputs to `dist/`) |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint to check code quality |
| `npm run lint:fix` | Fix ESLint errors automatically |
| `npm run format` | Format code with Prettier |
| `npm test` | Run unit tests with Vitest |
| `npm run test:ui` | Run tests with Vitest UI |
| `npm run test:e2e` | Run end-to-end tests with Playwright |
| `npm run type-check` | Check TypeScript types without emitting files |

## 📂 Project Structure

```
notesllm-frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── auth/        # Authentication components
│   │   ├── common/      # Reusable UI components (Button, Modal, etc.)
│   │   ├── documents/   # Document-related components
│   │   ├── generated/   # Generated content viewers
│   │   ├── chat/        # Chat interface components
│   │   └── layout/      # Layout components (Navbar, Layout)
│   ├── contexts/        # React contexts (Auth)
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components (routes)
│   ├── services/        # API service layer
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions
│   ├── config/          # Configuration constants
│   ├── tests/           # Test files
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # App entry point
│   └── index.css        # Global styles
├── tests/
│   └── e2e/             # End-to-end tests
├── .env.example         # Environment variables template
├── .env.local           # Local environment variables (git-ignored)
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
├── playwright.config.ts # Playwright test configuration
└── README.md            # This file
```

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |
| `VITE_POLLING_INTERVAL` | Document status polling interval (ms) | `5000` |
| `VITE_MAX_FILE_SIZE` | Maximum upload file size (bytes) | `52428800` (50MB) |

## 🎯 Usage

### 1. Authentication

#### Register a New Account
1. Navigate to `/register`
2. Enter email and password (must be 8+ characters with uppercase, lowercase, and number)
3. Confirm password
4. Click "Create Account"

#### Login
1. Navigate to `/login`
2. Enter email and password
3. Click "Sign in"

### 2. Upload Documents

1. From the Dashboard, click "Upload Document"
2. Drag & drop a PDF file or click to browse
3. Click "Upload Document"
4. Status will update automatically: `UPLOADING` → `PROCESSING` → `COMPLETED`

### 3. View Generated Content

1. Click on any completed document from the Dashboard
2. View tabs:
   - **Summary**: Read AI-generated summary, copy or download
   - **Mind Map**: Explore interactive knowledge graph
   - **Flashcards**: Study with flip cards

### 4. Chat with Documents

1. Navigate to Chat page
2. Select one or more completed documents (or leave unselected to search all)
3. Type your question
4. View AI response with source citations (document name, page number, relevance score)

## 🧪 Testing

### Unit Tests

Run unit tests with Vitest:
```bash
npm test
```

Run with UI:
```bash
npm run test:ui
```

### E2E Tests

Install Playwright browsers (first time only):
```bash
npx playwright install
```

Run E2E tests:
```bash
npm run test:e2e
```

Run E2E tests in headed mode:
```bash
npx playwright test --headed
```

## 🏗️ Building for Production

1. **Build the project:**
   ```bash
   npm run build
   ```

2. **Preview the production build:**
   ```bash
   npm run preview
   ```

3. **Deploy:**
   - The `dist/` folder contains the production-ready static files
   - Deploy to Vercel, Netlify, AWS S3 + CloudFront, or any static hosting service
   - Ensure environment variables are set in your deployment platform

### Deployment Example (Vercel)

```bash
npm install -g vercel
vercel --prod
```

## 🔌 API Integration

The frontend integrates with 7 backend endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | Create new user account |
| `/login` | POST | Authenticate and get JWT token |
| `/users/me` | GET | Get current user details |
| `/documents/upload` | POST | Upload PDF document |
| `/documents` | GET | List all user documents |
| `/documents/:id/generated` | GET | Get generated content for a document |
| `/chat` | POST | Chat with documents using RAG |

See API service files in `src/services/` for implementation details.

## 🐛 Troubleshooting

### Backend Connection Issues
- Ensure backend is running on the correct port
- Check `VITE_API_BASE_URL` in `.env.local`
- Verify CORS is enabled on the backend

### File Upload Fails
- Check file is PDF format
- Verify file size is under 50MB (or `VITE_MAX_FILE_SIZE`)
- Ensure backend `/documents/upload` endpoint is working

### TypeScript Errors
- Run `npm run type-check` to see all type errors
- Ensure all dependencies are installed: `npm install`

### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## 📝 License

This project is built as part of the NotesLLM application.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API integration guide

## 🎉 Acknowledgments

- Built with React, TypeScript, and Vite
- UI components inspired by modern design systems
- Icons by Lucide
- Visualization powered by React Flow

---

**Made with ❤️ for NotesLLM**
