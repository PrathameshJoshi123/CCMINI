# 🔑 Test Credentials & Authentication Guide

## Quick Test Account

### Sample Login Credentials
```
Email: test@example.com
Password: Test123!
```

### Sample Register Data
```
Email: demo@notesllm.com
Password: Demo123!
Confirm Password: Demo123!
```

---

## 📝 Validation Rules

### Email Requirements
- Must be valid email format
- Example: `user@domain.com`

### Password Requirements
- **Minimum 8 characters**
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*)

### Valid Password Examples
```
Password123!
SecurePass1@
MyPass2024#
Demo123!
Test456$
```

### Invalid Password Examples
```
❌ password     (too short, no uppercase, no number, no special char)
❌ PASSWORD123  (no lowercase, no special char)
❌ Password     (no number, no special char)
❌ Pass123      (too short, no special char)
```

---

## 🧪 Testing Quick Guide

### 1. Register New Account
Navigate to: `http://localhost:5173/register`

```
Email: yourname@test.com
Password: YourPass123!
Confirm Password: YourPass123!
```

Click "Register" → Auto-redirects to Dashboard

### 2. Login to Existing Account
Navigate to: `http://localhost:5173/login`

```
Email: yourname@test.com
Password: YourPass123!
```

Click "Login" → Redirects to Dashboard

### 3. Test Multiple Accounts
```
Account 1:
Email: alice@test.com
Password: Alice123!

Account 2:
Email: bob@test.com
Password: Bob456@

Account 3:
Email: charlie@test.com
Password: Charlie789#
```

---

## 🔒 How Authentication Works

### Registration Flow
1. User fills registration form
2. Password must match confirmation
3. Frontend validates email & password format
4. POST `/register` to backend
5. Backend creates user account
6. Success → User logged in automatically
7. JWT token stored in localStorage
8. Redirected to Dashboard

### Login Flow
1. User enters email & password
2. Frontend validates format
3. POST `/login` to backend
4. Backend verifies credentials
5. Returns JWT token + user info
6. Token stored in localStorage
7. AuthContext updated
8. Redirected to Dashboard

### Protected Routes
- Dashboard, Document Detail, Chat pages require login
- If not logged in → Auto-redirect to Login page
- JWT token sent with every API request
- Token expires after 7 days (backend configured)

### Logout
- Click "Logout" in navbar
- JWT token removed from localStorage
- AuthContext cleared
- Redirected to Login page

---

## 🛠️ For Development/Testing

### Test Without Backend
If backend is not running, you'll see errors. The frontend expects:
- Backend at `http://localhost:8000`
- CORS enabled
- `/register` and `/login` endpoints

### Quick Test Script (Browser Console)
```javascript
// Check if user is logged in
localStorage.getItem('token')

// Check stored email
localStorage.getItem('email')

// Clear session (logout)
localStorage.removeItem('token')
localStorage.removeItem('email')
```

---

## 📧 Email Format Examples

### Valid Emails ✅
```
user@example.com
john.doe@company.co.uk
test123@domain.io
my.name+tag@email.com
```

### Invalid Emails ❌
```
notanemail
@domain.com
user@
user@domain
user @domain.com (space)
```

---

## 🔐 Password Validation Code

Located in: `src/utils/validation.ts`

```typescript
export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain an uppercase letter')
  .regex(/[a-z]/, 'Password must contain a lowercase letter')
  .regex(/[0-9]/, 'Password must contain a number')
  .regex(/[!@#$%^&*]/, 'Password must contain a special character');
```

---

## 🚀 Quick Start

### First Time Setup
```powershell
# 1. Start backend (separate terminal)
cd path/to/backend
uvicorn main:app --reload

# 2. Start frontend
cd notesllm-frontend
npm run dev

# 3. Open browser
# http://localhost:5173
```

### Register First Account
1. Click "Sign Up" on login page
2. Enter email: `you@test.com`
3. Enter password: `Test123!`
4. Confirm password: `Test123!`
5. Click "Register"
6. ✅ You're logged in!

### Upload Document & Chat
1. On Dashboard, click "Upload Document"
2. Select PDF file
3. Wait for processing (status updates automatically)
4. Click document card → View summary/mindmap/flashcards
5. Go to Chat page
6. Select your document
7. Ask questions!

---

## 💡 Tips

### Creating Strong Passwords
```
Formula: [Word][Number][Special][Word]
Examples:
- Coffee2024!Time
- Book@Reading123
- Music#Party456
```

### Remember Your Password
- Use a password manager
- Or write it down in a safe place during testing
- Backend stores hashed passwords (secure)

### Multiple Test Accounts
Create different accounts to test:
- User isolation (documents separate per user)
- Multiple concurrent sessions
- Chat with different document sets

---

## ⚠️ Important Notes

1. **Backend Required**: Frontend needs backend running to authenticate
2. **CORS**: Backend must allow `http://localhost:5173`
3. **MongoDB**: Backend needs MongoDB for user storage
4. **Token Expiry**: Tokens expire after 7 days (or backend config)
5. **Case Sensitive**: Passwords are case-sensitive
6. **No Password Reset**: Not implemented yet (add if needed)

---

## 🐛 Common Issues

### "Network Error" on Login
- ✅ Check backend is running: `http://localhost:8000`
- ✅ Check `VITE_API_BASE_URL` in `.env.local`
- ✅ Check browser console for CORS errors

### "Invalid Credentials"
- ✅ Check email format is correct
- ✅ Check password is correct (case-sensitive)
- ✅ Try registering new account

### "Password Requirements Not Met"
- ✅ Minimum 8 characters
- ✅ Include: Uppercase + lowercase + number + special char
- ✅ Example: `MyPass123!`

### Form Won't Submit
- ✅ All fields must be filled
- ✅ Red error messages must be cleared
- ✅ Passwords must match (register page)

---

## 📱 Testing Checklist

### Registration
- [ ] Valid email accepted
- [ ] Invalid email shows error
- [ ] Weak password shows error
- [ ] Passwords must match
- [ ] Successful register → Dashboard redirect
- [ ] Token stored in localStorage

### Login
- [ ] Correct credentials → Dashboard
- [ ] Wrong password → Error message
- [ ] Unknown email → Error message
- [ ] Form validation works
- [ ] Remember session after page refresh

### Protected Routes
- [ ] Dashboard requires login
- [ ] Document Detail requires login
- [ ] Chat requires login
- [ ] Not logged in → Redirect to Login

### Logout
- [ ] Logout button in navbar
- [ ] Clears token
- [ ] Redirects to login
- [ ] Can't access protected routes after logout

---

## 🎯 Ready-to-Use Test Credentials

Copy & paste these for quick testing:

### Test User 1
```
Email: alice@notesllm.com
Password: Alice2024!
```

### Test User 2
```
Email: bob@notesllm.com
Password: BobTest123@
```

### Test User 3
```
Email: demo@test.com
Password: Demo123!
```

### Your Custom Account
```
Email: ___________________
Password: ___________________
```

---

**Happy Testing! 🎉**

Remember: These are test credentials for development only.
In production, use secure, unique passwords!
