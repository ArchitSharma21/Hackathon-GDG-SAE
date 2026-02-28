#!/bin/bash

# Google Cloud Setup Script for Airport Navigation Assistant
# This script will automatically set up your Google Cloud credentials

set -e  # Exit on error

echo "🚀 Google Cloud Credentials Setup"
echo "=================================="
echo ""

# Ensure gcloud is in PATH
export PATH=/opt/homebrew/bin:$PATH

# Check if authenticated
echo "Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "❌ Not authenticated. Please run: gcloud auth login"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo "✓ Authenticated as: $ACTIVE_ACCOUNT"
echo ""

# List available projects
echo "📋 Your Google Cloud Projects:"
echo "------------------------------"
gcloud projects list --format="table(projectId,name,projectNumber)"
echo ""

# Ask user to select or confirm project
read -p "Enter the PROJECT_ID you want to use: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No project ID provided"
    exit 1
fi

# Set the project
echo ""
echo "Setting project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo ""
echo "📡 Enabling required APIs..."
echo "  - Cloud Speech-to-Text API"
gcloud services enable speech.googleapis.com --project="$PROJECT_ID"

echo "  - Cloud Text-to-Speech API"
gcloud services enable texttospeech.googleapis.com --project="$PROJECT_ID"

echo "✓ APIs enabled"
echo ""

# Create service account
SERVICE_ACCOUNT_NAME="airport-nav-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "👤 Creating service account: $SERVICE_ACCOUNT_NAME"

# Check if service account already exists
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" &> /dev/null; then
    echo "⚠️  Service account already exists: $SERVICE_ACCOUNT_EMAIL"
    read -p "Do you want to use the existing service account? (y/n): " USE_EXISTING
    if [ "$USE_EXISTING" != "y" ]; then
        echo "Please delete the existing service account or use a different name"
        exit 1
    fi
else
    # Create service account
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="Airport Navigation Service Account" \
        --project="$PROJECT_ID"
    echo "✓ Service account created"
fi

echo ""

# Grant roles
echo "🔐 Granting permissions..."

echo "  - Cloud Speech Client"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/speech.client" \
    --quiet

echo "  - Cloud Text-to-Speech Client"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/texttospeech.client" \
    --quiet

echo "✓ Permissions granted"
echo ""

# Create and download key
KEY_FILE="/Users/ivanmardini/Hackathon-GDG-SAE/google-credentials.json"

echo "🔑 Creating JSON key..."
if [ -f "$KEY_FILE" ]; then
    echo "⚠️  Key file already exists at: $KEY_FILE"
    read -p "Do you want to overwrite it? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ]; then
        echo "Keeping existing key file"
    else
        rm "$KEY_FILE"
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SERVICE_ACCOUNT_EMAIL" \
            --project="$PROJECT_ID"
        echo "✓ New key created"
    fi
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SERVICE_ACCOUNT_EMAIL" \
        --project="$PROJECT_ID"
    echo "✓ Key created and saved to: $KEY_FILE"
fi

echo ""

# Update .env file
ENV_FILE="/Users/ivanmardini/Hackathon-GDG-SAE/.env"

echo "📝 Updating .env file..."

# Backup existing .env
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup"
    echo "  (Backup created: ${ENV_FILE}.backup)"
fi

# Update or add Google Cloud variables
if grep -q "GOOGLE_APPLICATION_CREDENTIALS" "$ENV_FILE" 2>/dev/null; then
    # Update existing
    sed -i '' "s|GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE|" "$ENV_FILE"
    sed -i '' "s|GOOGLE_CLOUD_PROJECT_ID=.*|GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID|" "$ENV_FILE"
else
    # Add new
    echo "" >> "$ENV_FILE"
    echo "# Google Cloud - Auto-configured" >> "$ENV_FILE"
    echo "GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE" >> "$ENV_FILE"
    echo "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID" >> "$ENV_FILE"
fi

echo "✓ .env file updated"
echo ""

# Test the setup
echo "🧪 Testing the setup..."

# Test with Python
if source /Users/ivanmardini/Hackathon-GDG-SAE/venv/bin/activate 2>/dev/null; then
    export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"

    if python3 -c "from google.cloud import speech_v1; print('✓ Speech API works!')" 2>/dev/null; then
        echo "✓ Speech-to-Text API connection successful"
    else
        echo "⚠️  Could not test Speech API (may need to restart Python environment)"
    fi

    if python3 -c "from google.cloud import texttospeech_v1; print('✓ TTS API works!')" 2>/dev/null; then
        echo "✓ Text-to-Speech API connection successful"
    else
        echo "⚠️  Could not test TTS API (may need to restart Python environment)"
    fi
else
    echo "⚠️  Virtual environment not found, skipping Python test"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SETUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Summary:"
echo "  Project: $PROJECT_ID"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "  Key File: $KEY_FILE"
echo "  .env File: Updated"
echo ""
echo "🔄 Next Steps:"
echo "  1. Restart your backend server:"
echo "     cd /Users/ivanmardini/Hackathon-GDG-SAE"
echo "     lsof -ti:8000 | xargs kill -9"
echo "     source venv/bin/activate"
echo "     cd backend && python main.py"
echo ""
echo "  2. Test the Text-to-Speech API:"
echo "     curl -X POST http://localhost:8000/api/speech/synthesize \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"text\":\"Hello from Google Cloud\",\"language\":\"en-US\"}' \\"
echo "       -o test.mp3 && open test.mp3"
echo ""
echo "🎉 Your app is now configured to use Google Cloud Speech APIs!"
echo ""
