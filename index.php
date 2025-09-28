<?php
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook Marketplace Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }

        .stat-label {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .success { border-left: 5px solid #4CAF50; }
        .warning { border-left: 5px solid #FF9800; }
        .error { border-left: 5px solid #f44336; }
        .info { border-left: 5px solid #2196F3; }

        .controls {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }

        .btn-success {
            background: #4CAF50;
            color: white;
        }

        .btn-danger {
            background: #f44336;
            color: white;
        }

        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .listings-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }

        tr:hover {
            background: #f5f5f5;
        }

        .status-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .status-pending { background: #FFF3CD; color: #856404; }
        .status-success { background: #D1ECF1; color: #0C5460; }
        .status-error { background: #F8D7DA; color: #721C24; }

        .logs-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .log-entry {
            padding: 10px;
            border-left: 4px solid #667eea;
            margin-bottom: 10px;
            background: #f8f9fa;
        }

        .log-time {
            font-size: 0.8rem;
            color: #666;
        }

        .log-message {
            margin-top: 5px;
        }

        .refresh-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            float: right;
        }

        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 2rem;
            }

            th, td {
                padding: 8px 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Facebook Marketplace Bot</h1>
            <p>Automated Listing Management Dashboard</p>
        </div>

        <div class="dashboard">
            <div class="stat-card success">
                <div class="stat-number" id="totalListings">0</div>
                <div class="stat-label">Total Listings</div>
            </div>
            <div class="stat-card info">
                <div class="stat-number" id="publicListings">0</div>
                <div class="stat-label">Public Listings</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-number" id="pendingListings">0</div>
                <div class="stat-label">Pending Listings</div>
            </div>
            <div class="stat-card error">
                <div class="stat-number" id="successRate">0%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>

        <div class="controls">
            <h2 class="section-title">Bot Controls</h2>
            <button class="btn btn-primary" onclick="startBot()">Start Bot</button>
            <button class="btn btn-danger" onclick="stopBot()">Stop Bot</button>
            <button class="btn btn-success" onclick="refreshData()">Refresh Data</button>
            <span id="botStatus" style="margin-left: 20px; padding: 8px 15px; background: #ff9800; color: white; border-radius: 5px;">Stopped</span>
        </div>

        <div class="listings-section">
            <h2 class="section-title">Listings Management</h2>
            <button class="refresh-btn" onclick="refreshListings()">Refresh</button>
            <div class="table-container">
                <table id="listingsTable">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Status</th>
                            <th>Visibility</th>
                            <th>Last Updated</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="listingsBody">
                        <!-- Listings will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <div class="logs-section">
            <h2 class="section-title">Activity Logs</h2>
            <button class="refresh-btn" onclick="refreshLogs()">Refresh</button>
            <div id="logsContainer">
                <!-- Logs will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        // Load data when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadListings();
            loadLogs();
            startAutoRefresh();
        });

        // Auto refresh every 10 seconds
        function startAutoRefresh() {
            setInterval(() => {
                loadStats();
                loadListings();
                loadLogs();
            }, 10000);
        }

        // Load statistics
        function loadStats() {
            fetch('api.php?action=get_stats')
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('totalListings').textContent = data.stats.total_listings;
                        document.getElementById('publicListings').textContent = data.stats.public_listings;
                        document.getElementById('pendingListings').textContent = data.stats.pending_listings;
                        document.getElementById('successRate').textContent = data.stats.success_rate + '%';
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        // Load listings
        function loadListings() {
            fetch('api.php?action=get_listings')
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        const tbody = document.getElementById('listingsBody');
                        tbody.innerHTML = '';

                        data.listings.forEach(listing => {
                            const row = document.createElement('tr');

                            let statusClass = 'status-pending';
                            if(listing.status === 'processed') statusClass = 'status-success';
                            if(listing.status === 'failed') statusClass = 'status-error';

                            row.innerHTML = `
                                <td>${listing.title}</td>
                                <td><span class="status-badge ${statusClass}">${listing.status}</span></td>
                                <td>${listing.is_visible ? '✅ Visible' : '❌ Hidden'}</td>
                                <td>${listing.updated_at}</td>
                                <td>
                                    <button class="btn btn-primary" onclick="processListing('${listing.item_id}')">Process</button>
                                </td>
                            `;

                            tbody.appendChild(row);
                        });
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        // Load logs
        function loadLogs() {
            fetch('api.php?action=get_logs')
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        const container = document.getElementById('logsContainer');
                        container.innerHTML = '';

                        data.logs.forEach(log => {
                            const logEntry = document.createElement('div');
                            logEntry.className = 'log-entry';
                            logEntry.innerHTML = `
                                <div class="log-time">${log.timestamp}</div>
                                <div class="log-message"><strong>${log.action}</strong>: ${log.message}</div>
                            `;
                            container.appendChild(logEntry);
                        });
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        // Bot control functions
        function startBot() {
            fetch('api.php?action=start_bot')
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        alert('Bot started successfully');
                        document.getElementById('botStatus').textContent = 'Running';
                        document.getElementById('botStatus').style.background = '#28a745';
                    } else {
                        alert('Error starting bot: ' + data.message);
                    }
                });
        }

        function stopBot() {
            fetch('api.php?action=stop_bot')
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        alert('Bot stopped successfully');
                        document.getElementById('botStatus').textContent = 'Stopped';
                        document.getElementById('botStatus').style.background = '#ff9800';
                    }
                });
        }

        function processListing(itemId) {
            fetch('api.php?action=process_listing&item_id=' + itemId)
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        alert('Listing processed successfully');
                        loadListings();
                        loadStats();
                    } else {
                        alert('Error processing listing');
                    }
                });
        }

        function refreshData() {
            loadStats();
            loadListings();
            loadLogs();
        }

        function refreshListings() {
            loadListings();
        }

        function refreshLogs() {
            loadLogs();
        }
    </script>
</body>
</html>
