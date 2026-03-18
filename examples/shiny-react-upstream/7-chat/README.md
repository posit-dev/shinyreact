# AI Chat Example

**Note: This example very experimental. In the future, it will benefit from better integration with Ellmer (R) and Chatlas (Python).**

A modern AI chat application built with Shiny-React, featuring:

- **Frontend**: React with shadcn/ui components and Tailwind CSS
- **R Backend**: Shiny server with `ellmer` for LLM integration
- **Python Backend**: Shiny server with `chatlas` for LLM integration
- **Modern UI**: Professional chat interface with message bubbles, avatars, and smooth scrolling
- **Multi-modal**: Image upload and attachment support
- **Theming**: Multiple beautiful themes with dynamic switching

## Features

- 💬 Real-time bidirectional chat communication
- 🖼️ **Image attachments**: Drag-and-drop image uploads with preview
- 🎨 **Multiple themes**: 6 beautiful themes (Default, Paper, Cyberpunk, Glass, Terminal, Discord)
- 🎛️ **Theme switcher**: Dynamic theme switching with live preview
- 🔄 Message history and conversation state
- ⚡ Fast response handling with loading states
- 🎯 TypeScript for type safety
- 📱 Responsive design optimized for all screen sizes
- ✨ Smooth animations and glassmorphism effects

## Prerequisites

### For R Backend
```r
# Install required packages
install.packages(c("shiny", "ellmer"))
```

### For Python Backend
```bash
# Install required packages
pip install -r py/requirements.txt
# Or manually: pip install shiny chatlas python-dotenv
```

### API Keys
Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Build the Application
```bash
# Development build with watch mode
npm run watch

# Or one-time build
npm run build
```

### 3. Run Shiny Server

**For R Backend:**
```bash
R -e "options(shiny.autoreload = TRUE); shiny::runApp('r/app.R', port=8000)"
```

**For Python Backend:**
```bash
shiny run py/app.py --port 8000
```

### 4. Open Browser
Navigate to `http://localhost:8000`

## Development Workflow

1. **Start file watcher** (rebuilds on changes):
   ```bash
   npm run watch
   ```

2. **Run Shiny server** (choose R or Python):
   ```bash
   # R
   R -e "shiny::runApp('r/app.R', port=8000)"

   # Python
   shiny run py/app.py --port 8000
   ```

3. **Make changes** to React components in `srcts/` - they will rebuild automatically

4. **Backend changes** are auto-reloaded by Shiny

## Project Structure

```
examples/7-chat/
├── package.json            # Node.js dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── build.ts                # Custom build script with Tailwind CSS
├── components.json         # shadcn/ui configuration
├── srcts/                  # React TypeScript source
│   ├── main.tsx            # App entry point
│   ├── globals.css         # Tailwind + CSS variables + theme styles
│   ├── components/
│   │   ├── ChatInterface.tsx   # Main chat component with image support
│   │   └── ThemeSwitcher.tsx   # Theme selection dropdown
│   ├── contexts/
│   │   └── ThemeContext.tsx    # Theme management context
│   ├── components/ui/      # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── scroll-area.tsx
│   │   └── avatar.tsx
│   └── lib/
│       └── utils.ts        # Utility functions
├── r/                      # R Shiny backend
│   ├── app.R               # Main R application with ellmer
│   ├── shinyreact.R        # R functions for shiny-react
│   └── www/                # Built assets (auto-generated)
├── py/                     # Python Shiny backend
│   ├── app.py              # Main Python application with chatlas
│   ├── shinyreact.py       # Python functions for shiny-react
│   ├── requirements.txt    # Python dependencies
│   └── www/                # Built assets (auto-generated)
└── README.md               # This file
```

## Customization

### Themes and Appearance

The application includes 6 built-in themes:

- **Default**: Clean and minimal design
- **Paper**: Notebook-inspired with ink aesthetics
- **Cyberpunk**: Neon colors and electric vibes
- **Glass**: Frosted glass effects with transparency
- **Terminal**: Retro computing green-on-black
- **Discord**: Familiar Discord-like styling

**Switch themes at runtime** using the theme picker in the top-right corner.

**Add custom themes** by editing `srcts/contexts/ThemeContext.tsx` and `srcts/globals.css`.

### Image Attachments

The chat interface supports drag-and-drop image uploads:

- **Supported formats**: PNG, JPEG, GIF, WebP
- **Size limits**: Configurable in backend
- **Preview**: Images show in chat with thumbnails
- **Multi-image**: Support for multiple attachments per message

### Changing AI Models

**R (ellmer):**
```r
# In r/app.R, modify the chat initialization:
chat <- chat_openai("Your system prompt", model = "gpt-4o")

# Or use other providers:
chat <- chat_claude("Your system prompt")
chat <- chat_gemini("Your system prompt")
```

**Python (chatlas):**
```python
# In py/app.py, modify the chat initialization:
chat = ChatOpenAI(
    model="gpt-4o-mini",
    system_prompt="Your system prompt"
)

# Other providers support coming to chatlas
```

### Customizing the UI

- **Modify components**: Edit `srcts/components/ChatInterface.tsx`
- **Change themes**: Edit `srcts/contexts/ThemeContext.tsx` and `srcts/globals.css`
- **Add new shadcn components**: Run `npx shadcn@latest add <component-name>`
- **Custom styling**: All themes use CSS variables for easy customization

### Environment Variables

Both backends support these environment variables:

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic Claude API key (for ellmer)
- `GOOGLE_API_KEY`: Google Gemini API key (for ellmer)

## Troubleshooting

### API Key Issues
- Ensure your API key is set as an environment variable
- Check the console/terminal for error messages
- Verify the key has proper permissions

### Build Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clean build artifacts and rebuild
npm run clean
npm run build

# Check TypeScript errors
npx tsc --noEmit
```

### Theme Issues
If themes appear broken or don't switch properly:
```bash
# Rebuild with fresh Tailwind CSS
npm run clean
npm run build

# Check if CSS variables are loading
# Open DevTools → Elements → Check <html> element for theme classes
```

### Port Conflicts
Change the port if 8000 is in use:
```bash
# R
R -e "shiny::runApp('r/app.R', port=8001)"

# Python
shiny run py/app.py --port 8001
```

## License

MIT License - see the main shiny-react repository for details.
