from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from defusedxml.ElementTree import fromstring, ParseError
from defusedxml.common import DefusedXmlException
app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

MAX_SCAN_BYTES = 1024 * 1024
@app.post("/api/scans/preview")
async def preview_scan(request: Request):
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_SCAN_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File exceeds maximum allowed size of 1MiB."
            )
            
        body.extend(chunk)
    if not body:
        raise HTTPException(
            status_code=400,
            detail="The file is empty"
        )
    try:
        root = fromstring(bytes(body),
                          forbid_dtd=True,
                          forbid_entities=True,
                          forbid_external=True)
    except DefusedXmlException:
        raise HTTPException(
            status_code=400,
            detail="Blocked XML feature."
        )
    except ParseError:
        raise HTTPException(
            status_code=400,
            detail="Malformed XML."
        )
    if root.tag != "nmaprun" or root.get("scanner") != "nmap":
        raise HTTPException(
            status_code=400,
            detail="Expected an Nmap XML file."
        )
    return{
           "status": "parsed",
           "received_bytes": len(body),
           "host_count": len(root.findall("host"))
        }