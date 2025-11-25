# ProGet URLs

This document lists all HTTP endpoints used by the cleanup tool, grouped by purpose (login, listing repositories, querying images, tagging, deleting).
Useful for debugging, extending the tool, or onboarding new developers.

## 1. Authentication
**POST** `/log-in`

**Purpose:** Authenticate and create a login session.
**Method:** POST
Form fields:
- Username
- Password
- button ("Log In")


## 2. List All Container Repositories
**GET** `/containers?skip=0&take=1000`

**Purpose:** Retrieve the list of all container repositories in ProGet UI.
**Method:** GET

## 3. List Images in a Repository
**GET** `/containers/repositories/<feed>/<repo>/images`

Example:
/containers/repositories/mycompany/api-service/images

**Purpose:** Retrieve all images (tagged + untagged) for a specific repository.  
**Method:** GET

Must extract:
- image digest (sha256:...)
- tag names (if any)

Untagged images appear as “(untagged)” in the UI.

## Endpoint Summary Table
| Purpose           | Method | URL                                             | Notes                           |
| ----------------- | ------ | ----------------------------------------------- | ------------------------------- |
| Login             | POST   | `/log-in`                                       | Required to get session cookies |
| List repositories | GET    | `/containers?skip=0&take=1000`                  | UI HTML page                    |
| List images       | GET    | `/containers/repositories/<feed>/<repo>/images` | Parse HTML                      |
