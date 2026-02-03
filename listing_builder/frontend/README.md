# Marketplace Listing Automation - Frontend

Modern Next.js 14 frontend for the Marketplace Listing Automation System.

## Features

- **Dashboard** - Overview stats and quick actions
- **Products Management** - List, view, edit products
- **Import System** - Single and batch product import
- **AI Optimization** - Bulk AI-powered listing optimization
- **Publishing** - Export to multiple marketplaces
- **Dark Mode** - Professional dark theme (#1A1A1A, #121212)
- **Real-time Updates** - TanStack Query for live data

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS + shadcn/ui components
- **State Management:**
  - TanStack Query (server state)
  - Zustand (UI state - if needed)
- **HTTP Client:** Axios
- **Forms:** React Hook Form
- **Icons:** Lucide React

## Prerequisites

- Node.js 18+
- Backend API running at http://localhost:8000

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Setup Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── page.tsx              # Dashboard
│   │   ├── layout.tsx            # Root layout
│   │   ├── products/
│   │   │   ├── page.tsx          # Product list
│   │   │   ├── [id]/page.tsx    # Product detail
│   │   │   └── import/page.tsx  # Import form
│   │   ├── optimize/page.tsx    # Bulk optimization
│   │   └── publish/page.tsx     # Publishing page
│   │
│   ├── components/
│   │   ├── ui/                   # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── input.tsx
│   │   │   └── toaster.tsx
│   │   ├── layout/
│   │   │   └── Sidebar.tsx       # Main navigation
│   │   └── providers/
│   │       └── QueryProvider.tsx # React Query setup
│   │
│   ├── lib/
│   │   ├── api/                  # API client functions
│   │   │   ├── client.ts         # Axios setup
│   │   │   ├── products.ts       # Product endpoints
│   │   │   ├── import.ts         # Import endpoints
│   │   │   ├── ai.ts             # Optimization endpoints
│   │   │   └── export.ts         # Publishing endpoints
│   │   ├── hooks/                # Custom React hooks
│   │   │   ├── useProducts.ts    # Product data hooks
│   │   │   └── useToast.ts       # Toast notifications
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript types
│   │   └── utils.ts              # Utility functions
│   │
│   └── styles/
│       └── globals.css           # Global styles
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── README.md
```

## API Endpoints Used

The frontend connects to these backend endpoints:

### Products
- `GET /api/products` - List products with filters
- `GET /api/products/{id}` - Get single product
- `DELETE /api/products/{id}` - Delete product
- `GET /api/products/stats/summary` - Dashboard stats

### Import
- `POST /api/import/product` - Import single product
- `POST /api/import/batch` - Import batch of products
- `GET /api/import/job/{id}` - Get import job status

### AI Optimization
- `POST /api/ai/optimize/{id}` - Optimize product (full)
- `POST /api/ai/optimize-title/{id}` - Optimize title only
- `POST /api/ai/optimize-description/{id}` - Optimize description only
- `POST /api/ai/batch-optimize` - Batch optimization

### Publishing
- `POST /api/export/publish/{id}` - Publish single product
- `POST /api/export/bulk-publish` - Bulk publish
- `GET /api/export/marketplaces` - List marketplaces

## Key Features

### Dashboard
- Real-time stats (total products, pending, optimized, published)
- Quick action cards
- Average optimization score
- Recent activity

### Product Management
- List view with pagination
- Status filters (pending, optimized, published, error)
- Search functionality
- Individual product detail view
- Delete products

### Import System
- Single product import form
- Batch import (multiple products at once)
- Dynamic bullet points
- Optional fields (ASIN, brand, price, category)

### AI Optimization
- View all products pending optimization
- Bulk selection with checkboxes
- Select all / Deselect all
- Batch optimization trigger
- Real-time progress feedback

### Publishing
- Select marketplace (Amazon, eBay, etc.)
- Bulk product selection
- Publish confirmation
- Success/failure reporting

## Design System

### Colors
- Background: `#1A1A1A`
- Secondary: `#121212`
- Borders: `#333333`, `#2C2C2C`
- Text: White, neutral-300, neutral-400
- Accent: Context-based (green, blue, yellow, red)

### Components
- Cards with subtle borders
- Consistent spacing (Tailwind)
- Button variants (default, outline, ghost, destructive)
- Badge status indicators
- Toast notifications for feedback

### Typography
- Font: Inter (Google Fonts)
- Headings: Bold, white
- Body: Regular, gray-300/400
- Code: Mono, gray-400

## Testing

To test the frontend:

1. **Start Backend** (required):
   ```bash
   cd ../backend
   uvicorn main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   npm run dev
   ```

3. **Test Flow**:
   - Visit http://localhost:3000
   - Check dashboard stats load
   - Import a test product
   - Optimize the product
   - Publish to marketplace

## Development Notes

### Adding New Pages
1. Create page in `src/app/[route]/page.tsx`
2. Add link to `Sidebar.tsx`
3. Use existing components from `src/components/ui/`

### Adding New API Calls
1. Add function to appropriate `src/lib/api/*.ts` file
2. Create custom hook in `src/lib/hooks/` if needed
3. Use TanStack Query for data fetching

### Styling
- Use Tailwind classes
- Follow existing dark mode palette
- Reuse shadcn/ui components
- Keep consistent spacing

## Troubleshooting

### "Cannot connect to backend"
- Ensure backend is running: `curl http://localhost:8000/health`
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Verify CORS is enabled in backend

### "Products not loading"
- Check browser console for errors
- Verify backend API endpoints are working
- Check network tab for failed requests

### "Build errors"
- Run `npm run type-check` to find TypeScript errors
- Ensure all imports are correct
- Check for missing dependencies

## Production Build

```bash
npm run build
npm run start
```

The app will be optimized and served on port 3000.

## Future Enhancements

- [ ] Add authentication
- [ ] Real-time job progress updates
- [ ] Product image upload
- [ ] CSV export
- [ ] Advanced filters
- [ ] Keyboard shortcuts
- [ ] Bulk editing
- [ ] Marketplace-specific templates

## Contributing

Follow these guidelines:
- TypeScript strict mode
- File headers (location, purpose, NOT for)
- WHY comments (not WHAT)
- Files under 200 lines
- Dark mode design system

## License

Private - Internal use only
