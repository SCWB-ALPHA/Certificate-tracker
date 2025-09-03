# File: app.py
# A single-file Flask web application for tracking professional certifications.
# Features a modern, accessible, and responsive design with Tailwind CSS.

import json
from flask import Flask, render_template_string, request, redirect, url_for
from pathlib import Path
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)

# Define the file path for data storage
DATA_FILE = Path("data.json")

# --- DATA HANDLING FUNCTIONS ---
# These functions handle reading from and writing to the JSON file.

def load_data():
    """Loads certificate data from the JSON file."""
    if not DATA_FILE.exists():
        # Initialize with a default structure if file does not exist
        return {"owner_name": "My", "certificates": []}
    with DATA_FILE.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Ensure the owner_name key exists for backward compatibility
            if "owner_name" not in data:
                data["owner_name"] = "My"
            return data
        except json.JSONDecodeError:
            return {"owner_name": "My", "certificates": []}

def save_data(data):
    """Saves certificate data to the JSON file."""
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- FLASK ROUTES ---
# Each route handles a specific part of the application's functionality.

@app.route("/", methods=["GET"])
def home():
    """Renders the home page, showing all certificates."""
    data = load_data()
    today = datetime.now().date()
    
    # Process certificates to determine status and collect unique career options
    career_options = set()
    for cert in data["certificates"]:
        if cert.get('expiry_date'):
            try:
                expiry_date = datetime.strptime(cert['expiry_date'], '%Y-%m-%d').date()
                if expiry_date < today:
                    cert['status'] = 'Expired'
                elif (expiry_date - today).days <= 90:
                    cert['status'] = 'Expiring Soon'
                else:
                    cert['status'] = 'Valid'
            except ValueError:
                cert['status'] = 'Unknown'
        else:
            cert['status'] = 'Unknown'
            
        if cert.get('career_option'):
            career_options.add(cert['career_option'])

    # Hardcoded career suggestions based on categories
    career_suggestions = {
        'IT': [
            {'title': 'Network Administrator', 'description': 'Manages and maintains computer networks, ensuring uptime and security.'},
            {'title': 'Cybersecurity Analyst', 'description': 'Protects an organization\'s computer systems and networks from cyber threats.'},
            {'title': 'IT Project Manager', 'description': 'Plans and oversees IT projects, ensuring they are completed on time and within budget.'}
        ],
        'HR': [
            {'title': 'Recruitment Specialist', 'description': 'Finds, screens, and interviews job candidates to fill open positions.'},
            {'title': 'Compensation and Benefits Analyst', 'description': 'Designs and manages employee pay, benefits, and reward programs.'},
            {'title': 'HR Business Partner', 'description': 'Works with business leaders to align HR strategy with organizational goals.'}
        ],
        'Finance': [
            {'title': 'Financial Planner', 'description': 'Helps individuals and businesses create and manage their financial goals.'},
            {'title': 'Auditor', 'description': 'Examines financial records to ensure accuracy and compliance with regulations.'},
            {'title': 'Investment Analyst', 'description': 'Researches and recommends investment opportunities for clients.'}
        ],
        'Healthcare': [
            {'title': 'Medical Coder', 'description': 'Translates medical services into codes for billing and record-keeping purposes.'},
            {'title': 'Health Information Technician', 'description': 'Maintains the integrity of patient health records.'},
            {'title': 'Healthcare Administrator', 'description': 'Manages the daily operations of a hospital, clinic, or other healthcare facility.'}
        ],
        'Other': [
            {'title': 'Project Manager', 'description': 'Leads projects from conception to completion, ensuring all objectives are met.'},
            {'title': 'Business Analyst', 'description': 'Analyzes an organization\'s processes to identify areas for improvement.'}
        ]
    }
    
    # Get the current time for the "Created Date" timestamp
    created_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    return render_template_string(HTML_TEMPLATE,
        certificates=data["certificates"],
        owner_name=data["owner_name"],
        career_options=sorted(list(career_options)),
        career_suggestions=career_suggestions,
        created_date=created_date
    )

@app.route("/add_certificate", methods=["POST"])
def add_certificate():
    """Adds a new certificate."""
    name = request.form.get("name")
    org = request.form.get("organization")
    expiry_date = request.form.get("expiry_date")
    career_option = request.form.get("career_option")
    
    if name and org:
        data = load_data()
        new_cert_id = len(data["certificates"]) + 1
        new_cert = {
            "id": new_cert_id,
            "name": name,
            "organization": org,
            "expiry_date": expiry_date,
            "career_option": career_option
        }
        data["certificates"].append(new_cert)
        save_data(data)
    return redirect(url_for("home"))

