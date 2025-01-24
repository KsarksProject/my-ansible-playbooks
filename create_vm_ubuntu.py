import os
import requests
import time
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
from requests.exceptions import RequestException

# Загрузка переменных из .env файла
load_dotenv()

# Параметры AWX
awx_url = os.getenv("AWX_URL")
awx_user = os.getenv("AWX_USER")
awx_password = os.getenv("AWX_PASSWORD")
job_template_id = 18  # ID шаблона в AWX
extra_vars = {
    "vm_name": "SRVCVD01",  # Имя создаваемой виртуальной машины
    "hostname": "SRV-CVD-01"  # Хостнейм виртуальной машины
}

# Параметры Proxmox
proxmox_host = os.getenv("PROXMOX_HOST")
proxmox_user = os.getenv("PROXMOX_USER")
proxmox_password = os.getenv("PROXMOX_PASSWORD")


def verify_env_variables():
    """Проверка наличия всех необходимых переменных окружения."""
    required_vars = ["AWX_URL", "AWX_USER", "AWX_PASSWORD", "PROXMOX_HOST", "PROXMOX_USER", "PROXMOX_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        return False
    return True


def launch_awx_job():
    """Запуск задачи в AWX."""
    try:
        launch_url = f"{awx_url}/api/v2/job_templates/{job_template_id}/launch/"
        response = requests.post(
            launch_url,
            auth=(awx_user, awx_password),
            json={"extra_vars": extra_vars},
            verify=False
        )
        response.raise_for_status()
        print("Job started successfully.")
        job_data = response.json()
        return job_data['id']
    except RequestException as e:
        print(f"Error launching AWX job: {e}")
        if 'response' in locals():
            print(f"Response: {response.text}")
        return None


def get_awx_job_status(job_id):
    """Проверка статуса задачи в AWX."""
    job_url = f"{awx_url}/api/v2/jobs/{job_id}/"
    while True:
        try:
            response = requests.get(job_url, auth=(awx_user, awx_password), verify=False)
            response.raise_for_status()
            job_status = response.json()
            print(f"Job Status: {job_status['status']}")
            if job_status['status'] in ["successful", "failed"]:
                return job_status['status']
        except RequestException as e:
            print(f"Error fetching job status: {e}")
            return None
        time.sleep(5)  # Задержка между проверками


def get_proxmox_vm_ip(vm_name):
    """Получение IP-адреса виртуальной машины через Proxmox API."""
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


def main():
    if not verify_env_variables():
        return

    print("=" * 50)
    print("Launching AWX Job...")
    print("=" * 50)
    job_id = launch_awx_job()
    if job_id:
        print("=" * 50)
        print(f"Monitoring Job ID: {job_id}")
        print("=" * 50)
        status = get_awx_job_status(job_id)
        if status == "successful":
            print("=" * 50)
            print("AWX Job completed successfully. Fetching VM details...")
            print("=" * 50)
            ip_address = get_proxmox_vm_ip(extra_vars["vm_name"])
            if ip_address:
                print(f"VM IP Address: {ip_address}")
            else:
                print("Failed to fetch VM IP Address.")
        else:
            print("AWX Job failed.")
    else:
        print("Failed to start AWX job.")


if __name__ == "__main__":
    main()
