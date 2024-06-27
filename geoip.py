from argparse import ArgumentParser
from geoip2 import webservice
from pathlib import Path
from dotenv import dotenv_values

from validators.ip_address import ipv4, ipv6
from dataclasses import dataclass
from typing import Optional
from rich.console import Console
from rich.table import Table
import asyncio


@dataclass
class ip:
    ip: str
    country_iso: Optional[str]
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]


async def main() -> list[ip]:
    ip_list = []
    async with webservice.AsyncClient(
        env["ACCOUNT_ID"], env["LICENSE_KEY"], host="geolite.info"
    ) as client:
        for v in search_ips:
            response = await client.city(v)
            ip_list.append(
                ip(
                    v,
                    response.country.iso_code if response.country else None,
                    response.country.name if response.country else None,
                    (
                        response.subdivisions.most_specific.name
                        if response.subdivisions
                        else None
                    ),
                    response.city.name if response.city else None,
                )
            )

    return ip_list


args = ArgumentParser()
args.add_argument("IP", nargs="+", help="IP address(es) to look up")
args.add_argument(
    "--env",
    help="Environment file containing MaxMind account ID and license key",
    default=".env",
)
args = args.parse_args()

env_file = Path(args.env)

if not env_file.exists() or not env_file.is_file():
    raise FileNotFoundError(f"{args.env} is not a file")

env = dotenv_values(args.env)

if "ACCOUNT_ID" not in env or "LICENSE_KEY" not in env:
    raise ValueError(f"{args.env} must contain ACCOUNT_ID and LICENSE_KEY")

invalid_ips = []
search_ips = []
for v in args.IP:
    if not ipv4(v) and not ipv6(v):
        invalid_ips.append(v)
    else:
        search_ips.append(v)


geoip_list = asyncio.run(main())
table = Table(title="IP Geolocations")
table.add_column("IP")
table.add_column("Country ISO")
table.add_column("Country")
table.add_column("State")
table.add_column("City")

for ip in geoip_list:
    table.add_row(ip.ip, ip.country_iso, ip.country, ip.state, ip.city)

console = Console()
console.print(table)