@app.route("/edit_certificate/<int:cert_id>", methods=["POST"])
def edit_certificate(cert_id):
    """Edits an existing certificate."""
    new_name = request.form.get("name")
    new_org = request.form.get("organization")
    new_expiry_date = request.form.get("expiry_date")
    new_career_option = request.form.get("career_option")
    
    if new_name and new_org:
        data = load_data()
        cert = next((c for c in data["certificates"] if c["id"] == cert_id), None)
        if cert:
            cert["name"] = new_name
            cert["organization"] = new_org
            cert["expiry_date"] = new_expiry_date
            cert["career_option"] = new_career_option
            save_data(data)
    return redirect(url_for("home"))

@app.route("/delete_certificate/<int:cert_id>", methods=["POST"])
def delete_certificate(cert_id):
    """Deletes a certificate."""
    data = load_data()
    data["certificates"] = [c for c in data["certificates"] if c["id"] != cert_id]
    save_data(data)
    return redirect(url_for("home"))

@app.route("/update_owner_name", methods=["POST"])
def update_owner_name():
    """Updates the owner's name."""
    new_name = request.form.get("owner_name")
    if new_name:
        data = load_data()
        data["owner_name"] = new_name
        save_data(data)
    return redirect(url_for("home"))

@app.route("/print_ledger", methods=["GET"])
def print_ledger():
    """Renders a print-friendly view of the certificates."""
    data = load_data()
    filter_type = request.args.get('filter', 'all')
    
    filtered_certs = []
    if filter_type == 'all':
        filtered_certs = data['certificates']
    elif filter_type == 'expiring_soon':
        filtered_certs = [c for c in data['certificates'] if c.get('status') == 'Expiring Soon']
    elif filter_type == 'expired':
        filtered_certs = [c for c in data['certificates'] if c.get('status') == 'Expired']
    else:
        # Assume it's a career option filter
        filtered_certs = [c for c in data['certificates'] if c.get('career_option') == filter_type]
    
    created_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
    return render_template_string(PRINT_TEMPLATE, 
        certificates=filtered_certs,
        owner_name=data["owner_name"],
        filter_type=filter_type,
        created_date=created_date
    )

# --- HTML TEMPLATES ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ owner_name }}'s Certificate & Career Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        .tooltip .tooltip-text {
            visibility: hidden;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px 8px;
            position: absolute;
            z-index: 10;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .tooltip:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 100;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background-color: white;
            padding: 24px;
            border-radius: 8px;
            text-align: center;
        }
        body.dark .modal-content {
            background-color: #1f2937;
        }
    </style>
