# API Integration Guide - NotesLLM Frontend

This document explains how the frontend integrates with the backend API.

## 📡 API Client Setup

### Base Configuration

Location: `src/services/api.ts`

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

The API client is built with Axios and includes:
- **Request Interceptor**: Automatically adds JWT token to all requests
- **Response Interceptor**: Handles 401 errors globally (redirects to login)

## 🔐 Authentication Flow

### 1. Register User

**Service**: `src/services/auth.service.ts`

```typescript
authService.register({ email, password })
```

- **Endpoint**: `POST /register`
- **Request**: `{ email: string, password: string }`
- **Response**: `{ email: string, created_at: string }`
- **Usage**: `Register.tsx` component

### 2. Login User

```typescript
authService.login(email, password)
```

- **Endpoint**: `POST /login`
- **Request**: Form-urlencoded with `username` (email) and `password`
- **Response**: `{ access_token: string, token_type: 'bearer' }`
- **Side Effects**: 
  - Stores JWT in localStorage
  - Stores email in localStorage
- **Usage**: `Login.tsx` and `AuthContext`

### 3. Get Current User

```typescript
authService.getCurrentUser()
```

- **Endpoint**: `GET /users/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{ email: string, created_at: string }`
- **Usage**: `AuthContext` to verify authentication

### 4. Logout

```typescript
authService.logout()
```

- **Action**: Clears localStorage (token + email)
- **Side Effect**: User redirected to login

## 📄 Document Management

### 1. Upload Document

**Service**: `src/services/documents.service.ts`

```typescript
documentsService.uploadDocument(file, onProgress)
```

- **Endpoint**: `POST /documents/upload`
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file` (PDF file)
- **Response**: 
  ```typescript
  {
    message: string,
    document_id: string,
    filename: string,
    status: ProcessingStatus
  }
  ```
- **Progress**: Callback receives `{ loaded, total }`
- **Usage**: `FileUploader.tsx` and `useUpload` hook

### 2. Get All Documents

```typescript
documentsService.getDocuments()
```

- **Endpoint**: `GET /documents`
- **Response**: Array of documents
  ```typescript
  {
    _id: string,
    user_id: string,
    original_filename: string,
    local_path: string,
    processing_status: 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED',
    uploaded_at: string
  }[]
  ```
- **Usage**: `Dashboard.tsx` and `useDocuments` hook
- **Polling**: Automatically refetched when documents are processing

### 3. Get Single Document

```typescript
documentsService.getDocument(documentId)
```

- **Implementation**: Filters from all documents
- **Usage**: `DocumentDetail.tsx` page

### 4. Get Generated Content

```typescript
documentsService.getGeneratedContent(documentId)
```

- **Endpoint**: `GET /documents/:documentId/generated`
- **Response**: Array of generated content
  ```typescript
  {
    _id: string,
    document_id: string,
    user_id: string,
    content_type: 'SUMMARY' | 'MINDMAP' | 'FLASHCARDS',
    content_data: SummaryData | MindMapData | FlashcardsData,
    created_at: string
  }[]
  ```
- **Usage**: `DocumentDetail.tsx` to display summary, mind map, flashcards

## 💬 Chat / RAG

### Send Chat Message

**Service**: `src/services/chat.service.ts`

```typescript
chatService.sendMessage(query, documentIds)
```

- **Endpoint**: `POST /chat`
- **Request**: 
  ```typescript
  {
    query: string,
    document_ids: string[]  // Empty array searches all documents
  }
  ```
- **Response**:
  ```typescript
  {
    answer: string,
    sources: [{
      document_id: string,
      page: number,
      score?: number  // Relevance score 0-1
    }]
  }
  ```
- **Usage**: `Chat.tsx` and `useChat` hook

## 🔄 React Query Integration

### Query Keys

Defined in `src/config/constants.ts`:

```typescript
QUERY_KEYS = {
  DOCUMENTS: 'documents',
  DOCUMENT: 'document',
  GENERATED: 'generated',
  USER: 'user',
}
```

### Documents Query

```typescript
useQuery({
  queryKey: [QUERY_KEYS.DOCUMENTS],
  queryFn: documentsService.getDocuments,
})
```

- **Refetch**: Manual via `refetchDocuments()`
- **Invalidation**: After successful upload
- **Polling**: Enabled when documents are processing

### Generated Content Query

```typescript
useQuery({
  queryKey: [QUERY_KEYS.GENERATED, documentId],
  queryFn: () => documentsService.getGeneratedContent(documentId),
  enabled: !!documentId,
})
```

- **Dependency**: Only runs when `documentId` exists
- **Cache**: Cached per document ID

### Upload Mutation

```typescript
useMutation({
  mutationFn: documentsService.uploadDocument,
  onSuccess: () => {
    queryClient.invalidateQueries([QUERY_KEYS.DOCUMENTS]);
  }
})
```

- **Invalidation**: Refetches documents list on success
- **Progress**: Updates via callback

### Chat Mutation

```typescript
useMutation({
  mutationFn: (query) => chatService.sendMessage(query, selectedDocuments),
  onMutate: (query) => {
    // Optimistically add user message
  },
  onSuccess: (response) => {
    // Add AI response with sources
  }
})
```

- **Optimistic Updates**: User message shown immediately
- **Error Handling**: Error message added to chat

## 🔁 Polling Strategy

Location: `src/hooks/usePolling.ts`

```typescript
usePolling(status, callback, options)
```

### How It Works

1. **Trigger**: Starts when status is `UPLOADING` or `PROCESSING`
2. **Interval**: Every 5 seconds (configurable)
3. **Stop Conditions**:
   - Status becomes `COMPLETED` or `FAILED`
   - 2 minutes elapsed (timeout)
4. **Cleanup**: Automatically clears intervals

### Usage Example

```typescript
const { data: documents } = useDocuments();
const refetch = useRefetchDocuments();

