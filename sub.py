import requests
import socket
import json
import threading
from queue import Queue
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
THREADS = 50
TIMEOUT = 5


# ==========================================
# BANNER
# ==========================================
def print_banner():
    print("=" * 60)
    print("   SUBDOMAIN ENUMERATION TOOL - PYTHON PROJECT")
    print("=" * 60)
    print()


# ==========================================
# LOGGER
# ==========================================
def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


# ==========================================
# CLASS: ENUMERATOR
# ==========================================
class SubdomainEnumerator:

    def __init__(self, domain):
        self.domain = domain
        self.subdomains = set()
        self.resolved = set()
        self.queue = Queue()

    # ======================================
    # PASSIVE ENUMERATION (crt.sh)
    # ======================================
    def fetch_from_crtsh(self):
        log("Fetching subdomains from crt.sh...")
        url = f"https://crt.sh/?q=%25.{self.domain}&output=json"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            for entry in data:
                name = entry.get("name_value")
                if name:
                    for sub in name.split("\n"):
                        sub = sub.strip()
                        if self.domain in sub:
                            self.subdomains.add(sub)

            log(f"Passive enumeration found {len(self.subdomains)} subdomains")

        except Exception as e:
            log(f"Error in crt.sh fetch: {e}")

    # ======================================
    # LOAD WORDLIST
    # ======================================
    def load_wordlist(self, filename):
        try:
            with open(filename, "r") as file:
                words = [line.strip() for line in file if line.strip()]
            log(f"Loaded {len(words)} words from wordlist")
            return words
        except:
            log("Wordlist file not found!")
            return []

    # ======================================
    # DNS RESOLUTION
    # ======================================
    def resolve(self, subdomain):
        try:
            socket.gethostbyname(subdomain)
            return True
        except:
            return False

    # ======================================
    # WORKER THREAD
    # ======================================
    def worker(self):
        while not self.queue.empty():
            sub = self.queue.get()

            if self.resolve(sub):
                log(f"FOUND: {sub}")
                self.resolved.add(sub)

            self.queue.task_done()

    # ======================================
    # BRUTE FORCE
    # ======================================
    def brute_force(self, wordlist):
        log("Starting brute force...")

        for word in wordlist:
            sub = f"{word}.{self.domain}"
            self.queue.put(sub)

        threads = []

        for _ in range(THREADS):
            t = threading.Thread(target=self.worker)
            t.start()
            threads.append(t)

        self.queue.join()

        log(f"Brute force found {len(self.resolved)} valid subdomains")

    # ======================================
    # HTTP STATUS CHECK
    # ======================================
    def check_http(self, subdomain):
        urls = [
            f"http://{subdomain}",
            f"https://{subdomain}"
        ]

        for url in urls:
            try:
                response = requests.get(url, timeout=TIMEOUT)
                return response.status_code
            except:
                continue

        return None

    # ======================================
    # HTTP SCAN
    # ======================================
    def scan_http(self):
        log("Checking HTTP status...")

        results = {}

        for sub in self.resolved:
            status = self.check_http(sub)
            if status:
                log(f"{sub} -> HTTP {status}")
                results[sub] = status

        return results

    # ======================================
    # SAVE RESULTS
    # ======================================
    def save_results(self, http_results):
        filename_txt = f"{self.domain}_subdomains.txt"
        filename_json = f"{self.domain}_subdomains.json"

        # Save TXT
        with open(filename_txt, "w") as f:
            for sub in sorted(self.resolved):
                f.write(sub + "\n")

        # Save JSON
        with open(filename_json, "w") as f:
            json.dump(http_results, f, indent=4)

        log(f"Saved results to {filename_txt} and {filename_json}")

    # ======================================
    # DISPLAY RESULTS
    # ======================================
    def display_results(self):
        print("\n" + "=" * 40)
        print("FINAL SUBDOMAINS")
        print("=" * 40)

        for sub in sorted(self.resolved):
            print(sub)

        print("=" * 40)


# ==========================================
# MAIN FUNCTION
# ==========================================
def main():
    print_banner()

    domain = input("Enter target domain: ").strip()

    enumerator = SubdomainEnumerator(domain)

    # Passive
    enumerator.fetch_from_crtsh()

    # Wordlist
    wordlist = enumerator.load_wordlist("wordlist.txt")

    # Brute force
    if wordlist:
        enumerator.brute_force(wordlist)

    # HTTP check
    http_results = enumerator.scan_http()

    # Display
    enumerator.display_results()

    # Save
    enumerator.save_results(http_results)


# ==========================================
# EXTRA UTILITIES
# ==========================================
def generate_default_wordlist():
    words = [
        "www", "mail", "ftp", "dev", "test", "api", "admin",
        "staging", "beta", "blog", "shop", "portal",
        "secure", "vpn", "m", "mobile", "img", "cdn",
        "static", "dashboard", "internal", "db", "webmail"
    ]

    with open("wordlist.txt", "w") as f:
        for w in words:
            f.write(w + "\n")

    log("Default wordlist generated.")


def menu():
    print("\n1. Run Enumeration")
    print("2. Generate Default Wordlist")
    print("3. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        main()
    elif choice == "2":
        generate_default_wordlist()
    elif choice == "3":
        print("Exiting...")
        exit()
    else:
        print("Invalid choice")


# ==========================================
# PROGRAM ENTRY
# ==========================================
if __name__ == "__main__":
    while True:
        menu()