# PowerPoint MCP Server - FastMCP Edition

A comprehensive MCP server for PowerPoint manipulation using python-pptx, built with [FastMCP](https://github.com/jlowin/fastmcp).

## Features

This server provides **32 specialized tools** organized into 11 focused modules:

### Presentation Management (7 tools)
- Create/open/save presentations
- Create from template files with layout preservation
- Get presentation info and properties
- Set core properties (title, author, etc.)

### Content Management (6 tools)
- Add slides with custom layouts and backgrounds
- Manage text with advanced formatting
- Add and enhance images
- Extract text content
- Populate placeholders
- Add bullet points

### Template Operations (7 tools)
- 31+ pre-built slide templates
- Auto-generate presentations from topics
- Apply templates to existing slides
- Optimize text for readability
- 8 color schemes & 5 typography styles

### Structural Elements (4 tools)
- Add tables with custom styling
- 20+ shape types (basic, flowchart, polygons)
- Add lines and connectors
- Add text boxes

### Professional Design (3 tools)
- Apply professional themes
- Add charts (column, bar, line, pie)
- Advanced text formatting

### Specialized Features (5 tools)
- Hyperlink management
- Chart data updates
- Connector lines/arrows
- Slide master management
- Slide transitions

## Transport Modes

This server supports two transport modes:

- **STDIO (default)**: For Claude Desktop and MCP clients. Communication via stdin/stdout.
- **HTTP**: For web applications, APIs, and cloud deployment. RESTful endpoints with streaming support.

## Quick Start

### Option 1: Claude Desktop (STDIO mode) - Recommended

#### 1. Install dependencies
```bash
cd powerpoint-mcp-server

# Install with uv (recommended)
uv sync

# Or manually install dependencies
uv pip install chuk-mcp-server python-pptx Pillow fonttools
```

#### 2. Test the server
```bash
# Test that it works
uv run python server.py --help
```

#### 3. Configure Claude Desktop

Add to your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "powerpoint": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/remicarvalot/project_pro/powerpoint-mcp-server",
        "run",
        "python",
        "server.py"
      ]
    }
  }
}
```

**Important**: Replace `/Users/remicarvalot/project_pro/powerpoint-mcp-server` with the actual path to your installation.

#### 4. Restart Claude Desktop

Your PowerPoint MCP server will now be available with all 32 tools!

### Option 2: Web/API (HTTP mode)

Perfect for web applications and cloud deployment.

```bash
# Start HTTP server on port 8000
uv run python server.py --http

# Or specify custom port/host
uv run python server.py --port 8000 --host 0.0.0.0
```

Test with curl:
```bash
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Option 3: Docker (Production Deployment)

Docker automatically runs the server in HTTP mode. The compose stack also includes a local web GUI backed by OpenAI.

#### Using docker-compose (easiest)
```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY to your key
docker compose up --build
```

Open the GUI at <http://localhost:8080>. The MCP HTTP API remains available at <http://localhost:8000>.

The OpenAI key is passed only to the `powerpoint-gui` container. The GUI loads the MCP tool schemas from the server, lets OpenAI choose tools, and forwards each tool call to the local MCP API. Set `OPENAI_MODEL` in `.env` to use a different model.

To stop the stack:

```bash
docker compose down
```

#### Or build manually
```bash
# Build the image
docker build -t powerpoint-mcp-server .

# Run the container
docker run -p 8000:8000 powerpoint-mcp-server
```

## Usage Examples

Once connected to Claude Desktop, you can ask:

```
"Create a new PowerPoint presentation about AI"
"Add a title slide with the title 'Machine Learning 101'"
"Apply the modern_blue color scheme"
"Add a slide with a chart showing quarterly results"
"Create a presentation from the business template"
"Save the presentation as 'my-presentation.pptx'"
```

## Available Tools (32 Total)

### Presentation Management
1. `create_presentation` - Create new blank presentation
2. `create_presentation_from_template` - Create from template file
3. `open_presentation` - Open existing .pptx
4. `save_presentation` - Save to disk
5. `get_presentation_info` - Get metadata
6. `get_template_file_info` - Get template details
7. `set_core_properties` - Set title, author, etc.

### Content Management
8. `add_slide` - Add slides with layouts
9. `get_slide_info` - Get slide details
10. `extract_slide_text` - Extract text from slide
11. `extract_presentation_text` - Extract all text
12. `populate_placeholder` - Fill placeholders
13. `add_bullet_points` - Add formatted bullets
14. `manage_text` - Unified text operations
15. `manage_image` - Add and enhance images

