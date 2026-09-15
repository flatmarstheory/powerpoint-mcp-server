"""Visual asset tools for Draw.io-compatible diagrams and web images."""
import base64
import json
import os
import re
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from xml.sax.saxutils import escape

from mcp.server.fastmcp import FastMCP
from PIL import Image, ImageDraw, ImageFont

import utils as ppt_utils


ASSET_ROOT = Path(os.getenv("PPT_ASSET_PATH", "/app/presentations/assets"))
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def _safe_name(value: str, fallback: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return (name[:100] or fallback)


def _asset_path(filename: str) -> Path:
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    return ASSET_ROOT / _safe_name(filename, f"asset_{uuid.uuid4().hex}")


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _render_diagram_png(nodes: List[Dict], edges: List[Dict], output_path: Path, title: str = "") -> None:
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#f8faf7")
    draw = ImageDraw.Draw(image)
    title_font = _font(38, True)
    node_font = _font(24, True)
    detail_font = _font(18)
    positions = {}

    if title:
        draw.text((60, 40), title, fill="#17231b", font=title_font)
    for index, node in enumerate(nodes):
        node_id = str(node.get("id", index + 1))
        x = int(node.get("x", 100 + (index % 4) * 360))
        y = int(node.get("y", 180 + (index // 4) * 250))
        node_width = int(node.get("width", 260))
        node_height = int(node.get("height", 120))
        x = max(30, min(x, width - node_width - 30))
        y = max(120, min(y, height - node_height - 30))
        positions[node_id] = (x, y, node_width, node_height)
        fill = node.get("color", "#dff28b")
        draw.rounded_rectangle((x, y, x + node_width, y + node_height), radius=18, fill=fill, outline="#344438", width=3)
        label = str(node.get("label", node_id))
        lines = [label[i:i + 23] for i in range(0, len(label), 23)] or [""]
        total_height = len(lines) * 30
        for line_index, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=node_font)
            draw.text((x + (node_width - (bbox[2] - bbox[0])) / 2, y + (node_height - total_height) / 2 + line_index * 30), line, fill="#17231b", font=node_font)
        if node.get("detail"):
            draw.text((x + 14, y + node_height - 29), str(node["detail"])[:32], fill="#526257", font=detail_font)

    for edge in edges:
        source = positions.get(str(edge.get("source")))
        target = positions.get(str(edge.get("target")))
        if not source or not target:
            continue
        start = (source[0] + source[2], source[1] + source[3] // 2)
        end = (target[0], target[1] + target[3] // 2)
        draw.line((start, end), fill="#607565", width=5)
        angle_x = end[0] - start[0]
        direction = 1 if angle_x >= 0 else -1
        arrow = [(end[0], end[1]), (end[0] - direction * 18, end[1] - 10), (end[0] - direction * 18, end[1] + 10)]
        draw.polygon(arrow, fill="#607565")
        if edge.get("label"):
            draw.text(((start[0] + end[0]) // 2, (start[1] + end[1]) // 2 - 28), str(edge["label"])[:30], fill="#526257", font=detail_font)

    image.save(output_path, format="PNG", optimize=True)


def _drawio_xml(nodes: List[Dict], edges: List[Dict], title: str = "") -> str:
    cells = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
    ]
    if title:
        cells.append(f'<mxCell id="title" value="{escape(title)}" style="text;html=1;fontSize=24;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="40" y="30" width="600" height="50" as="geometry"/></mxCell>')
    for index, node in enumerate(nodes):
        node_id = str(node.get("id", index + 1))
        x = int(node.get("x", 100 + (index % 4) * 360))
        y = int(node.get("y", 180 + (index // 4) * 250))
        node_width = int(node.get("width", 260))
        node_height = int(node.get("height", 120))
        label = escape(str(node.get("label", node_id)))
        color = escape(str(node.get("color", "#dff28b")))
        cells.append(f'<mxCell id="{escape(node_id)}" value="{label}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#344438;fontSize=18;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{node_width}" height="{node_height}" as="geometry"/></mxCell>')
    for index, edge in enumerate(edges):
        source = escape(str(edge.get("source", "")))
        target = escape(str(edge.get("target", "")))
        label = escape(str(edge.get("label", "")))
        cells.append(f'<mxCell id="edge_{index}" value="{label}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;" edge="1" parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    return '<?xml version="1.0" encoding="UTF-8"?><mxfile host="app.diagrams.net" modified="2026-09-15T00:00:00.000Z" agent="PowerPoint Studio"><diagram id="powerpoint-diagram" name="Page-1"><mxGraphModel><root>' + ''.join(cells) + '</root></mxGraphModel></diagram></mxfile>'


def register_visual_tools(app: FastMCP, presentations: Dict, get_current_presentation_id):
    @app.tool()
    def create_drawio_diagram(
        nodes: List[Dict],
        edges: List[Dict],
        title: str = "",
        output_name: str = "diagram",
        slide_index: Optional[int] = None,
        left: float = 1.0,
        top: float = 1.4,
        width: float = 8.0,
        height: float = 4.5,
        presentation_id: Optional[str] = None,
    ) -> Dict:
        """Create a Draw.io-compatible diagram from nodes and edges, render it to PNG, and optionally add it to a slide. Use this after the model has designed the diagram structure."""
        if not nodes:
            return {"error": "At least one node is required"}
        if len(nodes) > 40 or len(edges) > 80:
            return {"error": "Diagram limit is 40 nodes and 80 edges"}
        try:
            stem = _safe_name(output_name, "diagram")
            drawio_path = _asset_path(f"{stem}.drawio")
            png_path = _asset_path(f"{stem}.png")
            drawio_path.write_text(_drawio_xml(nodes, edges, title), encoding="utf-8")
            _render_diagram_png(nodes, edges, png_path, title)
            result = {
                "message": "Created Draw.io-compatible diagram and PNG render",
                "drawio_path": str(drawio_path),
                "image_path": str(png_path),
                "node_count": len(nodes),
                "edge_count": len(edges),
            }
            if slide_index is not None:
                pres_id = presentation_id if presentation_id is not None else get_current_presentation_id()
                if pres_id not in presentations:
                    return {"error": "No presentation is currently loaded or the specified ID is invalid"}
                pres = presentations[pres_id]
                if slide_index < 0 or slide_index >= len(pres.slides):
                    return {"error": f"Invalid slide index: {slide_index}"}
                ppt_utils.add_image(pres.slides[slide_index], str(png_path), left, top, width, height)
                result["slide_index"] = slide_index
                result["presentation_id"] = pres_id
            return result
        except Exception as error:
            return {"error": f"Failed to create diagram: {error}"}

    @app.tool()
    def search_web_images(query: str, limit: int = 5) -> Dict:
        """Search Wikimedia Commons for relevant reusable images without an API key. Returns image URLs and attribution metadata."""
        if not query.strip():
            return {"error": "Query is required"}
        limit = max(1, min(limit, 10))
        params = urllib.parse.urlencode({
            "action": "query", "format": "json", "generator": "search", "gsrsearch": query,
            "gsrnamespace": 6, "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size",
        })
        request = urllib.request.Request(f"{WIKIMEDIA_API}?{params}", headers={"User-Agent": "PowerPointStudio/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
        results = []
        for page in payload.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            mime = info.get("mime", "")
            url = info.get("url", "")
            if mime.startswith("image/") and url.startswith("https://upload.wikimedia.org/"):
                metadata = info.get("extmetadata", {})
                results.append({
                    "title": page.get("title", "").removeprefix("File:"),
                    "image_url": url,
                    "mime": mime,
                    "width": info.get("width"),
                    "height": info.get("height"),
                    "artist": metadata.get("Artist", {}).get("value", ""),
                    "license": metadata.get("LicenseShortName", {}).get("value", ""),
                    "source_page": f"https://commons.wikimedia.org/?curid={page.get('pageid')}",
                })
        return {"query": query, "source": "Wikimedia Commons", "results": results}

    @app.tool()
    def download_web_image(image_url: str, output_name: str = "web_image") -> Dict:
        """Download an image returned by search_web_images into the shared presentation assets folder for use with manage_image."""
        parsed = urllib.parse.urlparse(image_url)
        if parsed.scheme != "https" or parsed.netloc != "upload.wikimedia.org":
            return {"error": "Only HTTPS Wikimedia Commons image URLs are allowed"}
        request = urllib.request.Request(image_url, headers={"User-Agent": "PowerPointStudio/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            data = response.read(MAX_IMAGE_BYTES + 1)
        if not content_type.startswith("image/") or len(data) > MAX_IMAGE_BYTES:
            return {"error": "The response was not a supported image or exceeded the size limit"}
        path = _asset_path(f"{output_name}.png")
        path.write_bytes(data)
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception as error:
            path.unlink(missing_ok=True)
            return {"error": f"Downloaded file is not a valid image: {error}"}
        with Image.open(path) as image:
            image.convert("RGBA").save(path, format="PNG", optimize=True)
        return {"message": "Downloaded image", "image_path": str(path), "content_type": content_type, "bytes": len(data)}
