# NDMG Task Manager

A professional enterprise task management platform combining visual management methodologies with artificial intelligence. Designed to accelerate development lifecycles through automated code reviews, streamlined pull request generation, and granular access controls.

## System Architecture

The ecosystem relies on a modular, decoupled architecture, operating through three main tiers:

1. Frontend (React / Vite)
A responsive interface implementing customized glassmorphism aesthetics. Features optimistic UI rendering using dnd-kit for seamless Kanban transitions, alongside robust Context API patterns for global state and role management.

2. Backend (Python / Flask)
A secure RESTful middleware layer intercepting core actions. Integrates with third-party providers (GitHub API, Groq AI) and enforces strict route-level authorization using custom decorators.

3. Database & BaaS (Supabase)
Relational PostgreSQL database managing complex many-to-many associations (participants, tickets). Relies heavily on Row Level Security (RLS) policies, Object Storage for CDN attachments, and Google OAuth 2.0 identity provisioning.

## Key Capabilities

- Advanced Kanban Board: Drag-and-drop mechanics with real-time status synchronization.
- Multi-Participant Attribution: Hierarchical role distribution directly within tickets.
- File Attachments: Secure native image and document uploads coupled with real-time rendering.
- Role-Based Access Control (RBAC): Dedicated administrative views limiting system manipulation strictly to authenticated database administrators.
- Automated Code Reviews (Groq AI): Direct integration with feature branches, outputting advanced technical analysis on git diffs before merging.
- GitHub Integration: Native capability to track, analyze, and open Pull Requests autonomously based on ticket progression.
- Analytical Dashboard: Automated computational views for Cycle Time and Lead Time metrics.

## Requirements

- Docker and docker-compose
- Node.js 18+ (for local frontend manipulation)
- Python 3.12+ (for local backend manipulation)
- A Supabase Project Instance
- Groq AI API Key
- GitHub Personal Access Token (classic with "repo" scope)

## Initialization Strategy

1. Repository Configuration
Clone the repository and structure your environment variables based on the example structure.

cp .env.example .env

2. Environment Mapping
Fill the required keys in your `.env` file at the root of the project:

SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
GROQ_API_KEY=...
FLASK_SECRET_KEY=...
GITHUB_TOKEN=...
GITHUB_REPO_OWNER=...
GITHUB_REPO_NAME=...

3. Database Seeding
Execute the SQL files located in the `/supabase` directory directly into your Supabase SQL Editor. Start with table schema and proceed to RLS configurations.

4. Container Deployment
Spin up the containerized architecture automatically:

docker-compose up -d --build

The frontend application will be exposed on localhost:3000, while the backend API rests on localhost:5000.

## Development Workflow

- All developers must branch off main utilizing the required identifier nomenclature: feature/NDMG-[ID]-[slug].
- Commits pushing a ticket into "In Review" or "Done" state automatically trigger webhook analysis.
- Supabase instances validate OAuth sessions using Google domain restrictions. Ensure team accounts belong to authorized organization domains.

## Security Constraints

Every API endpoint enforces strict JWT validation originating from Supabase Auth middleware. Attachments, metadata updates, and team reassignments undergo deep RLS verification prior to acknowledging table mutation requests. Do not expose your Supabase Service Role Key on the frontend under any circumstances.
