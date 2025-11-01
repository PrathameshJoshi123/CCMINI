# NotesLLM Frontend - Quick Start Guide

## 🚀 Getting Started

Follow these steps to get the NotesLLM frontend up and running on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** version 18 or higher ([Download](https://nodejs.org/))
- **npm** (comes with Node.js) or **yarn**
- **Git** (optional, for cloning)

Check your versions:
```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 9.0.0 or higher
```

### Step 1: Navigate to Project Directory

```bash
cd notesllm-frontend
```

### Step 2: Install Dependencies

This will install all required packages including React, TypeScript, Tailwind CSS, React Query, and more.

```bash
npm install
```

**Note:** Installation may take 2-5 minutes depending on your internet connection.

### Step 3: Configure Environment Variables

Create a `.env.local` file in the project root:

```bash
# On Windows (PowerShell)
Copy-Item .env.example .env.local

# On macOS/Linux
cp .env.example .env.local
```

Edit `.env.local` if needed (default values work with standard backend setup):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_POLLING_INTERVAL=5000
VITE_MAX_FILE_SIZE=52428800
```

### Step 4: Start Development Server

```bash
npm run dev
```

You should see output like:
```
  VITE v5.4.5  ready in 523 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Step 5: Open in Browser

Navigate to **http://localhost:5173** in your web browser.

You should see the NotesLLM login page! 🎉

---

## ✅ Verification Steps

### Test the Application

1. **Register a new account:**
   - Click "Sign up"
   - Enter email and strong password
   - Click "Create Account"

2. **Login:**
   - Enter your credentials
   - Click "Sign in"

3. **Upload a document:**
   - Click "Upload Document"
   - Select a PDF file
   - Wait for processing

4. **Explore features:**
   - View generated summary, mind map, and flashcards
   - Navigate to Chat page
   - Ask questions about your documents

---

## 🛠️ Common Issues & Solutions

### Issue: Port 5173 is already in use

**Solution:** Kill the process using the port or change the port:

```bash
# Change port in vite.config.ts
server: {
  port: 3000,  # Use a different port
}
```

### Issue: Backend connection failed

**Error:** "Network Error" or API requests failing

**Solution:**
1. Ensure backend is running at `http://localhost:8000`
2. Check CORS settings on backend
3. Verify `VITE_API_BASE_URL` in `.env.local`

### Issue: Module not found errors

**Solution:** Clear cache and reinstall:

```bash
# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Issue: TypeScript errors

**Solution:** TypeScript errors are expected until dependencies are installed. After running `npm install`, they should resolve. If issues persist:

```bash
npm run type-check
```

---

## 📦 Production Build

To create a production-ready build:

```bash
npm run build
```

Output will be in the `dist/` folder. Preview it locally:

```bash
npm run preview
```

---

## 🧪 Running Tests

### Unit Tests
```bash
npm test
```

### E2E Tests (First time setup)
```bash
# Install Playwright browsers
npx playwright install

# Run tests
npm run test:e2e
```

---

## 🔧 Development Tools

### Code Formatting
```bash
npm run format
```

### Linting
```bash
npm run lint
npm run lint:fix  # Auto-fix issues
```

### Type Checking
```bash
npm run type-check
```

---

## 📁 Project Structure Overview

```
notesllm-frontend/
├── src/
│   ├── pages/           # Login, Register, Dashboard, DocumentDetail, Chat
│   ├── components/      # Reusable UI components
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API integration
│   ├── types/           # TypeScript definitions
│   ├── utils/           # Helper functions
│   ├── contexts/        # React Context (Auth)
│   └── config/          # Constants
├── public/              # Static assets
├── tests/               # E2E tests
├── .env.local           # Environment variables
└── package.json         # Dependencies
```

---

## 🎯 Next Steps

1. **Connect to Backend:** Ensure your backend API is running
2. **Register an Account:** Create your first user
3. **Upload Documents:** Try uploading a PDF
4. **Explore Features:** Test summaries, mind maps, flashcards, and chat

---

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Vite Guide](https://vitejs.dev/guide/)
- [React Query Docs](https://tanstack.com/query/latest)

---

## 💡 Tips

- **Hot Reload:** Changes to source files will automatically reload the browser
- **Browser DevTools:** Use React DevTools and React Query DevTools for debugging
- **Network Tab:** Check API requests in browser developer tools
- **Console Errors:** Always check browser console for errors

---

## 🤝 Need Help?

- Check the main README.md for detailed documentation
- Review API integration in `src/services/`
- Check TypeScript types in `src/types/`
- Open an issue if you encounter bugs

---

**Happy Coding! 🚀**
