#!/usr/bin/env python3
"""
ContractShield AI Backend Startup Script

This script starts the ContractShield AI backend server using uvicorn.
It reads configuration from environment variables and starts the FastAPI application.
"""

import os
import uvicorn

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )