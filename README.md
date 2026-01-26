# SSH Plus Manager

A simple tool to manage SSH users on your server. Create users, set passwords, limit connections, and manage expiration dates.

## What it does

- Create and remove SSH users
- Change user passwords
- Set connection limits per user
- Set expiration dates for users
- Monitor active connections
- Manage network services

## Installation

Run **one** of these on your server (use the first if you have `curl`, the second if you have `wget`):

```bash
# If you have curl:
bash <(curl -Ls https://raw.githubusercontent.com/namnamir/SSH-Plus-Manager/main/install.sh)
```

```bash
# If you have wget (or curl is not installed):
wget -qO- https://raw.githubusercontent.com/namnamir/SSH-Plus-Manager/main/install.sh | bash
```

**Requirements:** You need either `curl` or `wget`. Run as root. On minimal systems you may need to install one first, for example:
- Debian/Ubuntu: `apt update && apt install -y curl`  or  `apt install -y wget`
- CentOS/RHEL: `yum install -y curl`  or  `yum install -y wget`

## Usage

After installation, type `menu` to open the main menu.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