### Template Operations
16. `list_slide_templates` - List 31+ templates
17. `apply_slide_template` - Apply template to slide
18. `create_slide_from_template` - Create from template
19. `create_presentation_from_templates` - Build from sequence
20. `get_template_info` - Get template details
21. `auto_generate_presentation` - AI-style generation
22. `optimize_slide_text` - Optimize readability

### Structural Elements
23. `add_table` - Add formatted tables
24. `add_shape` - Add 20+ shape types
25. `add_line` - Draw lines
26. `add_textbox` - Add text boxes

### Professional Design
27. `apply_professional_design` - Apply themes
28. `add_chart` - Add professional charts
29. `format_text_advanced` - Advanced formatting

### Specialized Features
30. `update_chart_data` - Update chart data
31. `manage_hyperlinks` - Manage hyperlinks
32. `add_connector` - Add connector lines
33. `manage_slide_masters` - Access slide masters
34. `manage_slide_transitions` - Set transitions

### Utility Tools
- `list_presentations` - List all loaded presentations
- `switch_presentation` - Switch between presentations
- `get_server_info` - Get server capabilities

## Template System

The server includes 31+ pre-built slide templates with:

**Standard Templates:**
- title_slide, agenda_slide, text_with_image
- two_column_text, key_metrics_dashboard
- chart_comparison, thank_you_slide
- data_table_slide, full_image_slide
- three_column_layout, quote_testimonial
- process_flow, and more...

**Color Schemes (8):**
1. modern_blue
2. corporate_gray
3. elegant_green
4. warm_red
5. pastel_dream
6. nature_earth
7. neon_vibrant
8. minimalist_mono

**Typography Styles (5):**
1. modern_sans
2. elegant_serif
3. tech_modern
4. organic_flow
5. brutalist_bold

## Environment Configuration

Set custom template directories:

```bash
# Unix/Mac
export PPT_TEMPLATE_PATH="/path/to/templates:/another/path"

# Windows
set PPT_TEMPLATE_PATH="C:\templates;D:\more-templates"
```

## Development

### Install dev dependencies
```bash
uv sync --dev
```

### Run tests
```bash
uv run pytest
```

### Type checking
```bash
uv run mypy server.py
```

### Linting
```bash
uv run ruff check .
```

## Command-Line Options

```bash
# Force STDIO mode (default)
python server.py --stdio
python server.py --transport=stdio

# Force HTTP mode
python server.py --http
python server.py --port 8000
python server.py --host 0.0.0.0
python server.py --transport=http

# Enable debug logging
python server.py --debug
python server.py --log-level debug
```

## Architecture

This server combines:
- **FastMCP** - Lightweight and fast MCP framework
- **Office-PowerPoint-MCP-Server** - 32 specialized PowerPoint tools
- **Modular Design** - 11 tool modules + 7 utility modules (3,068 lines)
- **Advanced Features** - Templates, themes, auto-generation, optimization

## Project Structure

```
powerpoint-mcp-server/
├── server.py                      # Main server file
├── pyproject.toml                 # Project configuration
├── tools/                         # 11 tool modules
│   ├── presentation_tools.py      # Presentation management
│   ├── content_tools.py           # Content operations
│   ├── template_tools.py          # Template system
│   ├── structural_tools.py        # Shapes, tables, lines
│   ├── professional_tools.py      # Design & themes
│   ├── chart_tools.py             # Chart operations
│   ├── hyperlink_tools.py         # Hyperlink management
│   ├── connector_tools.py         # Connectors
│   ├── master_tools.py            # Slide masters
│   └── transition_tools.py        # Transitions
├── utils/                         # 7 utility modules
│   ├── template_utils.py          # Template system (1,142 lines)
│   ├── design_utils.py            # Design tools (688 lines)
│   ├── content_utils.py           # Content ops (578 lines)
│   ├── validation_utils.py        # Validation (322 lines)
│   └── presentation_utils.py      # Presentation ops (216 lines)
├── slide_layout_templates.json    # 31+ template definitions
├── Dockerfile                     # Docker configuration
└── docker-compose.yml             # Docker Compose setup
```

## Contributing

This project combines:
- [ChukMCPServer](https://github.com/chrishayuk/chuk-mcp-server) - MCP framework
- [Office-PowerPoint-MCP-Server](https://github.com/yourusername/Office-PowerPoint-MCP-Server) - PowerPoint tools

See individual repositories for contribution guidelines.

## License

MIT License - See LICENSE file for details.

## Version

**2.3.0** - FastMCP Edition with full PowerPoint capabilities (Fixed tool schema issues)

## Support

For issues:
- ChukMCPServer: https://github.com/chrishayuk/chuk-mcp-server/issues
- PowerPoint features: https://github.com/yourusername/Office-PowerPoint-MCP-Server/issues
