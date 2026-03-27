// Database connection with better error handling
let pool;
let isConnected = false;

async function connectToDatabase() {
    try {
        const connectionString = process.env.DATABASE_URL;
        if (!connectionString) {
            console.error('❌ DATABASE_URL not found in environment variables');
            return false;
        }
        
        // Parse connection string to check if it's a local or remote DB
        const isLocalConnection = connectionString.includes('localhost') || connectionString.includes('127.0.0.1');
        
        pool = new Pool({
            connectionString: connectionString,
            ssl: isLocalConnection ? false : { rejectUnauthorized: false },
            connectionTimeoutMillis: process.env.PG_CONNECTION_TIMEOUT || 10000,
            idleTimeoutMillis: process.env.PG_IDLE_TIMEOUT || 30000,
            max: parseInt(process.env.PG_MAX_CLIENTS) || 10,
        });
        
        console.log('✅ Database configured');
        
        // Test connection
        const client = await pool.connect();
        const result = await client.query('SELECT NOW()');
        console.log('✅ Connected to PostgreSQL at:', result.rows[0].now);
        client.release();
        isConnected = true;
        return true;
        
    } catch (err) {
        console.error('❌ Database connection error:', err.message);
        console.log('⚠️ Running in offline mode - API endpoints will return mock data');
        isConnected = false;
        return false;
    }
}

// Call connection function
connectToDatabase();
