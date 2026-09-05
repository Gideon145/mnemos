# Mnemos MCP — remote serving (Smithery)
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY core ./core

RUN pip install --no-cache-dir .[mcp]

ENV PORT=8000
ENV MNEMOS_DB=/data/memory.db

EXPOSE 8000

# Streamable HTTP MCP endpoint at /mcp for Smithery and remote clients
CMD ["mnemos", "mcp", "--http"]