const hasProcessing = documents?.some(
  doc => doc.processing_status === 'PROCESSING'
);

usePolling(
  hasProcessing ? 'PROCESSING' : 'COMPLETED',
  refetch,
  {
    enabled: hasProcessing,
    onComplete: () => toast.success('Document processed!'),
  }
);
```

## 🛡️ Error Handling

### API Errors

All API errors are caught and handled:

```typescript
try {
  await authService.login(email, password);
} catch (error: any) {
  const message = error.response?.data?.detail || 'Login failed';
  toast.error(message);
}
```

### 401 Unauthorized

Handled globally in API interceptor:

```typescript
interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      storage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Network Errors

```typescript
catch (error: any) {
  if (error.message === 'Network Error') {
    toast.error('Unable to connect to server');
  }
}
```

## 🔒 Token Management

### Storage

Location: `src/utils/storage.ts`

```typescript
storage.getToken()      // Get JWT
storage.setToken(token) // Store JWT
storage.removeToken()   // Clear JWT
storage.clear()         // Clear all auth data
```

### Injection

Automatic via Axios interceptor:

```typescript
config.headers.Authorization = `Bearer ${token}`;
```

### Validation

AuthContext checks token on mount:

```typescript
useEffect(() => {
  if (authService.isAuthenticated()) {
    fetchUser();
  }
}, []);
```

## 📊 Type Safety

All API types defined in `src/types/api.types.ts`:

- Request interfaces (e.g., `RegisterRequest`)
- Response interfaces (e.g., `LoginResponse`)
- Domain models (e.g., `Document`, `GeneratedContent`)
- Enums (e.g., `ProcessingStatus`, `ContentType`)

## 🧪 Testing API Integration

### Mock Services

```typescript
vi.mock('@/services/auth.service', () => ({
  authService: {
    login: vi.fn().mockResolvedValue({
      access_token: 'mock-token',
      token_type: 'bearer',
    }),
  },
}));
```

### Test Queries

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

render(
  <QueryClientProvider client={queryClient}>
    <Dashboard />
  </QueryClientProvider>
);
```

## 🚀 Best Practices

1. **Always use service layer**: Never call axios directly in components
2. **Use React Query**: For all server state management
3. **Handle errors**: Show user-friendly messages
4. **Type everything**: Use TypeScript interfaces for all API data
5. **Optimistic updates**: Show immediate feedback to users
6. **Loading states**: Show spinners/skeletons during requests
7. **Invalidate queries**: After mutations that change server data
8. **Clean up**: Clear timers, abort requests on unmount

## 📝 Adding New Endpoints

1. **Define types** in `src/types/api.types.ts`
2. **Create service function** in appropriate service file
3. **Create custom hook** if needed
4. **Use in component** with React Query
5. **Add error handling** and loading states
6. **Test** integration

## 🔍 Debugging API Calls

### Browser DevTools

1. **Network Tab**: See all requests/responses
2. **React Query DevTools**: View query cache and status
3. **Console**: Log errors and responses

### Common Issues

- **CORS errors**: Check backend CORS configuration
- **401 errors**: Token expired or invalid
- **Network errors**: Backend not running
- **404 errors**: Wrong endpoint URL

---

**For more details, see the service files in `src/services/` and type definitions in `src/types/`**
