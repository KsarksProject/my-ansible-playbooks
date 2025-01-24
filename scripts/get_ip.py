import os
from dotenv import load_dotenv
from proxmoxer import ProxmoxAPI

# Загрузка переменных из файла .env
load_dotenv()

def get_proxmox_vm_ip(proxmox_host, proxmox_user, proxmox_password, vm_name):
    try:
        proxmox = ProxmoxAPI(proxmox_host, user=proxmox_user, password=proxmox_password, verify_ssl=False)
        vm = None
        node_name = None
        for node in proxmox.nodes.get():
            vms = proxmox.nodes(node['node']).qemu.get()
            for v in vms:
                if v['name'] == vm_name:
                    vm = v
                    node_name = node['node']
                    break

        if not vm:
            print(f"VM '{vm_name}' not found.")
            return None

        print(f"Found VM: {vm['name']}, VMID: {vm['vmid']}")

        network = proxmox.nodes(node_name).qemu(vm['vmid']).agent("network-get-interfaces").get()
        for iface in network['result']:
            if 'ip-addresses' in iface:
                print(f"Interface: {iface['name']}")
                for ip in iface['ip-addresses']:
                    print(f"  - {ip['ip-address']} ({ip['ip-address-type']})")
                    if ip['ip-address-type'] == 'ipv4' and ip['ip-address'] != '127.0.0.1':
                        print(f"Selected IP Address: {ip['ip-address']}")
                        return ip['ip-address']
        print("No valid IPv4 address found.")
        return None
    except Exception as e:
        print(f"Error while fetching IP address: {e}")
        return None



if __name__ == "__main__":
    # Загрузка параметров из переменных окружения
    PROXMOX_HOST = os.getenv("PROXMOX_HOST")
    PROXMOX_USER = os.getenv("PROXMOX_USER")
    PROXMOX_PASSWORD = os.getenv("PROXMOX_PASSWORD")
    VM_NAME = os.getenv("VM_NAME")

    # Проверка параметров
    if not all([PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASSWORD, VM_NAME]):
        print("Error: Missing required environment variables.")
        exit(1)

    ip_address = get_proxmox_vm_ip(PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASSWORD, VM_NAME)
    if ip_address:
        print(f"IP Address of VM '{VM_NAME}': {ip_address}")
    else:
        print(f"Failed to fetch IP address for VM '{VM_NAME}'.")
