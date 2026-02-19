# TruCar / VEMAG.mes Frontend

This is the frontend application for TruCar, built with **Vue 3** and the **Quasar Framework**.

## 🛠 Tech Stack

-   **Framework**: Quasar (Vue 3, Vite)
-   **State Management**: Pinia
-   **Router**: Vue Router
-   **HTTP Client**: Axios
-   **Charts**: ECharts, ApexCharts
-   **Maps**: Leaflet
-   **Mobile**: Capacitor (Android/iOS)
-   **Desktop**: Electron

## 🚀 Setup & Installation (Manual)

### 1. Prerequisites

-   Node.js v18+ (LTS)
-   NPM or Yarn

### 2. Install Dependencies

```bash
# Using Yarn (Recommended)
yarn install

# Or using NPM
npm install
```

### 3. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env.development
```

Edit `.env.development` and set your API URL:

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### 4. Start Development Server

```bash
quasar dev
```

This will start the development server at [http://localhost:9000](http://localhost:9000).

## 🏗 Building for Production

To build the application for production (SPA):

```bash
quasar build
```

The output will be in the `dist/spa` directory.

### Building for other platforms

-   **Mobile (Android)**: `quasar build -m capacitor -T android`
-   **Desktop (Electron)**: `quasar build -m electron`

## 🧹 Linting & Formatting

```bash
# Lint files
yarn lint

# Format files
yarn format
```

## 📂 Structure

-   `src/`: Application source code
    -   `assets/`: Static assets (images, fonts)
    -   `boot/`: Boot files (plugins, libraries)
    -   `components/`: Vue components
    -   `layouts/`: Page layouts
    -   `pages/`: Application pages (views)
    -   `router/`: Routing configuration
    -   `stores/`: Pinia stores (state management)
    -   `App.vue`: Root component
-   `src-capacitor/`: Mobile app configuration
-   `src-electron/`: Desktop app configuration
