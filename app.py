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

def extract_open_ports(host):
    ports = []
    for port in host.findall("ports/port"):
        try:
            number = int(port.get("portid", ""))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="A port has an invalid port number."
            )
        if not 0 <= number <= 65535:
            raise HTTPException(
                status_code=400,
                detail="Invalid port number detected. Must be between 0 and 65535."
            )
        protocol = port.get("protocol")
        if protocol not in ("tcp", "udp", "sctp"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported port protocol detected."
            )
        state = port.find("state")
        if state is None or not state.get("state"):
            raise HTTPException(
                status_code=400,
                detail="A port has no state."
            )
        if state.get("state") != "open":
            continue
        service = port.find("service")
        details = service.attrib if service is not None else {}
        
        ports.append({
            "port": number,
            "protocol": protocol,
            "service": details.get("name") or "unknown",
            "product": details.get("product", ""),
            "version": details.get("version", ""),
        })
    return ports

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
            ),
            "ports": extract_open_ports(host)
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
                          forbid_dtd=False,
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