# Piyu ImgExtract - Premium Image Extractor

**Piyu ImgExtract** is a powerful and modern web application designed to extract images from any public website effortlessly. Built with a robust Flask backend and a sleek, responsive frontend, it offers a premium user experience for designers, developers, and content creators who need to gather visual assets quickly.

## 🚀 Features

*   **Universal Extraction**: Enter any public URL to scan and extract images automatically.
*   **Smart Parsing**: Handles standard `<img>` tags, CSS background images, and Open Graph meta tags.
*   **Premium UI/UX**:
    *   Modern, dark-themed interface (with Light mode toggle).
    *   Responsive design for all devices.
    *   Smooth animations and transitions.
*   **Advanced Controls**:
    *   **Selection Support**: Select specific images or select all.
    *   **Bulk Download**: Download selected images as a verified ZIP archive.
    *   **Proxy Support**: Bypass CORS restrictions for direct image viewing and downloading.
*   **Pricing Tiers**: Dedicated pricing page showcasing 'Starter' and 'Professional' plans.

## 🛠️ Tech Stack

**Backend**
*   **Python 3.x**
*   **Flask**: Micro web framework.
*   **BeautifulSoup4 & lxml**: High-performance HTML parsing.
*   **Requests**: HTTP library for fetching web content.
*   **Zipfile**: For generating downloadable archives on the fly.

**Frontend**
*   **HTML5 & CSS3**: Semantic markup with modern CSS variables, Flexbox, and Grid.
*   **JavaScript (ES6+)**: Dynamic interactions, Fetch API for asynchronous requests.
*   **Font Awesome**: For scalable vector icons.
*   **Google Fonts**: 'Space Grotesk' for headings and 'Inter' for body text.

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Piyu242005/Piyu-ImgExtract.git
    cd Piyu-ImgExtract
    # (Or navigate to the downloaded folder)
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```

5.  **Access the Website**
    Open your browser and navigate to:
    ```
    http://127.0.0.1:5000
    ```

## 📖 Usage

1.  **Home Page**: Paste a valid URL (e.g., `https://unsplash.com`) into the input field.
2.  **Extract**: Click the "Extract Images" button. The app will analyze the target site.
3.  **Review**: Extracted images will appear in a grid.
4.  **Select & Download**:
    *   Click images to select/deselect them.
    *   Use "Select All" for bulk actions.
    *   Click "Download Selected" to get a ZIP file.
    *   Use the individual download button on card hover for single files.
5.  **Premium Plans**: Visit the "Go Premium" link to view pricing options.

## 💰 Pricing Plans

*   **Starter (₹350/month)**: Ideal for individuals. Includes single site extraction and up to 10k images.
*   **Professional (₹2499/month)**: Best for teams. Unlimited extraction, API access, and priority support.

## 📂 Project Structure

```
TT/
├── app.py              # Main Flask application entry point
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css   # Main stylesheet (Dark/Light mode, Responsiveness)
│   └── js/
│   │   └── script.js   # Frontend logic (Fetch, DOM manipulation)
└── templates/
    ├── index.html      # Home page template
    └── pricing.html    # Pricing page template
```

## 🖼️ Website Screenshots

### About Us
![About Us](About%20Us.jpeg)

### Dashboard
![Dashboard](Dashboard.jpeg)

### Features
![Features](Features.jpeg)

### Pricing
![Pricing](Pricing.jpeg)

### How the Website Works
![Website Works](Website%20Works.jpeg)

## 📄 License

© 2025 Piyu ImgExtract. All Rights Reserved To Piyush Ramteke.
