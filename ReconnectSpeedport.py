
#CONFIG - Set your speedport password here
device_password = ""              # The device password for login
speedport_url = "http://speedport.ip/"    # The URL to the Speedport Smart Configurator
Sleeptime = 5                             # If the Reconnect doesn't work, change the number to 10 and then try again

# DO NOT CHANGE ANYTHING BELOW THIS LINE

import argparse
import asyncio
import logging
import sys
import aiohttp
from speedport.speedport import Speedport

_LOGGER = logging.getLogger("speedport")


def set_logger(args):
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    if args["debug"]:
        _LOGGER.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
    elif args["quiet"]:
        _LOGGER.setLevel(logging.WARNING)
        formatter = logging.Formatter("%(message)s")
    else:
        _LOGGER.setLevel(logging.INFO)
        formatter = logging.Formatter("%(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _LOGGER.addHandler(console_handler)


def get_arguments():
    """Get parsed arguments."""
    parser = argparse.ArgumentParser(description="Speedport: Reconnect Utility")
    parser.add_argument(
        "-H",
        "--host",
        help="IP address or hostname of Speedport web interface",
        default="speedport.ip",
    )
    parser.add_argument(
        "-s", "--https", help="Use HTTPS connection", action="store_true"
    )
    parser.add_argument("-p", "--password", help="Password of Speedport web interface")
    parser.add_argument(
        "-d", "--debug", help="Enable debug logging", action="store_true"
    )
    parser.add_argument("-q", "--quiet", help="Output only errors", action="store_true")
    return vars(parser.parse_args())


async def reconnect(args, speedport):
    """Reconnect to the internet and get a new IP address."""
    if not args.get("quiet"):
        await speedport.update_ip_data()  # Initial IP data fetch
        _LOGGER.info(f"Old IP: {speedport.public_ip_v4} / {speedport.public_ip_v6}")
    
    # Start reconnect process
    await speedport.reconnect()

    if not args.get("quiet"):
        # Retry loop to fetch the IP until a valid one is found
        for i in range(240):  # Try up to 240 checks (2 minutes)
            try:
                # Update IP data
                await speedport.update_ip_data()
                
                # If we have a valid IP, print the message and break
                if speedport.public_ip_v4 and speedport.public_ip_v6:
                    _LOGGER.info(f"New IP: {speedport.public_ip_v4} / {speedport.public_ip_v6}")
                    break  # Exit the loop once a valid IP is found
            except Exception as e:
                _LOGGER.error(f"Unexpected error: {e}")
            
            # If no IP found yet, retry every 0.5 seconds
            await asyncio.sleep(0.5)
            print(f"Connecting.{'.' * (i % 3)}  ", end="\r", flush=True)

async def main():
    args = get_arguments()
    set_logger(args)
    
    # Direkt festgelegtes Passwort
    password = device_password  
    timeout = aiohttp.ClientTimeout(total=5)
    # Initialisiere das Speedport-Objekt
    async with Speedport(args["host"], password, args.get("https")) as speedport:
        await reconnect(args, speedport)


def start():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == "__main__":
    start()
