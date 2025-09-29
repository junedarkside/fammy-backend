# Project Overview

This is a Django project for a travel application. It consists of three main Django apps: `Accounts`, `tours`, and `wholesale`.

*   **`Accounts`**: Manages user accounts.
*   **`tours`**: Manages tours, including categories, types, and promotions. It provides a RESTful API for managing tours.
*   **`wholesale`**: Synchronizes data from external wholesale providers. It is designed to be extensible and support multiple providers.

The project uses the following technologies:

*   **Django**: The main web framework.
*   **Django REST Framework**: For building RESTful APIs.
*   **PostgreSQL**: The primary database.
*   **Celery**: For asynchronous task processing.
*   **Redis**: As a Celery message broker and cache.
*   **Docker**: For containerization.

## Building and Running

### Prerequisites

*   Docker
*   Docker Compose
*   Python 3.10+
*   pip

### Local Development (without Docker)

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run database migrations:**

    ```bash
    python manage.py migrate
    ```

3.  **Start the development server:**

    ```bash
    python manage.py runserver
    ```

### Docker Development

1.  **Build and run the containers:**

    ```bash
    docker-compose up --build
    ```

2.  **Run database migrations:**

    ```bash
    docker-compose exec web python manage.py migrate
    ```

The application will be available at [http://localhost:8000](http://localhost:8000).

## Development Conventions

*   The project follows the standard Django project structure.
*   The `wholesale` app uses a service-oriented architecture to interact with external APIs.
*   The `APIServiceFactory` allows for easy extension to support new wholesale providers.
*   The `DataSyncService` contains the business logic for data synchronization.
*   The project uses `python-decouple` to manage environment variables. Configuration is stored in a `.env` file.
*   The `wholesale` app's views are currently commented out, so the data synchronization functionality is not exposed via the API. To enable it, uncomment the views in `wholesale/views.py` and the URLs in `wholesale/urls.py`.
