import asyncio
import json
import os
import socket
import struct
import time
from pyartnet import ArtNetNode
from pyartnet.errors import UniverseNotFoundError

ARTNET_PORT = 6454

class NodeCtrl:
    nodes = {}

    @classmethod
    def new(cls, node_id, ip_addr, port):
        cls.nodes[node_id] = ArtNetNode(ip_addr, port)
        if Session.isVerbose():
            print(f"ADDING NODE - [ID]: {node_id}    [IP]: {ip_addr}    [PORT]: {port}    [STATUS]: {'SUCCESS' if  node_id in cls.nodes and cls.nodes[node_id]._ip == ip_addr and cls.nodes[node_id]._port == port else 'FAIL'}")

    @classmethod
    def getNode(cls, node_id):
        return cls.nodes[node_id]

    @classmethod
    def clear(cls):
        cls.nodes.clear()

    @classmethod
    def print(cls):
        print("-"*20, "NODE DUMP", "-"*20)
        for node_id, node in cls.nodes.items():
            print(f"NODE [ID]: {node_id}    [IP]: {node._ip}    [PORT]: {node._port}")
        print("-"*51)

class UniverseCtrl:    
    universes = {}

    @classmethod
    def new(cls, parent_node_id, universe_id):
        cls.universes[universe_id] = NodeCtrl.getNode(parent_node_id).add_universe(universe_id)
        if Session.isVerbose():
            print(f"ADDING UNIVERSE - [UNID]: {universe_id}    [PARENT NODE]: {parent_node_id}    [STATUS]: {'SUCCESS' if universe_id in cls.universes and universe_id in NodeCtrl.getNode(parent_node_id)._universe_map else 'FAIL'}")
    
    @classmethod
    def clear(cls):
        cls.universes.clear()

    @classmethod
    def print(cls):
        for universe_id, universe in cls.universes.items():
            print(f"[UNID]: {universe_id}    [PARENT NODE]: {Helper.parent_node_id(universe_id, universe)}")

class Helper:
    def parent_node_id(universe_id, universe):
        universe_id_int = int(universe_id)
        for node_id, node in NodeCtrl.nodes.items():
            try:
                if node.get_universe(universe_id_int) is universe:
                    return node_id
            except UniverseNotFoundError:
                continue
            raise ValueError(f"No parent node found for universe {universe_id}")
    
    def discover_artnet_nodes(ip_address: str = "192.168.1.100", timeout: float = 2.0):
        """
        Discover ArtNet nodes by sending an ArtPoll packet and parsing ArtPollReply packets.

        Args:
            ip_address (str): Local IP address to determine broadcast address (default: '192.168.1.100').
            timeout (float): Time in seconds to wait for responses (default: 2.0).

        Returns:
            list: List of dictionaries with 'name', 'ip', and 'universe_count' for each node.
                Returns empty list on error or if no nodes are found.
        """
        ARTNET_PORT = 6454
        broadcast_ip = ip_address.rsplit('.', 1)[0] + '.255'
        print(f"[INFO] Using broadcast IP: {broadcast_ip}")

        # ArtPoll packet (OpCode = 0x2000)
        artpoll = b'Art-Net\x00'
        artpoll += struct.pack('<H', 0x2000)
        artpoll += struct.pack('>H', 14)
        artpoll += struct.pack('B', 0b00000010)
        artpoll += struct.pack('B', 0)
        print(f"[INFO] ArtPoll packet: {artpoll.hex()}")

        # Create socket
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            print(f"[INFO] Binding to all interfaces on port {ARTNET_PORT} (required for broadcast reply)")
            sock.bind(('', ARTNET_PORT))
            sock.settimeout(timeout)
            print(f"[INFO] Socket timeout set to {timeout} sec")

            # Send ArtPoll
            print(f"[INFO] Sending ArtPoll packet to {broadcast_ip}:{ARTNET_PORT}")
            sock.sendto(artpoll, (broadcast_ip, ARTNET_PORT))

            nodes = []
            start_time = time.time()
            print(f"[INFO] Waiting for ArtPollReply packets (timeout = {timeout} sec)...")

            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    if data.startswith(b'Art-Net'):
                        opcode = struct.unpack('<H', data[8:10])[0]
                        if opcode == 0x2100:
                            if addr[0] == ip_address:
                                print(f"[INFO] Ignoring loopback reply from self ({addr[0]})")
                                continue

                            # Parse required fields
                            name = data[26:44].decode('ascii', errors='ignore').rstrip('\x00')
                            port_count = data[173]
                            universes = list(data[190:190 + port_count])

                            print(f"[REPLY] Node at {addr[0]}")
                            print(f"         Name: {name}")
                            print(f"         Universe Count: {len(universes)}")

                            nodes.append({
                                'name': name,
                                'ip': addr[0],
                                'universe_count': len(universes)
                            })
                    else:
                        print(f"[WARNING] Non-ArtNet packet from {addr[0]}: header={data[0:8].hex()}")
                except socket.timeout:
                    print(f"[INFO] Timeout waiting for replies")
                    break
                except Exception as e:
                    print(f"[ERROR] Exception while receiving replies: {e}")
                    continue

        except Exception as e:
            print(f"[ERROR] Discovery error: {e}")
        finally:
            if sock:
                sock.close()
                print(f"[INFO] Socket closed.")

        print(f"[INFO] Discovery complete. {len(nodes)} node(s) found: {nodes}")
        return nodes

class Session:

    def isVerbose():
        return True

    @classmethod
    def saveToConfig(cls):
        """Saves the current state of nodes and universes to a JSON configuration file."""
        config = {
            "nodes": [
                {
                    "node_id": node_id,
                    "ip_addr": node._ip,
                    "port": node._port
                }
                for node_id, node in NodeCtrl.nodes.items()
            ],
            "universes": [
                {
                    "universe_id": universe_id,
                    "parent_node_id": Helper.parent_node_id(universe_id, universe)
                }
                for universe_id, universe in UniverseCtrl.universes.items()
            ]
        }
        
        return json.dumps(config, indent=4)

    @classmethod
    def loadFromConfig(cls, file_path):
        """Loads nodes and universes from a JSON configuration file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file {file_path} not found.")
        
        with open(file_path, 'r') as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {file_path}: {e}")

        # Clear existing nodes and universes to avoid duplicates
        NodeCtrl.nodes.clear()
        UniverseCtrl.universes.clear()

        # Load nodes first
        for node_data in config.get("nodes", []):
            node_id = node_data.get("node_id")
            ip_addr = node_data.get("ip_addr")
            port = node_data.get("port")
            if node_id and ip_addr and port is not None:
                NodeCtrl.new(node_id, ip_addr, port)
            else:
                raise ValueError(f"Invalid node data in {cls.CONFIG_FILE}: {node_data}")

        # Load universes, which depend on nodes
        for universe_data in config.get("universes", []):
            universe_id = universe_data.get("universe_id")
            parent_node_id = universe_data.get("parent_node_id")
            if universe_id and parent_node_id:
                if parent_node_id in NodeCtrl.nodes:
                    UniverseCtrl.new(parent_node_id, universe_id)
                else:
                    raise ValueError(f"Parent node {parent_node_id} not found for universe {universe_id}")
            else:
                raise ValueError(f"Invalid universe data in {cls.CONFIG_FILE}: {universe_data}")

async def main():
    pass


asyncio.run(main())