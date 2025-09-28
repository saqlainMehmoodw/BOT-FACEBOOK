<?php
header('Content-Type: application/json; charset=utf-8');

// Database connection
$db_path = 'facebook_bot.db'; // Adjust path as needed

try {
    $pdo = new PDO("sqlite:$db_path");
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    echo json_encode(['success' => false, 'message' => 'Database connection failed']);
    exit;
}

$action = $_GET['action'] ?? '';

switch($action) {
    case 'get_stats':
        getStats($pdo);
        break;
    case 'get_listings':
        getListings($pdo);
        break;
    case 'get_logs':
        getLogs($pdo);
        break;
    case 'start_bot':
        startBot($pdo);
        break;
    case 'stop_bot':
        stopBot($pdo);
        break;
    case 'process_listing':
        processListing($pdo);
        break;
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

function getStats($pdo) {
    try {
        // Total listings
        $stmt = $pdo->query("SELECT COUNT(*) as total FROM listings");
        $total = $stmt->fetch()['total'];

        // Public listings
        $stmt = $pdo->query("SELECT COUNT(*) as public FROM listings WHERE is_public = 1");
        $public = $stmt->fetch()['public'];

        // Pending listings
        $stmt = $pdo->query("SELECT COUNT(*) as pending FROM listings WHERE status = 'pending'");
        $pending = $stmt->fetch()['pending'];

        // Success rate
        $success_rate = $total > 0 ? round(($public / $total) * 100, 2) : 0;

        echo json_encode([
            'success' => true,
            'stats' => [
                'total_listings' => $total,
                'public_listings' => $public,
                'pending_listings' => $pending,
                'success_rate' => $success_rate
            ]
        ]);
    } catch(PDOException $e) {
        echo json_encode(['success' => false, 'message' => $e->getMessage()]);
    }
}

function getListings($pdo) {
    try {
        $stmt = $pdo->query("SELECT * FROM listings ORDER BY updated_at DESC LIMIT 50");
        $listings = $stmt->fetchAll(PDO::FETCH_ASSOC);

        echo json_encode([
            'success' => true,
            'listings' => $listings
        ]);
    } catch(PDOException $e) {
        echo json_encode(['success' => false, 'message' => $e->getMessage()]);
    }
}

function getLogs($pdo) {
    try {
        $stmt = $pdo->query("SELECT * FROM bot_logs ORDER BY timestamp DESC LIMIT 20");
        $logs = $stmt->fetchAll(PDO::FETCH_ASSOC);

        echo json_encode([
            'success' => true,
            'logs' => $logs
        ]);
    } catch(PDOException $e) {
        echo json_encode(['success' => false, 'message' => $e->getMessage()]);
    }
}

function startBot($pdo) {
    try {
        // Update bot status
        $stmt = $pdo->prepare("UPDATE settings SET is_running = 1 WHERE id = 1");
        $stmt->execute();

        // Add log entry
        $stmt = $pdo->prepare("INSERT INTO bot_logs (action, status, message) VALUES (?, ?, ?)");
        $stmt->execute(['start_bot', 'success', 'Bot started from web interface']);

        // In a real implementation, you would start the Python bot here
        // This could be done via exec() or a queue system

        echo json_encode(['success' => true, 'message' => 'Bot started successfully']);
    } catch(PDOException $e) {
        echo json_encode(['success' => false, 'message' => $e->getMessage()]);
    }
}

function stopBot($pdo) {
    try {
        // Update bot status
        $stmt = $pdo->prepare("UPDATE settings SET is_running = 0 WHERE id = 1");
        $stmt->execute();

        // Add log entry
        $stmt = $pdo->prepare("INSERT INTO bot_logs (action, status, message) VALUES (?, ?, ?)");
        $stmt->execute(['stop_bot', 'success', 'Bot stopped from web interface']);

        echo json_encode(['success' => true, 'message' => 'Bot stopped successfully']);
    } catch(PDOException $e) {
        echo json_encode(['success' => false, 'message' => $e->getMessage()]);
    }
}

function processListing($pdo) {
    $item_id = $_GET['item_id'] ?? '';

    if(empty($item_id)) {
        echo json_encode(['success' => false, 'message' => 'Item ID required']);
        return;
    }

    try {
        // Update listing status
        $stmt = $pdo->prepare("UPDATE listings SET status = 'processed', is_public = 1, is_visible = 1 WHERE item_id = ?");
        $stmt->execute([$item_id]);

        // Add log entry
        $stmt = $pdo->prepare("INSERT INTO bot_logs (action, status, message) VALUES (?, ?, ?)");
        $stmt->execute(['process_listing', 'success', "Processed listing: $item_id"]);

        echo json_encode(['success' => true, 'message' => 'Listing processed successfully']);
    } catch(PDOException $e) {
        echo json_encode(['success' => false, 'message' => $e->getMessage()]);
    }
}
?>