</head>
<body class="bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors duration-300">
    <div class="container mx-auto p-4 md:p-8">
        <header class="flex justify-between items-center mb-6">
            <h1 id="main-header" class="text-3xl md:text-4xl font-extrabold flex items-center">
                <svg class="h-8 w-8 md:h-10 md:w-10 mr-2 text-green-500" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2ZM9 16.5l-4-4 1.5-1.5L9 13.5l6.5-6.5L17 8l-8 8Z"/>
                </svg>
                <span id="owner-name-display">{{ owner_name }}'s</span> Certificate & Career Tracker
            </h1>
            <button id="theme-toggle" aria-label="Toggle dark mode" class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500">
                <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path class="moon-icon" d="M12 2.75a9.25 9.25 0 1 0 0 18.5 9.25 9.25 0 0 0 0-18.5ZM12 4.25a7.75 7.75 0 1 1 0 15.5 7.75 7.75 0 0 1 0-15.5Z"/>
                    <path class="sun-icon hidden" d="M12 18.25a6.25 6.25 0 1 0 0-12.5 6.25 6.25 0 0 0 0 12.5ZM12 2.75a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5a.75.75 0 0 1 .75-.75ZM12 19.25a.75.75 0 0 1-.75.75v1.5a.75.75 0 0 1 1.5 0v-1.5a.75.75 0 0 1-.75-.75ZM18.5 12a.75.75 0 0 1 .75-.75h1.5a.75.75 0 0 1 0 1.5h-1.5a.75.75 0 0 1-.75-.75ZM3.5 12a.75.75 0 0 1-.75-.75h-1.5a.75.75 0 0 1 0 1.5h1.5a.75.75 0 0 1 .75-.75ZM16.326 7.674a.75.75 0 0 1-.53-.22L17.53 6.31a.75.75 0 0 1 1.06 1.06L16.856 8.41a.75.75 0 0 1-.53-.22ZM6.41 17.53a.75.75 0 0 1-1.06-1.06L6.31 16.856a.75.75 0 0 1 1.06 1.06L6.41 17.53ZM17.53 16.856a.75.75 0 0 1-1.06 1.06l-1.205-1.205a.75.75 0 0 1 1.06-1.06l1.205 1.205ZM6.31 6.31a.75.75 0 0 1-1.06-1.06L7.674 3.984a.75.75 0 0 1 .53.22L7.674 6.31a.75.75 0 0 1-.53.22Z"/>
                </svg>
            </button>
        </header>
        
        <!-- Settings Section for Owner Name -->
        <main class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
            <h2 class="text-2xl md:text-3xl font-semibold mb-4">Settings</h2>
            <form id="owner-name-form" action="{{ url_for('update_owner_name') }}" method="post" class="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-4">
                <input type="text" name="owner_name" value="{{ owner_name }}" required class="flex-grow p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                <button type="submit" class="w-full md:w-auto p-3 rounded-lg bg-gray-500 text-white font-semibold hover:bg-gray-600 transition-colors duration-200">
                    Update Tracker Owner Name
                </button>
            </form>
        </main>
        
        <!-- Add Certificate Section -->
        <main class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
            <h2 class="text-2xl md:text-3xl font-semibold mb-4">Add a New Certificate</h2>
            <form id="add-form" action="{{ url_for('add_certificate') }}" method="post" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <input type="text" name="name" placeholder="Certificate Name" required class="p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                    <input type="text" name="organization" placeholder="Issuing Organization" required class="p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                    <input type="date" name="expiry_date" required class="p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                    <input type="text" name="career_option" placeholder="Career Category (e.g., IT, HR)" class="p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                </div>
                <button type="submit" class="w-full p-3 rounded-lg bg-green-500 text-white font-semibold hover:bg-green-600 transition-colors duration-200">
                    Add Certificate
                </button>
            </form>
        </main>
        
        <h2 class="text-2xl md:text-3xl font-semibold mb-4">My Certifications</h2>
        <!-- Informational note -->
        <div class="bg-blue-100 dark:bg-blue-900 border-l-4 border-blue-500 text-blue-800 dark:text-blue-200 p-4 rounded-lg mb-6 flex items-center space-x-3">
            <svg class="h-6 w-6 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
            </svg>
            <p class="text-sm md:text-base">
                Professional certifications often have an expiry date. Ensure you keep them current to maintain your professional standing and pursue your desired career path. A valid certification shows that you are up-to-date with the latest industry standards.
            </p>
        </div>

        <!-- Career Path Suggestions Section -->
        <main class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
            <h2 class="text-2xl md:text-3xl font-semibold mb-4">Career Path Suggestions</h2>
            {% if career_options %}
                <p class="text-sm md:text-base text-gray-700 dark:text-gray-300 mb-4">Based on your entered career categories, here are some roles you might be interested in. Use these as a starting point for your research!</p>
                {% for option in career_options %}
                    {% if career_suggestions[option] %}
                        <h3 class="text-xl md:text-2xl font-semibold mt-6 mb-2">{{ option }}</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {% for suggestion in career_suggestions[option] %}
                                <div class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                                    <h4 class="text-lg font-bold text-green-500">{{ suggestion.title }}</h4>
                                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">{{ suggestion.description }}</p>
                                </div>
                            {% endfor %}
                        </div>
                    {% endif %}
                {% endfor %}
            {% else %}
                <p class="text-sm md:text-base text-gray-500 dark:text-gray-400">
                    Start by adding some certificates with a **Career Category** to see personalized career path suggestions here.
                </p>
            {% endif %}
        </main>

        <!-- Filters and Print button -->
        <div class="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0 md:space-x-4 mb-4">
            <div class="flex space-x-2 items-center">
                <label for="filter-select" class="font-medium text-gray-700 dark:text-gray-300">Filter By:</label>
                <select id="filter-select" onchange="filterCertificates(this.value)" class="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                    <option value="all">All</option>
                    <option value="expiring_soon">Expiring Soon</option>
                    <option value="expired">Expired</option>
                    <optgroup label="By Career Category">
                        {% for option in career_options %}
                            <option value="{{ option }}">{{ option }}</option>
                        {% endfor %}
                    </optgroup>
                </select>
            </div>
            <button onclick="printLedger()" class="p-3 rounded-lg bg-blue-500 text-white font-semibold hover:bg-blue-600 transition-colors duration-200">
                <svg class="h-5 w-5 inline-block mr-2" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19 8H5a3 3 0 0 0-3 3v6h4v4h12v-4h4v-6a3 3 0 0 0-3-3ZM6 12a1 1 0 1 1 0-2 1 1 0 0 1 0 2Zm14 5h-4v-4h4v4ZM8 3h8v4H8V3Z"/>
                </svg>
                Print Ledger
            </button>
        </div>
        
        <!-- Certificate List -->
        <ul id="certificate-list" class="space-y-4">
            {% for cert in certificates %}
                <li class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 flex flex-col md:flex-row items-start md:items-center justify-between">
                    <div class="flex-grow">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg font-medium {% if cert.status == 'Expired' %}text-red-500{% elif cert.status == 'Expiring Soon' %}text-yellow-500{% else %}text-green-500{% endif %}">
                                <span class="text-gray-900 dark:text-gray-100 font-bold">{{ cert.name }}</span>
                            </span>
                            <span class="text-sm font-semibold p-1 rounded-full px-2 {% if cert.status == 'Expired' %}bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200{% elif cert.status == 'Expiring Soon' %}bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200{% else %}bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200{% endif %}">{{ cert.status }}</span>
                        </div>
                        <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Issued by {{ cert.organization }} | Expires: {{ cert.expiry_date }}
                            {% if cert.career_option %} | Category: {{ cert.career_option }}{% endif %}
                        </div>
                    </div>
                    <div class="flex space-x-2 mt-2 md:mt-0">
                        <button onclick="editCert({{ cert.id }}, '{{ cert.name }}', '{{ cert.organization }}', '{{ cert.expiry_date }}', '{{ cert.career_option }}')" class="p-2 text-blue-500 hover:text-blue-600 transition-colors duration-200 relative tooltip" aria-label="Edit certificate">
                            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M14.06 9.06L15.94 10.94 9 17.88 7.12 16L14.06 9.06ZM17.66 4.34a.996.996 0 0 0-1.41 0L15.06 5.53l2.83 2.83 1.18-1.18a.996.996 0 0 0 0-1.41L17.66 4.34ZM14.06 7.47L16.53 10l-6.38 6.38-2.47-2.47 6.38-6.38Z"/>
                            </svg>
                            <span class="tooltip-text">Edit</span>
                        </button>
                        <button onclick="showDeleteModal({{ cert.id }})" class="p-2 text-red-500 hover:text-red-600 transition-colors duration-200 relative tooltip" aria-label="Delete certificate">
                            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12Zm-2-4v2h16v-2h-2V7h-3V5h-6v2H6v2H4Zm12-2h-2V9h2v2Z"/>
                            </svg>
                            <span class="tooltip-text">Delete</span>
                        </button>
                    </div>
                </li>
            {% endfor %}
        </ul>
    </div>

    <!-- Delete Confirmation Modal -->
    <div id="delete-modal" class="modal">
        <div class="modal-content dark:text-gray-900">
            <p>Are you sure you want to delete this certificate?</p>
            <div class="mt-4 flex justify-center space-x-4">
                <button onclick="document.getElementById('delete-modal').style.display='none'" class="p-2 rounded-lg bg-gray-300 text-gray-800 font-semibold hover:bg-gray-400">Cancel</button>
                <form id="delete-form" method="post" class="inline">
                    <button type="submit" class="p-2 rounded-lg bg-red-500 text-white font-semibold hover:bg-red-600">Delete</button>
                </form>
            </div>
        </div>
    </div>
    
    <footer class="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        Created on {{ created_date }}
    </footer>

    <script>
        const allCertificates = {{ certificates | tojson }};
        let currentFilter = 'all';
    
        // Theme toggle logic
        const toggleButton = document.getElementById('theme-toggle');
        const sunIcon = toggleButton.querySelector('.sun-icon');
        const moonIcon = toggleButton.querySelector('.moon-icon');

        const isDarkMode = localStorage.getItem('theme') === 'dark';
        if (isDarkMode) {
            document.documentElement.classList.add('dark');
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        } else {
            document.documentElement.classList.remove('dark');
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }

        toggleButton.addEventListener('click', () => {
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.removeItem('theme');
                sunIcon.classList.add('hidden');
                moonIcon.classList.remove('hidden');
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
                sunIcon.classList.remove('hidden');
                moonIcon.classList.add('hidden');
            }
        });
        
        function showDeleteModal(certId) {
            const deleteForm = document.getElementById('delete-form');
            deleteForm.action = `/delete_certificate/${certId}`;
            document.getElementById('delete-modal').style.display = 'flex';
        }

        function filterCertificates(filterValue) {
            currentFilter = filterValue;
            const certList = document.getElementById('certificate-list');
            certList.innerHTML = '';
            
            const filteredCerts = allCertificates.filter(cert => {
                if (filterValue === 'all') return true;
                if (filterValue === 'expiring_soon' && cert.status === 'Expiring Soon') return true;
                if (filterValue === 'expired' && cert.status === 'Expired') return true;
                if (cert.career_option === filterValue) return true;
                return false;
            });

            filteredCerts.forEach(cert => {
                const certItem = document.createElement('li');
                certItem.className = 'bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 flex flex-col md:flex-row items-start md:items-center justify-between';
                certItem.innerHTML = `
                    <div class="flex-grow">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg font-medium ${cert.status === 'Expired' ? 'text-red-500' : (cert.status === 'Expiring Soon' ? 'text-yellow-500' : 'text-green-500')}">
                                <span class="text-gray-900 dark:text-gray-100 font-bold">${cert.name}</span>
                            </span>
                            <span class="text-sm font-semibold p-1 rounded-full px-2 ${cert.status === 'Expired' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' : (cert.status === 'Expiring Soon' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200')}">${cert.status}</span>
                        </div>
                        <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Issued by ${cert.organization} | Expires: ${cert.expiry_date}
                            ${cert.career_option ? `| Category: ${cert.career_option}` : ''}
                        </div>
                    </div>
                    <div class="flex space-x-2 mt-2 md:mt-0">
                        <button onclick="editCert(${cert.id}, '${cert.name}', '${cert.organization}', '${cert.expiry_date}', '${cert.career_option}')" class="p-2 text-blue-500 hover:text-blue-600 transition-colors duration-200 relative tooltip" aria-label="Edit certificate">
                            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M14.06 9.06L15.94 10.94 9 17.88 7.12 16L14.06 9.06ZM17.66 4.34a.996.996 0 0 0-1.41 0L15.06 5.53l2.83 2.83 1.18-1.18a.996.996 0 0 0 0-1.41L17.66 4.34ZM14.06 7.47L16.53 10l-6.38 6.38-2.47-2.47 6.38-6.38Z"/>
                            </svg>
                            <span class="tooltip-text">Edit</span>
                        </button>
                        <button onclick="showDeleteModal(${cert.id})" class="p-2 text-red-500 hover:text-red-600 transition-colors duration-200 relative tooltip" aria-label="Delete certificate">
                            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12Zm-2-4v2h16v-2h-2V7h-3V5h-6v2H6v2H4Zm12-2h-2V9h2v2Z"/>
                            </svg>
                            <span class="tooltip-text">Delete</span>
                        </button>
                    </div>
                `;
                certList.appendChild(certItem);
            });
        }
        
        // Edit certificate function
        function editCert(certId, currentName, currentOrg, currentExpiryDate, currentCareerOption) {
            const certElement = event.target.closest('li');
            const originalContent = certElement.querySelector('.flex-grow');
            const buttonContainer = certElement.querySelector('div.flex.space-x-2');
            
            const editForm = document.createElement('form');
            editForm.action = `/edit_certificate/${certId}`;
            editForm.method = 'post';
            editForm.classList.add('flex', 'flex-col', 'md:flex-row', 'space-y-2', 'md:space-y-0', 'md:space-x-2', 'w-full');

            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.name = 'name';
            nameInput.value = currentName;
            nameInput.required = true;
            nameInput.placeholder = 'Certificate Name';
            nameInput.className = 'p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500';

            const orgInput = document.createElement('input');
            orgInput.type = 'text';
            orgInput.name = 'organization';
            orgInput.value = currentOrg;
            orgInput.required = true;
            orgInput.placeholder = 'Issuing Organization';
            orgInput.className = 'p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500';

            const dateInput = document.createElement('input');
            dateInput.type = 'date';
            dateInput.name = 'expiry_date';
            dateInput.value = currentExpiryDate;
            dateInput.required = true;
            dateInput.className = 'p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500';
            
            const careerOptionInput = document.createElement('input');
            careerOptionInput.type = 'text';
            careerOptionInput.name = 'career_option';
            careerOptionInput.value = currentCareerOption;
            careerOptionInput.placeholder = 'Career Category';
            careerOptionInput.className = 'p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500';

            const saveButton = document.createElement('button');
            saveButton.type = 'submit';
            saveButton.textContent = 'Save';
            saveButton.className = 'p-2 rounded-lg bg-green-500 text-white hover:bg-green-600 transition-colors duration-200';

            editForm.appendChild(nameInput);
            editForm.appendChild(orgInput);
            editForm.appendChild(dateInput);
            editForm.appendChild(careerOptionInput);
            editForm.appendChild(saveButton);
            
            originalContent.replaceWith(editForm);
            buttonContainer.classList.add('hidden');
            nameInput.focus();
        }
        
        function printLedger() {
            const filterValue = document.getElementById('filter-select').value;
            window.open(`/print_ledger?filter=${filterValue}`, '_blank');
        }

    </script>
