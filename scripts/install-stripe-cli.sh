#!/bin/bash
set -e

echo "=== Installing Stripe CLI on Ubuntu ==="

# Add Stripe GPG key
curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg > /dev/null

# Add Stripe apt repository
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee /etc/apt/sources.list.d/stripe.list > /dev/null

# Install
sudo apt update && sudo apt install -y stripe

echo ""
echo "=== Stripe CLI installed: $(stripe --version) ==="
echo ""
echo "Next steps:"
echo "  1. stripe login"
echo "  2. stripe listen --forward-to localhost:5000/api/v1/plugins/stripe/webhook"
echo "  3. Copy the whsec_... secret into your Stripe plugin config (webhook_secret)"
