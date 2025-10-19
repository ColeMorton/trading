# Complete Guide: SSH + Terminal Apps (MacBook ↔ Samsung Galaxy)

A comprehensive step-by-step guide for accessing Claude Code on your MacBook from your Samsung Galaxy using SSH and terminal apps.

## Table of Contents

- [Part 1: MacBook SSH Server Setup](#part-1-macbook-ssh-server-setup)
- [Part 2: Samsung Galaxy SSH Client Setup](#part-2-samsung-galaxy-ssh-client-setup)
- [Part 3: Claude Code Integration](#part-3-claude-code-integration)
- [Part 4: Tailscale Enhanced Setup (Optional)](#part-4-tailscale-enhanced-setup-optional)
- [Part 5: Optimization & Troubleshooting](#part-5-optimization--troubleshooting)

## Part 1: MacBook SSH Server Setup

### Step 1: Enable SSH Server (Remote Login)

1. **Open System Settings** (macOS 2025):

   - Click Apple menu → "System Settings"
   - Navigate to "Sharing" section

2. **Enable Remote Login**:

   - Toggle on "Remote Login"
   - SSH server starts immediately when enabled

3. **Configure Access (Recommended)**:

   - Click the (i) button next to Remote Login
   - For security: Choose "Only these users" instead of "All users"
   - Select your username for remote access
   - Check "Allow full disk access for remote users" for complete shell experience

4. **Note Your Connection Details**:
   - System Settings will display: `ssh username@YOUR_MAC_IP`
   - Write down your Mac's IP address (e.g., 192.168.1.100)

### Step 2: Set Up SSH Keys (Security Enhancement)

1. **Generate SSH key on MacBook** (if not exists):

   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location (~/.ssh/id_ed25519)
   # Set a passphrase for security
   ```

2. **Display your public key**:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

## Part 2: Samsung Galaxy SSH Client Setup

### Step 1: Install SSH Client App

**Recommended apps for Samsung Galaxy:**

**Option A: JuiceSSH (Best Overall - Free)**

- Download from Google Play Store
- Completely free with all essential features
- Best identity management
- Volume key font sizing
- No ads in free version

**Option B: Termius (Modern Interface)**

- Download from Google Play Store
- Free version available (some features require paid upgrade)
- Clean, modern UI
- Good for beginners

### Step 2: Configure SSH Connection in JuiceSSH

1. **Open JuiceSSH**

2. **Create New Connection**:

   - Tap "+" to add new connection
   - **Nickname**: "MacBook Claude"
   - **Type**: SSH
   - **Address**: Your Mac's IP address
   - **Port**: 22 (default)

3. **Set Up Identity**:

   - Tap "Identity" → "New"
   - **Nickname**: "MacBook User"
   - **Username**: Your Mac username
   - **Auth Type**:
     - For password: Select "Password"
     - For key-based: Select "Private Key"

4. **For Key-Based Authentication** (Recommended):
   - Generate key pair on Android or transfer from Mac
   - In JuiceSSH: Identity → Auth Type → "Private Key" → "Generate"
   - Copy the public key shown
   - Add this public key to Mac's `~/.ssh/authorized_keys`

## Part 3: Claude Code Integration

### Step 1: Install tmux on MacBook (Session Persistence)

```bash
# Install tmux via Homebrew
brew install tmux
```

### Step 2: Create Claude Code Session Script

```bash
# Create alias in your Mac's ~/.zshrc or ~/.bash_profile
echo 'alias claude-session="tmux new-session -d -s claude '\''claude'\'' && tmux attach-session -t claude"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Connect from Samsung Galaxy

1. **Open JuiceSSH**

2. **Connect to MacBook**:

   - Tap your "MacBook Claude" connection
   - Enter password/use key authentication

3. **Start Claude Code Session**:

   ```bash
   # Start new tmux session with Claude Code
   tmux new-session -d -s claude 'claude'
   tmux attach-session -t claude
   ```

4. **Detach/Reattach Sessions**:
   - Detach: `Ctrl+B`, then `D`
   - Reattach: `tmux attach-session -t claude`

## Part 4: Tailscale Enhanced Setup (Optional)

### Why Use Tailscale?

- Works across different networks (5G, WiFi, etc.)
- No router configuration needed
- Secure encrypted tunnel
- Stable connections regardless of location

### Step 1: Install Tailscale

**On MacBook:**

1. Download from [tailscale.com/download](https://tailscale.com/download)
2. Install and sign in with your account
3. Requires macOS 12.0+ (Monterey or later)

**On Samsung Galaxy:**

1. Download Tailscale from Google Play Store
2. Works with Android 8.0+
3. Sign in with same account

### Step 2: Enable Tailscale SSH (Advanced)

1. **In Tailscale Admin Console**:

   - Enable "Tailscale SSH" feature
   - Configure access controls for your devices

2. **Connect via Tailscale IP**:
   - Use Tailscale IP instead of local IP
   - Format: `ssh username@100.x.x.x` (Tailscale assigns 100.x.x.x range)

### Step 3: Update JuiceSSH Connection

- Edit your connection in JuiceSSH
- Change address to Tailscale IP (found in Tailscale app)
- Connection now works from anywhere

## Part 5: Optimization & Troubleshooting

### Performance Optimizations

1. **Samsung Galaxy DeX Mode**:

   - Connect keyboard/mouse for laptop-like experience
   - Better for extended coding sessions

2. **Font and Display**:

   - JuiceSSH: Use Volume Up key to increase font size
   - Configure color themes for better visibility

3. **Network Stability**:
   - Use autossh for automatic reconnection
   - Keep mobile device plugged in for long sessions

### Common Issues & Solutions

**Connection Refused:**

- Verify MacBook's firewall allows SSH (port 22)
- Check if Remote Login is still enabled
- Confirm IP address hasn't changed

**Authentication Failed:**

- Double-check username/password
- For key auth: verify public key in `~/.ssh/authorized_keys`
- Check key permissions: `chmod 600 ~/.ssh/authorized_keys`

**Session Disconnects:**

- Use tmux for session persistence
- Enable "Keep connections alive" in SSH client
- Consider Tailscale for better network stability

### Security Best Practices

1. **Use key-based authentication** instead of passwords
2. **Change default SSH port** if needed: Edit `/etc/ssh/sshd_config`
3. **Limit user access** to specific accounts only
4. **Use Tailscale** for additional network security layer
5. **Regular key rotation** for enhanced security

### Quick Command Reference

```bash
# Start Claude Code in tmux
tmux new-session -d -s claude 'claude' && tmux attach-session -t claude

# Detach from tmux session
Ctrl+B, then D

# Reattach to existing session
tmux attach-session -t claude

# List tmux sessions
tmux list-sessions

# Kill specific session
tmux kill-session -t claude

# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to clipboard (macOS)
pbcopy < ~/.ssh/id_ed25519.pub

# View public key
cat ~/.ssh/id_ed25519.pub

# Check SSH connection
ssh -T username@your_mac_ip

# Test with verbose output
ssh -v username@your_mac_ip
```

### SSH Configuration File (Optional)

Create `~/.ssh/config` on your MacBook for easier management:

```
Host macbook-local
    HostName 192.168.1.100
    User your_username
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host macbook-tailscale
    HostName 100.x.x.x
    User your_username
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

## Summary

This setup provides a robust, secure, and persistent way to access Claude Code on your MacBook from your Samsung Galaxy. The combination of SSH, tmux, and optionally Tailscale creates a professional development environment that works seamlessly across different networks and locations.

### Key Benefits:

- **Persistent Sessions**: tmux keeps your Claude Code sessions alive
- **Security**: Key-based authentication and encrypted connections
- **Flexibility**: Works on any network with Tailscale
- **Performance**: Native terminal experience on mobile
- **Reliability**: Automatic reconnection and session recovery

### Next Steps:

1. Start with basic SSH setup between devices
2. Add tmux for session persistence
3. Configure key-based authentication for security
4. Optionally add Tailscale for enhanced connectivity
5. Customize your mobile terminal app for optimal experience

Happy coding from anywhere! 🚀