</body>
</html>
"""

PRINT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ owner_name }}'s Certificate Ledger</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
        }
        @media print {
            body {
                background-color: white !important;
                color: black !important;
            }
            .no-print {
                display: none;
            }
        }
    </style>
</head>
<body class="bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors duration-300 p-8">
    <div class="container mx-auto">
        <header class="flex flex-col items-center text-center mb-8">
            <h1 class="text-3xl md:text-4xl font-extrabold">{{ owner_name }}'s Certificate Ledger</h1>
            <p class="text-xl md:text-2xl mt-2 font-semibold text-gray-700 dark:text-gray-300">
                {% if filter_type == 'all' %}
                    All Certificates
                {% elif filter_type == 'expiring_soon' %}
                    Expiring Soon
                {% elif filter_type == 'expired' %}
                    Expired Certificates
                {% else %}
                    Category: {{ filter_type }}
                {% endif %}
            </p>
        </header>

        <ul class="space-y-6">
            {% for cert in certificates %}
                <li class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 
                    {% if cert.status == 'Expired' %}border-red-500{% elif cert.status == 'Expiring Soon' %}border-yellow-500{% else %}border-green-500{% endif %}">
                    <div class="flex flex-col space-y-2">
                        <div class="flex justify-between items-start">
                            <div class="flex-grow">
                                <h3 class="text-2xl font-bold">{{ cert.name }}</h3>
                                <p class="text-sm text-gray-600 dark:text-gray-400">Issued by: {{ cert.organization }}</p>
                            </div>
                            <span class="text-lg font-semibold px-3 py-1 rounded-full {% if cert.status == 'Expired' %}bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200{% elif cert.status == 'Expiring Soon' %}bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200{% else %}bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200{% endif %}">
                                {{ cert.status }}
                            </span>
                        </div>
                        <div class="grid grid-cols-2 gap-4 text-sm text-gray-700 dark:text-gray-300">
                            <div>
                                <span class="font-semibold">Expires:</span> {{ cert.expiry_date }}
                            </div>
                            {% if cert.career_option %}
                                <div>
                                    <span class="font-semibold">Category:</span> {{ cert.career_option }}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </li>
            {% endfor %}
        </ul>
        
        <div class="flex justify-center mt-8 no-print">
            <button onclick="window.print()" class="p-3 rounded-lg bg-blue-500 text-white font-semibold hover:bg-blue-600 transition-colors duration-200">
                <svg class="h-5 w-5 inline-block mr-2" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19 8H5a3 3 0 0 0-3 3v6h4v4h12v-4h4v-6a3 3 0 0 0-3-3ZM6 12a1 1 0 1 1 0-2 1 1 0 0 1 0 2Zm14 5h-4v-4h4v4ZM8 3h8v4H8V3Z"/>
                </svg>
                Print
            </button>
        </div>
    </div>
    <footer class="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        Created on {{ created_date }}
    </footer>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
