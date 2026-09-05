# Mnemos MCP — remote serving (Smithery)
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY core ./core
COPY site ./site

RUN pip install --no-cache-dir .[mcp]

ENV PORT=8000
ENV MNEMOS_DB=/data/memory.db
ENV SITE_DIR=/app/site

EXPOSE 8000

# Site at /, agent chat at /chat, streamable MCP at /mcp
CMD ["mnemos", "mcp", "--http"]
