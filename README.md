📖 About
A GUI-based security testing tool for WordPress user enumeration via REST API and ID brute-forcing. Features real-time logging, metadata extraction, and CSV/Log export capabilities.
🎯 Use Cases:
    🔐 Bug Bounty Hunting
    🛡️ Penetration Testing
    📊 Security Audits
    🎓 Educational Purposes
    
✨ Features:
    ✅ REST API Testing - Tests /wp-json/wp/v2/users endpoints
    ✅ ID Brute Force - Automated user ID enumeration
    ✅ Metadata Extraction - WordPress version, plugins, and themes
    ✅ Persian GUI - Fully localized interface with dark theme
    ✅ Export Results - CSV and Log file support
    ✅ Real-time Logging - Live scan progress tracking
    ✅ Keyboard Shortcuts - Quick actions (Ctrl+S, Ctrl+L, Ctrl+R, Ctrl+E)

🚀 Installation
bash
Clone repository

git clone https://github.com/yourusername/wordpress-user-enumerator.git

cd wordpress-user-enumerator
Install dependencies

pip install requests
Run

python wordpressv21.py
💻 Usage

    Enter target URL
    Set maximum ID to scan (default: 20)
    Configure delay between requests (default: 1.0s)
    Click “شروع” (Start) button

Keyboard Shortcuts
    Ctrl+S - Export CSV
    Ctrl+L - Export Log
    Ctrl+R - Reset
    Ctrl+E - Start Scan

🔬 Technical Details
Enumeration Methods

    REST API: /wp-json/wp/v2/users
    Query String: ?rest_route=/wp/v2/users
    ID Brute Force: /wp-json/wp/v2/users/{id}

Extracted Data

    User ID, Username, Display Name
    Profile Links
    WordPress Version
    Installed Plugins & Themes

⚠️ Legal Disclaimer
For educational and authorized security testing only.
    ⚠️ Only test systems you have permission to test
    ⚠️ Follow Bug Bounty program rules
    ⚠️ Unauthorized use may be illegal

⚖️ The author is not responsible for misuse of this tool.
🛡️ Security Fix

For WordPress Developers:

php

// Disable REST API Users endpoint

add_filter(‘rest_endpoints’, function($endpoints) {

unset($endpoints[‘/wp/v2/users’]);

unset($endpoints[‘/wp/v2/users/(?P<id>[\d]+)’]);

return $endpoints;

});

📜 License
    GitHub: @miladdrag

⭐ Star this repo if you find it useful!

Made with ❤️ for Security Researchers
