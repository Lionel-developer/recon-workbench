from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from defusedxml.ElementTree import fromstring, ParseError
from defusedxml.common import DefusedXmlException
from ipaddress import ip_address

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
def extract_hosts(root):
    hosts = []
    for host in root.findall("host"):
        addresses = []
        for address in host.findall("address"):
            address_type = address.get("addrtype")
            
            if address_type not in ("ipv4", "ipv6"):
                continue
            try:
                parsed = ip_address(address.get("addr", ""))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail= "A host contains an invalid IP address."
                )
            if address_type != f"ipv{parsed.version}":
                raise HTTPException(
                    status_code=400,
                    detail="An IP address has the wrong address type."
                )
            addresses.append(str(parsed))
        if not addresses:
            raise HTTPException(
                status_code=400,
                detail="A host has no IP addresses."
            )
        status = host.find("status")
        hosts.append({
            "addresses": addresses,
            "status": (
                status.get("state", "unknown")
                if status is not None else "unknown"
            )
        })
    return hosts
        
        

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
    hosts = extract_hosts(root)
    return{
           "status": "parsed",
           "received_bytes": len(body),
           "host_count": len(hosts),
              "hosts": hosts
        }