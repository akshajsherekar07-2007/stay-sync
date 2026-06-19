# StaySync

StaySync is a modern, responsive student accommodation platform designed to seamlessly connect students with verified property owners. Built with a focus on real-time availability and smooth user experiences, it offers secure authentication, role-based access, and a streamlined booking and hold management system.

## 🌟 Key Features

### For Students
*   **Browse & Filter**: Easily search for properties, filtering by location, amenities, and availability.
*   **Bed Holds**: Request to hold a specific bed for up to 24 hours while finalizing details. 
*   **Waitlists**: Join waitlists for beds that are currently occupied and get notified when they become available.
*   **Wishlist**: Save favorite properties to your "Saved Properties" for quick access later.
*   **Dashboard**: A dedicated overview to track active holds, saved properties, and account notifications.

### For Property Owners
*   **Property Management**: Add and manage properties, including detailed hierarchies (Floors -> Rooms -> Beds).
*   **Hold Approvals**: Review, approve, or reject bed hold requests from students in real-time.
*   **Occupancy Tracking**: Monitor your portfolio's performance with metrics on total properties and occupancy rates.
*   **Dashboard**: A comprehensive, fluid SaaS-style dashboard to manage daily operations efficiently.

### General Features
*   **Role-Based Authentication**: Secure JWT-based authentication with refresh token rotation for Students and Owners.
*   **Modern UI/UX**: A clean, aesthetic, and fully responsive layout with seamless light/dark mode toggling.

---

## 🛠 Tech Stack

### Frontend
*   **Framework**: React (with Vite)
*   **Language**: TypeScript
*   **State Management**: Zustand (Global), TanStack Query (Server State)
*   **Forms & Validation**: React Hook Form, Zod
*   **Styling**: CSS Modules (Custom modern SaaS-like design system)
*   **Icons**: Lucide React

### Backend
*   **Framework**: FastAPI (Python)
*   **ORM & Database**: SQLAlchemy (Async), Alembic (Migrations)
*   **Database**: PostgreSQL (Hosted on Supabase)
*   **Storage**: Supabase Storage (for property images and avatars)

---

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites
*   Node.js (v18+)
*   Python (3.10+)
*   Docker & Docker Compose (optional, for local DB)
*   Supabase Account (for remote DB & Storage)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your `.env` file with your Database and JWT credentials.
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file and configure your API URL:
   ```env
   VITE_API_URL=http://localhost:8000/api/v1
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

---

## 📂 Project Structure

```text
StaySync/
├── backend/                  # FastAPI backend
│   ├── app/                  
│   │   ├── api/              # API routes (v1)
│   │   ├── core/             # Config, security, and constants
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Business logic layer
│   │   └── repositories/     # Database interaction layer
│   └── alembic/              # Database migrations
└── frontend/                 # React frontend
    ├── src/
    │   ├── components/       # Reusable UI components
    │   ├── features/         # Domain-driven feature modules (auth, dashboard, owner, properties)
    │   ├── layouts/          # Page layouts (Root, Dashboard, Auth)
    │   ├── services/         # API client and requests
    │   └── stores/           # Zustand state stores
    └── public/               # Static assets
```

---

## 📝 License

This project is licensed under the MIT License.
