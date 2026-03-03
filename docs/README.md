# Documentation Site

Professional documentation for FastAPI SSE Events library.

## 📁 Structure

```
docs/
├── index.html    # Main documentation page
├── styles.css    # Professional dark/light theme
├── script.js     # Interactive features
└── README.md     # This file
```

## ✨ Features

### 🎨 Professional Theme
- **Dark/Light Mode**: Toggle between GitHub-inspired dark and light themes
- **Responsive Design**: Optimized for desktop, tablet, and mobile
- **Modern Layout**: Sticky header, fixed sidebar navigation, table of contents

### 🔍 Navigation
- **Sidebar Search**: Filter documentation sections (Try Ctrl/Cmd + K)
- **Active Highlighting**: Current section highlighted in sidebar and TOC
- **Smooth Scrolling**: Seamless navigation between sections
- **Mobile Menu**: Hamburger menu for mobile devices

### 💻 Code Features
- **Syntax Highlighting**: Prism.js with professional color scheme
- **Copy Buttons**: One-click code copying with visual feedback
- **Multiple Languages**: Python, JavaScript, TypeScript, Bash, YAML, Nginx, Docker

### ⚡ Interactive Elements
- **Theme Toggle**: Switch themes (Ctrl/Cmd + /)
- **Back to Top**: Floating button appears on scroll
- **Keyboard Shortcuts**: Quick access to common actions
- **Smooth Animations**: Hover effects and transitions

## 🚀 Usage

### Local Development

Simply open `index.html` in your browser:

```bash
cd docs
open index.html  # macOS
# or
xdg-open index.html  # Linux
# or
start index.html  # Windows
```

### Using Python HTTP Server

```bash
cd docs
python3 -m http.server 8080
```

Then visit: http://localhost:8080

### Using Node.js

```bash
npx http-server docs -p 8080
```

### Production Deployment

#### GitHub Pages

1. Push to GitHub
2. Go to Settings → Pages
3. Set source to `/docs` folder
4. Visit `https://yourusername.github.io/fastapi-sse-events/`

#### Netlify

```bash
# netlify.toml (in project root)
[build]
  publish = "docs"
```

Deploy: `netlify deploy --prod`

#### Vercel

```bash
# vercel.json (in project root)
{
  "cleanUrls": true,
  "trailingSlash": false
}
```

Deploy: `vercel --prod`

#### Custom Server (Nginx)

```nginx
server {
    listen 80;
    server_name docs.example.com;
    root /path/to/project/docs;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 🎯 Customization

### Update Project Info

Edit `index.html`:

- Line 8: Update page title
- Line 20: Update GitHub URL
- Line 28: Update project name and logo
- Line 68: Update version badge
- Line 69: Update hero title
- Lines 220-230: Update footer links

### Change Color Theme

Edit `styles.css` variables (lines 8-43):

```css
:root {
  --accent-primary: #1f6feb;    /* Brand color */
  --accent-success: #238636;    /* Success green */
  --accent-warning: #9e6a03;    /* Warning yellow */
  /* ... customize other colors */
}
```

### Add New Sections

1. Add section to `index.html`:
```html
<section id="new-section" class="section">
  <h2 class="section-title">
    <i class="fas fa-icon"></i>
    New Section
  </h2>
  <p>Content here...</p>
</section>
```

2. Add to sidebar navigation (lines 50-90):
```html
<li><a href="#new-section"><i class="fas fa-icon"></i> New Section</a></li>
```

3. Add to table of contents (lines 740+):
```html
<a href="#new-section" class="toc-link">New Section</a>
```

## 📱 Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🔧 Dependencies

### External CDNs

- **Font Awesome 6.4.0**: Icons
- **Prism.js 1.29.0**: Syntax highlighting

All dependencies loaded from CDN - no build step required!

## ⌨️ Keyboard Shortcuts

- `Ctrl/Cmd + K`: Focus search
- `Ctrl/Cmd + /`: Toggle theme
- `Esc`: Clear search

## 📊 Analytics (Optional)

To add analytics, include your tracking code in `index.html` before `</head>`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 🎨 Design Philosophy

The documentation follows **GitHub's design system**:

- Professional dark theme as default
- High contrast for readability
- Clear hierarchy with typography
- Generous whitespace
- Subtle animations
- Mobile-first responsive design

## 📝 Content Guidelines

When adding new documentation:

1. **Use clear headings**: H2 for sections, H3 for subsections
2. **Add icons**: Use Font Awesome icons for visual interest
3. **Include examples**: Show code snippets with copy buttons
4. **Use info cards**: Highlight important information
5. **Keep it scannable**: Use lists, tables, and short paragraphs

## 🐛 Troubleshooting

### Styles not loading
- Check file paths are relative
- Verify `styles.css` is in same directory as `index.html`

### JavaScript not working
- Check browser console for errors
- Ensure `script.js` is loaded after DOM content

### Theme not persisting
- Check localStorage is enabled in browser
- Clear browser cache and try again

## 📄 License

Same as parent project (MIT).

## 🙏 Credits

- Icons: [Font Awesome](https://fontawesome.com/)
- Syntax Highlighting: [Prism.js](https://prismjs.com/)
- Design Inspiration: [GitHub](https://github.com/)

---

**Built with ❤️ for the FastAPI community**
