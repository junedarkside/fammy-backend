# System Patterns

## System Architecture

- The TravelApp project follows a microservices architecture.
- Key services include:
    - User authentication service
    - Tour search service
    - Booking service
    - Wholesale management service

## Key Technical Decisions

- Use Django for the backend framework.
- Use React for the frontend framework.
- Use PostgreSQL for the database.

## Design Patterns in Use

- Model-View-Controller (MVC) pattern for the backend.
- Component-based architecture for the frontend.

## Component Relationships

- The frontend interacts with the backend through REST APIs.
- The backend services communicate with each other through message queues.

## Critical Implementation Paths

- User registration and login.
- Tour search and booking.
- Wholesale tour creation and management.
